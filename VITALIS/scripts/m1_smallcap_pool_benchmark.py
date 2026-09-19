"""M1: the small-cap candidate pool's benchmark differential against QQQ.

Mirrors the method review module 11 section 8.2 used for the top-200 pool, so
the two numbers are directly comparable: at each month end rank the eligible
point-in-time universe by market cap, take the P009 size band, then measure the
equal-weight forward 21-session total return of that pool against the QQQ
total-return path over the same windows.

Delisting is the dominant bias risk here -- 10,302 of 13,513 eligible tickers
are delisted -- so a name that starts a window without an end price is handled
three ways and all three are reported: last known price inside the window (the
engine's existing forced_exit convention, primary), dropped (survivorship-
flattered upper bound), and marked -100% (lower bound).

Read-only: no strategy run, no parameter search, no remote request, no change
to prior artifacts. This measures a pool, not a strategy.
"""
import bisect
import csv
import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path

SHARADAR = Path('data/authorized/sharadar')
QQQ = Path('data/public-yahoo/QQQ-1999-01-01-2026-09-20.json')
OUT = Path('runs/m1-smallcap-pool-benchmark.json')

SIZE_BANDS = ((1000, 3000), (1, 200), (200, 1000), (3000, 6000))
PRIMARY_BAND = (1000, 3000)
ADV_FLOORS_USD = (0, 1_000_000, 5_000_000, 20_000_000)
# rank1-200 at the P003 $20M floor reproduces module 11 section 8.2's screen,
# so the two measurements can be compared on the same convention.
COMPARISON_BAND = (1, 200)
CATEGORIES = ('Domestic Common Stock', 'Domestic Common Stock Primary Class')
EXCHANGES = ('NYSE', 'NASDAQ', 'NYSEMKT')
HOLDING_SESSIONS = 21
FIRST_MONTH_END = '2004-06-30'
LAST_MONTH_END = '2025-11-30'


def sessions_and_qqq():
    from vitalis.data import normalize
    bars, issues = normalize(json.loads(QQQ.read_text()))
    if issues:
        raise ValueError(f'{len(issues)} invalid bars in the QQQ snapshot')
    return sorted(bars), {d: b['adjclose'] for d, b in bars.items()}


def month_end_sessions(sessions):
    by_month = {}
    for day in sessions:
        by_month[day[:7]] = day
    return [d for d in sorted(by_month.values()) if FIRST_MONTH_END <= d <= LAST_MONTH_END]


def eligible_tickers():
    with zipfile.ZipFile(SHARADAR / 'tickers-bulk-full.csv.zip') as archive:
        with archive.open('tickers.csv') as handle:
            return {row['ticker'] for row in csv.DictReader(io.TextIOWrapper(handle, 'utf-8'))
                    if row['table'] == 'SEP' and row['category'] in CATEGORIES
                    and row['exchange'] in EXCHANGES}


def market_caps_on(month_ends, eligible):
    """Point-in-time market cap for eligible tickers on each month-end session."""
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
    return caps


def prices_and_volume(tickers, dates):
    """closeadj and dollar volume for the given tickers on the given dates."""
    wanted_dates, out = set(dates), defaultdict(dict)
    with zipfile.ZipFile(SHARADAR / 'stocks-bulk-full.csv.zip') as archive:
        with archive.open('stocks.csv') as handle:
            stream = io.TextIOWrapper(handle, 'utf-8')
            header = stream.readline().rstrip('\n').split(',')
            i_t, i_d = header.index('ticker'), header.index('date')
            i_a, i_c, i_v = header.index('closeadj'), header.index('close'), header.index('volume')
            for line in stream:
                parts = line.rstrip('\n').split(',')
                if len(parts) <= i_v or parts[i_d] not in wanted_dates or parts[i_t] not in tickers:
                    continue
                try:
                    adj, close, volume = float(parts[i_a]), float(parts[i_c]), float(parts[i_v])
                except ValueError:
                    continue
                if adj > 0:
                    out[parts[i_t]][parts[i_d]] = (adj, close * volume)
    return out


def last_price_before(series, sessions, start, end):
    """Last known adjusted close strictly after `start` and at or before `end`."""
    days = sorted(d for d in series if start < d <= end)
    return series[days[-1]][0] if days else None


def chain(returns):
    wealth = 1.0
    for value in returns:
        wealth *= 1 + value
    return wealth ** (12 / len(returns)) - 1


