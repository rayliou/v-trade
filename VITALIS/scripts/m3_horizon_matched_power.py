"""M3: recompute the P009 power table at holding horizons matched to the turnover cap.

The 25% monthly one-way turnover cap frozen on 2026-09-19 implies replacing
about five names of twenty per month, so the average holding period is near
four months. Every measurement in P009 sections 12 and 13 used a 21-session
horizon, which is the mismatch gate M3 exists to close.

Windows are NON-OVERLAPPING at each horizon, so a year holds 252/h of them.
Monthly decision-making over overlapping holds could recover some breadth,
but that is not measurable here and assuming it would be generous, so this
takes the conservative reading.

Read-only: no strategy run, no parameter search, no remote request, no change
to prior artifacts.
"""
import bisect
import csv
import io
import json
import math
import random
import zipfile
from collections import defaultdict
from pathlib import Path

SHARADAR = Path('data/authorized/sharadar')
QQQ = Path('data/public-yahoo/QQQ-1999-01-01-2026-09-20.json')
OUT = Path('runs/m3-horizon-matched-power.json')

BAND = (1000, 3000)
CATEGORIES = ('Domestic Common Stock', 'Domestic Common Stock Primary Class')
EXCHANGES = ('NYSE', 'NASDAQ', 'NYSEMKT')
HORIZON_SESSIONS = (21, 63, 84)
SESSIONS_PER_YEAR = 252
COUNT = 20
TRANSFER_COEFFICIENTS = (0.40, 0.30)
ANNUAL_COST = 0.0308              # M2: 25% monthly one-way turnover, 300k/20 names
TARGET_ABS_T = 2.0
TARGET_EXCESS = 0.02
ADV_FLOOR_USD = 5_000_000         # matches the screened ceiling M2 used
RANDOM_DRAWS = 200
RANDOM_SEED = 0
FIRST_MONTH_END, LAST_MONTH_END = '2004-06-30', '2025-11-28'


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
            i_t, i_d, i_c = (header.index('ticker'), header.index('date'),
                             header.index('marketcap'))
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
    return {m: [t for t, _ in sorted(caps.get(m, {}).items(), key=lambda kv: -kv[1])
                [BAND[0] - 1:BAND[1]]] for m in month_ends}


def collect(tickers, dates):
    wanted, out = set(dates), defaultdict(dict)
    with zipfile.ZipFile(SHARADAR / 'stocks-bulk-full.csv.zip') as archive:
        with archive.open('stocks.csv') as handle:
            stream = io.TextIOWrapper(handle, 'utf-8')
            header = stream.readline().rstrip('\n').split(',')
            i_t, i_d = header.index('ticker'), header.index('date')
            i_a, i_c, i_v = (header.index('closeadj'), header.index('close'),
                             header.index('volume'))
            for line in stream:
                parts = line.rstrip('\n').split(',')
                if len(parts) <= i_v or parts[i_d] not in wanted or parts[i_t] not in tickers:
                    continue
                try:
                    adj, close, volume = float(parts[i_a]), float(parts[i_c]), float(parts[i_v])
                except ValueError:
                    continue
                if adj > 0:
                    out[parts[i_t]][parts[i_d]] = (adj, close * volume)
    return out


def sd(values):
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))


def chain(values, per_year):
    wealth = 1.0
    for value in values:
        wealth *= 1 + value
    return wealth ** (per_year / len(values)) - 1


