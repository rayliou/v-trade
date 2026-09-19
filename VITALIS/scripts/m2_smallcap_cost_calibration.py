"""M2: real cost calibration for the P009 small-cap shape.

Three questions in one scan of the bulk files:
  1. Effective spread for the rank 1000-3000 pool, from the Corwin-Schultz
     high-low estimator (daily OHLC only; no intraday data is available here).
  2. Market impact at this account's real position sizes, from participation
     against each name's own trailing dollar volume.
  3. How much of the perfect-foresight ceiling in P009 section 12 survives a
     tradability screen -- that ceiling rests on a last-price proxy that
     includes delisted names nobody could have traded at those prices, and
     P009 flagged it as the largest unquantified bias in the power table.

Read-only: no strategy run, no parameter search, no remote request, no change
to prior artifacts. Cost inputs are estimators and assumptions, not fills.
"""
import bisect
import csv
import io
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path

SHARADAR = Path('data/authorized/sharadar')
QQQ = Path('data/public-yahoo/QQQ-1999-01-01-2026-09-20.json')
OUT = Path('runs/m2-smallcap-cost-calibration.json')

BAND = (1000, 3000)
CATEGORIES = ('Domestic Common Stock', 'Domestic Common Stock Primary Class')
EXCHANGES = ('NYSE', 'NASDAQ', 'NYSEMKT')
HOLDING_SESSIONS = 21
LOOKBACK_SESSIONS = 5
FIRST_MONTH_END, LAST_MONTH_END = '2004-06-30', '2025-11-28'

ACCOUNTS_USD = (200_000, 300_000, 400_000)
COUNTS = (20, 40)
MONTHLY_ONE_WAY_TURNOVER = (0.25, 0.50, 1.00)
IMPACT_COEFFICIENT = 1.0          # impact = k * daily_vol * sqrt(participation)
CEILING_TOP_N = 20
ADV_FLOORS_USD = (0, 1_000_000, 5_000_000)
WINSOR_LIMITS = (None, 1.0, 3.0)  # cap each name's window return at +/- this


def corwin_schultz(high_a, low_a, high_b, low_b):
    """Two-day high-low effective spread, as a fraction of price."""
    if min(high_a, low_a, high_b, low_b) <= 0 or high_a < low_a or high_b < low_b:
        return None
    beta = math.log(high_a / low_a) ** 2 + math.log(high_b / low_b) ** 2
    gamma = math.log(max(high_a, high_b) / min(low_a, low_b)) ** 2
    denominator = 3 - 2 * math.sqrt(2)
    alpha = (math.sqrt(2 * beta) - math.sqrt(beta)) / denominator \
        - math.sqrt(gamma / denominator)
    spread = 2 * (math.exp(alpha) - 1) / (1 + math.exp(alpha))
    return max(0.0, spread)          # the estimator's standard truncation


def sessions_and_qqq():
    from vitalis.data import normalize
    bars, issues = normalize(json.loads(QQQ.read_text()))
    if issues:
        raise ValueError(f'{len(issues)} invalid bars in the QQQ snapshot')
    return sorted(bars), {d: b['adjclose'] for d, b in bars.items()}


def eligible_tickers():
    with zipfile.ZipFile(SHARADAR / 'tickers-bulk-full.csv.zip') as archive:
        with archive.open('tickers.csv') as handle:
            return {r['ticker'] for r in csv.DictReader(io.TextIOWrapper(handle, 'utf-8'))
                    if r['table'] == 'SEP' and r['category'] in CATEGORIES
                    and r['exchange'] in EXCHANGES}


def band_membership(month_ends, eligible):
    wanted, caps = set(month_ends), defaultdict(dict)
    with zipfile.ZipFile(SHARADAR / 'daily-bulk-full.csv.zip') as archive:
        with archive.open('daily.csv') as handle:
            stream = io.TextIOWrapper(handle, 'utf-8')
            header = stream.readline().rstrip('\n').split(',')
            i_t, i_d, i_c = header.index('ticker'), header.index('date'), header.index('marketcap')
            for line in stream:
                parts = line.rstrip('\n').split(',')
                if len(parts) <= i_c or parts[i_d] not in wanted or parts[i_t] not in eligible:
                    continue
                try:
                    value = float(parts[i_c])
                except ValueError:
                    continue
                if value > 0:
                    caps[parts[i_d]][parts[i_t]] = value
    out = {}
    for month_end in month_ends:
        ranked = sorted(caps.get(month_end, {}).items(), key=lambda kv: -kv[1])
        out[month_end] = [t for t, _ in ranked[BAND[0] - 1:BAND[1]]]
    return out