def main():
    sessions, qqq = sessions_and_qqq()
    index = {d: i for i, d in enumerate(sessions)}
    month_ends = month_end_sessions(sessions)
    eligible = eligible_tickers()
    print(f'eligible tickers: {len(eligible):,}   month ends: {len(month_ends)} '
          f'({month_ends[0]} .. {month_ends[-1]})')

    print('scanning daily.csv for point-in-time market caps ...', flush=True)
    caps = market_caps_on(month_ends, eligible)

    windows, members = [], set()
    for month_end in month_ends:
        ranked = sorted(caps.get(month_end, {}).items(), key=lambda kv: -kv[1])
        position = bisect.bisect_right(sessions, month_end)
        if not ranked or position + HOLDING_SESSIONS >= len(sessions):
            continue
        start, end = sessions[position], sessions[position + HOLDING_SESSIONS]
        bands = {band: [t for t, _ in ranked[band[0] - 1:band[1]]] for band in SIZE_BANDS}
        windows.append({'month_end': month_end, 'start': start, 'end': end,
                        'ranked_count': len(ranked), 'bands': bands})
        for names in bands.values():
            members.update(names)
    print(f'windows: {len(windows)}   median ranked universe: '
          f'{sorted(w["ranked_count"] for w in windows)[len(windows) // 2]:,}   '
          f'distinct pool members ever: {len(members):,}')

    needed = {w['start'] for w in windows} | {w['end'] for w in windows}
    print('scanning stocks.csv for prices ...', flush=True)
    quotes = prices_and_volume(members, needed)

    # Every band must get the same last-price recovery, or a band left out of it
    # silently degrades to the -100% treatment and is reported as if it were the
    # proxy. An earlier version recovered only some bands and did exactly that.
    gaps = [(w, t) for w in windows for band in SIZE_BANDS for t in w['bands'][band]
            if t in quotes and w['start'] in quotes[t] and w['end'] not in quotes[t]]
    gaps = list({(w['month_end'], t): (w, t) for w, t in gaps}.values())
    print(f'names with a start price but no end price: {len(gaps):,}')
    if gaps:
        span = set()
        for w, _ in gaps:
            span.update(sessions[index[w['start']]:index[w['end']] + 1])
        recovery = prices_and_volume({t for _, t in gaps}, span)
        for t, series in recovery.items():
            quotes[t].update(series)

    results = {}
    for band in SIZE_BANDS:
        for floor in (ADV_FLOORS_USD if band == PRIMARY_BAND else (0,)):
            pool, bench, dropped, zeroed, proxied, sizes = [], [], [], [], [], []
            for w in windows:
                start, end = w['start'], w['end']
                proxy_rets, drop_rets, zero_rets = [], [], []
                for ticker in w['bands'][band]:
                    series = quotes.get(ticker, {})
                    if start not in series or series[start][1] < floor:
                        continue
                    first = series[start][0]
                    if end in series:
                        value = series[end][0] / first - 1
                        proxy_rets.append(value)
                        drop_rets.append(value)
                        zero_rets.append(value)
                        continue
                    last = last_price_before(series, sessions, start, end)
                    proxy_rets.append((last / first - 1) if last else -1.0)
                    zero_rets.append(-1.0)
                if len(proxy_rets) < 30:
                    continue
                sizes.append(len(proxy_rets))
                pool.append(sum(proxy_rets) / len(proxy_rets))
                dropped.append(sum(drop_rets) / len(drop_rets) if drop_rets else 0.0)
                zeroed.append(sum(zero_rets) / len(zero_rets))
                bench.append(qqq[end] / qqq[start] - 1)
            if not pool:
                continue
            key = f'rank{band[0]}-{band[1]}' + (f'_adv{floor // 1000}k' if floor else '')
            results[key] = {
                'windows': len(pool), 'median_pool_size': sorted(sizes)[len(sizes) // 2],
                'pool_cagr_last_price_proxy': chain(pool), 'pool_cagr_dropped': chain(dropped),
                'pool_cagr_delisted_to_zero': chain(zeroed), 'qqq_cagr': chain(bench),
                'gap_pp_primary': (chain(pool) - chain(bench)) * 100,
            }

    print(f'\n{"pool":<26}{"n":>5}{"size":>7}{"pool":>9}{"QQQ":>9}{"gap_pp":>9}'
          f'{"dropped":>10}{"to_zero":>10}')
    for key, row in results.items():
        print(f'{key:<26}{row["windows"]:5d}{row["median_pool_size"]:7d}'
              f'{row["pool_cagr_last_price_proxy"] * 100:8.2f}%{row["qqq_cagr"] * 100:8.2f}%'
              f'{row["gap_pp_primary"]:+9.2f}{row["pool_cagr_dropped"] * 100:9.2f}%'
              f'{row["pool_cagr_delisted_to_zero"] * 100:9.2f}%')

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({'method': 'equal-weight forward 21-session total return, '
                                         'monthly, point-in-time market-cap rank bands',
                               'gap_count_primary_band': len(gaps), 'results': results}, indent=2))
    print(f'\nwritten: {OUT}')


if __name__ == '__main__':
    main()