def main():
    sessions, qqq = sessions_and_qqq()
    by_month = {}
    for day in sessions:
        by_month[day[:7]] = day
    month_ends = [d for d in sorted(by_month.values()) if FIRST_MONTH_END <= d <= LAST_MONTH_END]
    eligible = eligible_tickers()
    print('scanning daily.csv ...', flush=True)
    membership = band_membership(month_ends, eligible)

    plans, members, needed = {}, set(), set()
    for horizon in HORIZON_SESSIONS:
        step = max(1, round(horizon / 21))
        windows = []
        for month_end in month_ends[::step]:
            position = bisect.bisect_right(sessions, month_end)
            if position + horizon >= len(sessions) or not membership.get(month_end):
                continue
            start, end = sessions[position], sessions[position + horizon]
            windows.append({'start': start, 'end': end, 'names': membership[month_end],
                            'span': sessions[position:position + horizon + 1]})
            members.update(membership[month_end])
            needed.update((start, end))
        plans[horizon] = windows
        print(f'  horizon {horizon:3d} sessions: {len(windows)} non-overlapping windows')

    print('scanning stocks.csv ...', flush=True)
    quotes = collect(members, needed)

    # Recover last known prices for every name-window missing an end price, in
    # every horizon -- a band or horizon left out of this silently becomes the
    # -100% treatment while still being reported as the proxy.
    span = set()
    for windows in plans.values():
        for w in windows:
            for ticker in w['names']:
                series = quotes.get(ticker, {})
                if w['start'] in series and w['end'] not in series:
                    span.update(w['span'])
    print(f'recovering last prices over {len(span):,} sessions ...', flush=True)
    for ticker, series in collect(members, span).items():
        quotes[ticker].update(series)

    rng = random.Random(RANDOM_SEED)
    results = {}
    print(f'\n{"h":>4}{"win":>5}{"yrs":>6}{"disp":>8}{"pool":>8}{"QQQ":>8}{"gap":>8}'
          f'{"poolTE":>8}{"ceil":>9}{"actRisk":>9}{"TEqqq":>8}')
    for horizon in HORIZON_SESSIONS:
        per_year = SESSIONS_PER_YEAR / horizon
        pool, bench, dispersions, spreads, diffs = [], [], [], [], []
        for w in plans[horizon]:
            values = []
            for ticker in w['names']:
                series = quotes.get(ticker, {})
                if w['start'] not in series or series[w['start']][1] < ADV_FLOOR_USD:
                    continue
                first = series[w['start']][0]
                if w['end'] in series:
                    values.append(series[w['end']][0] / first - 1)
                else:
                    later = [d for d in w['span'] if d in series and d > w['start']]
                    values.append((series[later[-1]][0] / first - 1) if later else -1.0)
            if len(values) < COUNT + 10:
                continue
            mean = sum(values) / len(values)
            pool.append(mean)
            bench.append(qqq[w['end']] / qqq[w['start']] - 1)
            dispersions.append(sd(values))
            spreads.append(sum(sorted(values, reverse=True)[:COUNT]) / COUNT - mean)
            diffs.extend(sum(rng.sample(values, COUNT)) / COUNT - mean for _ in range(RANDOM_DRAWS))

        years = len(pool) / per_year
        pool_cagr, bench_cagr = chain(pool, per_year), chain(bench, per_year)
        gap = pool_cagr - bench_cagr
        pool_te = sd([p - b for p, b in zip(pool, bench)]) * math.sqrt(per_year)
        ceiling = sum(spreads) / len(spreads) * per_year
        active = sd(diffs) * math.sqrt(per_year)
        tracking = math.sqrt(active ** 2 + pool_te ** 2)
        dispersions.sort()
        results[horizon] = {
            'windows': len(pool), 'years': years,
            'median_dispersion': dispersions[len(dispersions) // 2],
            'pool_cagr': pool_cagr, 'qqq_cagr': bench_cagr, 'gap': gap,
            'pool_te': pool_te, 'ceiling': ceiling, 'active_risk': active,
            'te_vs_qqq': tracking, 'required_ic': {}}
        print(f'{horizon:4d}{len(pool):5d}{years:6.1f}{dispersions[len(dispersions)//2]*100:7.2f}%'
              f'{pool_cagr*100:7.2f}%{bench_cagr*100:7.2f}%{gap*100:+7.2f}'
              f'{pool_te*100:7.2f}%{ceiling*100:8.0f}%{active*100:8.2f}%{tracking*100:7.2f}%')

    print(f'\nRequired IC with M2 costs ({ANNUAL_COST*100:.2f}pp/yr at the 25% cap):')
    print(f'{"h":>4}{"tc":>6}{"parity":>9}{"+2pp":>8}{"prove":>9}')
    for horizon in HORIZON_SESSIONS:
        r = results[horizon]
        detection = TARGET_ABS_T / math.sqrt(r['years']) * r['te_vs_qqq']
        for transfer in TRANSFER_COEFFICIENTS:
            capacity = transfer * r['ceiling']
            row = {'parity': (-r['gap'] + ANNUAL_COST) / capacity,
                   'plus_2pp': (-r['gap'] + ANNUAL_COST + TARGET_EXCESS) / capacity,
                   'prove': (detection - r['gap'] + ANNUAL_COST) / capacity}
            r['required_ic'][f'tc{transfer:.2f}'] = row
            print(f'{horizon:4d}{transfer:6.2f}{row["parity"]:9.3f}'
                  f'{row["plus_2pp"]:8.3f}{row["prove"]:9.3f}')

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'band': list(BAND), 'adv_floor_usd': ADV_FLOOR_USD,
                               'annual_cost': ANNUAL_COST, 'horizons': results}, indent=2))
    print(f'\nwritten: {OUT}')


if __name__ == '__main__':
    main()