def collect_bars(tickers, dates):
    wanted, out = set(dates), defaultdict(dict)
    with zipfile.ZipFile(SHARADAR / 'stocks-bulk-full.csv.zip') as archive:
        with archive.open('stocks.csv') as handle:
            stream = io.TextIOWrapper(handle, 'utf-8')
            header = stream.readline().rstrip('\n').split(',')
            cols = {k: header.index(k) for k in
                    ('ticker', 'date', 'high', 'low', 'close', 'volume', 'closeadj')}
            for line in stream:
                parts = line.rstrip('\n').split(',')
                if len(parts) <= max(cols.values()):
                    continue
                if parts[cols['date']] not in wanted or parts[cols['ticker']] not in tickers:
                    continue
                try:
                    row = {k: float(parts[i]) for k, i in cols.items()
                           if k not in ('ticker', 'date')}
                except ValueError:
                    continue
                out[parts[cols['ticker']]][parts[cols['date']]] = row
    return out


def percentiles(values, points=(0.1, 0.25, 0.5, 0.75, 0.9)):
    ordered = sorted(values)
    return {f'p{int(p * 100)}': ordered[int(p * (len(ordered) - 1))] for p in points}


def main():
    sessions, qqq = sessions_and_qqq()
    index = {d: i for i, d in enumerate(sessions)}
    by_month = {}
    for day in sessions:
        by_month[day[:7]] = day
    month_ends = [d for d in sorted(by_month.values()) if FIRST_MONTH_END <= d <= LAST_MONTH_END]

    eligible = eligible_tickers()
    print('scanning daily.csv for point-in-time market caps ...', flush=True)
    membership = band_membership(month_ends, eligible)

    windows, members, needed = [], set(), set()
    for month_end in month_ends:
        names = membership.get(month_end, [])
        position = bisect.bisect_right(sessions, month_end)
        if not names or position + HOLDING_SESSIONS >= len(sessions):
            continue
        start = sessions[position]
        end = sessions[position + HOLDING_SESSIONS]
        lookback = sessions[max(0, position - LOOKBACK_SESSIONS):position + 1]
        windows.append({'start': start, 'end': end, 'lookback': lookback, 'names': names})
        members.update(names)
        needed.update(lookback)
        needed.add(end)
    print(f'windows {len(windows)}   pool members ever {len(members):,}   '
          f'price dates needed {len(needed):,}', flush=True)

    print('scanning stocks.csv for OHLCV ...', flush=True)
    bars = collect_bars(members, needed)

    spreads, advs, records = [], [], []
    for position, window in enumerate(windows):
        start, end, lookback = window['start'], window['end'], window['lookback']
        for ticker in window['names']:
            series = bars.get(ticker)
            if not series or start not in series:
                continue
            days = [d for d in lookback if d in series]
            if len(days) < 2:
                continue
            pairs = [corwin_schultz(series[a]['high'], series[a]['low'],
                                    series[b]['high'], series[b]['low'])
                     for a, b in zip(days, days[1:])]
            pairs = [s for s in pairs if s is not None]
            if not pairs:
                continue
            spread = sum(pairs) / len(pairs)
            adv = sum(series[d]['close'] * series[d]['volume'] for d in days) / len(days)
            if adv <= 0:
                continue
            daily_vol = math.sqrt(sum(math.log(series[d]['high'] / series[d]['low']) ** 2
                                      for d in days if series[d]['low'] > 0) / len(days)) / 2
            first = series[start]['closeadj']
            has_end = end in series
            value = (series[end]['closeadj'] / first - 1) if has_end and first > 0 else None
            spreads.append(spread)
            advs.append(adv)
            records.append({'window': position, 'spread': spread, 'adv': adv,
                            'vol': daily_vol, 'ret': value, 'has_end': has_end})

    print(f'\nname-windows measured: {len(records):,}')
    print(f'Corwin-Schultz effective spread, fraction of price:')
    for k, v in percentiles(spreads).items():
        print(f'  {k}: {v * 1e4:8.1f} bps')
    print(f'trailing {LOOKBACK_SESSIONS}-session average dollar volume:')
    for k, v in percentiles(advs).items():
        print(f'  {k}: ${v:,.0f}')

    print(f'\nRound-trip cost per rebalance and annualised, by account and book size')
    print(f'(impact = {IMPACT_COEFFICIENT} x daily vol x sqrt(position/ADV))')
    print(f'{"acct":>9}{"names":>7}{"pos$":>10}{"median part.":>14}'
          f'{"half-spread":>13}{"impact":>9}{"1-way bps":>11}'
          + ''.join(f'{"ann@" + f"{t:.0%}":>11}' for t in MONTHLY_ONE_WAY_TURNOVER))
    cost_table = {}
    for account in ACCOUNTS_USD:
        for count in COUNTS:
            position = account / count
            per_name = []
            for r in records:
                participation = position / r['adv']
                impact = IMPACT_COEFFICIENT * r['vol'] * math.sqrt(participation)
                per_name.append((r['spread'] / 2 + impact, participation,
                                 r['spread'] / 2, impact))
            per_name.sort(key=lambda x: x[0])
            mid = per_name[len(per_name) // 2]
            one_way_bps = mid[0] * 1e4
            annual = {f'{t:.0%}': 2 * 12 * t * mid[0] for t in MONTHLY_ONE_WAY_TURNOVER}
            cost_table[f'{account}_{count}'] = {
                'position_usd': position, 'median_participation': mid[1],
                'median_half_spread_bps': mid[2] * 1e4, 'median_impact_bps': mid[3] * 1e4,
                'median_one_way_bps': one_way_bps, 'annual_cost_pp': {k: v * 100 for k, v in annual.items()}}
            print(f'{account:9,}{count:7d}{position:10,.0f}{mid[1] * 100:13.2f}%'
                  f'{mid[2] * 1e4:12.0f}b{mid[3] * 1e4:8.0f}b{one_way_bps:11.0f}'
                  + ''.join(f'{annual[f"{t:.0%}"] * 100:10.2f}p' for t in MONTHLY_ONE_WAY_TURNOVER))

    print(f'\nTradability haircut on the perfect-foresight top-{CEILING_TOP_N} ceiling')
    print(f'{"screen":<34}{"name-windows":>14}{"ceiling %/yr":>15}')
    grouped = defaultdict(list)
    for record in records:
        grouped[record['window']].append(record)

    ceilings = {}
    for floor in ADV_FLOORS_USD:
        for require_end in (False, True):
            for winsor in WINSOR_LIMITS:
                label = (f'adv>=${floor // 1000}k' if floor else 'all') \
                    + (', end price required' if require_end else '') \
                    + (f', winsor +/-{winsor:.0f}' if winsor else '')
                spreads_out, kept = [], 0
                for chunk in grouped.values():
                    values = []
                    for r in chunk:
                        if r['adv'] < floor:
                            continue
                        if require_end and not r['has_end']:
                            continue
                        value = r['ret'] if r['ret'] is not None else -1.0
                        if winsor:
                            value = max(-winsor, min(winsor, value))
                        values.append(value)
                    if len(values) < CEILING_TOP_N:
                        continue
                    kept += len(values)
                    mean = sum(values) / len(values)
                    top = sorted(values, reverse=True)[:CEILING_TOP_N]
                    spreads_out.append(sum(top) / CEILING_TOP_N - mean)
                if not spreads_out:
                    continue
                ceiling = sum(spreads_out) / len(spreads_out) * 12
                ceilings[label] = {'name_windows': kept, 'ceiling_pct_per_year': ceiling * 100}
                print(f'{label:<34}{kept:>14,}{ceiling * 100:>15.1f}')

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        'name_windows': len(records),
        'spread_bps': {k: v * 1e4 for k, v in percentiles(spreads).items()},
        'adv_usd': percentiles(advs), 'costs': cost_table, 'ceilings': ceilings}, indent=2))
    print(f'\nwritten: {OUT}')


if __name__ == '__main__':
    main()
