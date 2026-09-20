"""Ex-ante feasibility screen for a cross-sectional signal overlay (docs/review/11 section 8).

Scope: the P003-P005 portfolio shape only -- top-200-by-market-cap point-in-time
pool, long only, 10 or 20 equal-weight names, monthly rebalance. It is NOT a
P007 screen: P007 inherits P006's whole-market relative-volume top-100 pool and
holds 3/5 names, so neither the pool, the holding count nor the tracking error
here transfers to it.

This is NOT a backtest and NOT investment evidence. It uses no options data.
Signal strength (IC) is a grid of ASSUMPTIONS, not an estimate from this data.

Two benchmarks are kept separate, because mixing them was an error in an earlier
draft: selection skill is measured against the equal-weight candidate pool, while
the project's acceptance target is measured against the QQQ total-return proxy.
The gap between those two benchmarks is itself measured here.

No simulation, parameter search, remote request, or change to prior artifacts.
"""
import csv
import gzip
import json
import math
import random
from pathlib import Path

RUN = Path('runs/20260913T230559016875Z-pit-0f145816')
BARS_CACHE = Path('data/authorized/sharadar/derived-cache/'
                  'eda371b8c8ce8e2bd7388f2d040099ec9f5de4b97da93f517e642b143f9a3c57.json.gz')

HOLDING_SESSIONS = 21
REBALANCES_PER_YEAR = 12
COUNTS = (10, 20)
IC_GRID = (0.01, 0.02, 0.03, 0.05, 0.10, 0.15)
TRANSFER_COEFFICIENTS = (1.00, 0.60, 0.40)
TARGET_ABS_T = 2.0
TARGET_NET_EXCESS_PP = 2.0
RANDOM_DRAWS_PER_MONTH = 200
RANDOM_SEED = 0


def load_inputs():
    with gzip.open(BARS_CACHE, 'rt') as handle:
        bars = json.load(handle)['bars']
    universe = [(r['month_end'], r['selected'])
                for r in json.loads((RUN / 'universe_diagnostics.json').read_text())]
    with (RUN / 'QQQ-total-return-proxy-nav.csv').open() as handle:
        benchmark = {r['date']: float(r['nav_usd']) for r in csv.DictReader(handle)}
    return bars, universe, benchmark


def monthly_panel(bars, universe, benchmark):
    """Per review month: every eligible name's forward 21-session total return."""
    sessions = sorted({d for series in bars.values() for d in series})
    index = {d: i for i, d in enumerate(sessions)}
    panel = []
    for month_end, selected in universe:
        start = next((d for d in sessions if d > month_end), None)
        if start is None or index[start] + HOLDING_SESSIONS >= len(sessions):
            continue
        end = sessions[index[start] + HOLDING_SESSIONS]
        if start not in benchmark or end not in benchmark:
            continue
        values = []
        for symbol in selected:
            series = bars.get(symbol)
            if not series or start not in series or end not in series:
                continue
            if series[start]['adjclose'] > 0:
                values.append(series[end]['adjclose'] / series[start]['adjclose'] - 1)
        if len(values) >= 50:
            panel.append((values, benchmark[end] / benchmark[start] - 1))
    return panel


def cagr(returns):
    wealth = 1.0
    for value in returns:
        wealth *= 1 + value
    return wealth ** (REBALANCES_PER_YEAR / len(returns)) - 1


def annual_sd(values):
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1)) \
        * math.sqrt(REBALANCES_PER_YEAR)


def perfect_foresight(panel, count):
    spreads = [sum(sorted(v, reverse=True)[:count]) / count - sum(v) / len(v)
               for v, _ in panel if len(v) >= count]
    return sum(spreads) / len(spreads) * REBALANCES_PER_YEAR


def random_book_active_risk(panel, count):
    """Active risk of an equal-weight `count`-name book drawn at random from the pool.

    A signal-selected book clusters, so this is a lower bound on the real
    active risk against the pool -- stated as such, not as the true value.
    """
    rng = random.Random(RANDOM_SEED)
    diffs = []
    for values, _ in panel:
        mean = sum(values) / len(values)
        diffs.extend(sum(rng.sample(values, count)) / count - mean
                     for _ in range(RANDOM_DRAWS_PER_MONTH))
    return annual_sd(diffs)


def main():
    bars, universe, benchmark = load_inputs()
    panel = monthly_panel(bars, universe, benchmark)
    pool = [sum(v) / len(v) for v, _ in panel]
    bench = [b for _, b in panel]
    years = len(panel) / REBALANCES_PER_YEAR

    pool_cagr, bench_cagr = cagr(pool), cagr(bench)
    pool_gap = pool_cagr - bench_cagr
    pool_te = annual_sd([p - b for p, b in zip(pool, bench)])

    print(f'Measured from the real point-in-time universe and prices, no options data.')
    print(f'  windows={len(panel)} ({years:.1f}y)  '
          f'median pool={sorted(len(v) for v, _ in panel)[len(panel) // 2]}')
    print()
    print('  [1] The candidate pool itself, before any stock selection:')
    print(f'      equal-weight top-200 pool (gross, no costs): CAGR {pool_cagr * 100:6.2f}%')
    print(f'      QQQ total-return proxy, same windows:        CAGR {bench_cagr * 100:6.2f}%')
    print(f'      >>> pool minus QQQ: {pool_gap * 100:+.2f}pp/yr   (pool-vs-QQQ TE {pool_te * 100:.2f}%)')
    print()

    ceilings, active_risks = {}, {}
    print('  [2] Selection ceiling and the matching active risk against the pool:')
    for count in COUNTS:
        ceilings[count] = perfect_foresight(panel, count)
        active_risks[count] = random_book_active_risk(panel, count)
        print(f'      top-{count}: perfect-foresight excess over pool '
              f'{ceilings[count] * 100:6.1f}%/yr at IC=1.0; '
              f'random-book active risk vs pool {active_risks[count] * 100:5.2f}%/yr (lower bound)')

    te_vs_bench = {}
    def nav(path):
        with path.open() as handle:
            return {r['date']: float(r['nav_usd']) for r in csv.DictReader(handle)}
    daily_bench = nav(RUN / 'QQQ-total-return-proxy-nav.csv')
    dates = sorted(daily_bench)
    bench_daily = [daily_bench[dates[i]] / daily_bench[dates[i - 1]] - 1
                   for i in range(1, len(dates))]
    for variant in ('Q20', 'M10'):
        series = nav(RUN / variant / 'nav.csv')
        strat = [series[dates[i]] / series[dates[i - 1]] - 1 for i in range(1, len(dates))]
        excess = [s - b for s, b in zip(strat, bench_daily)]
        mean = sum(excess) / len(excess)
        te_vs_bench[variant] = math.sqrt(
            sum((e - mean) ** 2 for e in excess) / (len(excess) - 1)) * math.sqrt(252)
    print(f'      measured strategy TE vs QQQ-TR: '
          + ', '.join(f'{k}={v * 100:.2f}%' for k, v in te_vs_bench.items()))
    print()

    print('  [3] Required IC, keeping the two benchmarks separate.')
    for count in COUNTS:
        ceiling = ceilings[count]
        print(f'\n      --- top-{count} (IC=1.0 ceiling {ceiling * 100:.1f}%/yr over the pool) ---')
        for transfer in TRANSFER_COEFFICIENTS:
            capacity = transfer * ceiling
            beat_pool = (TARGET_ABS_T / math.sqrt(years) * active_risks[count]) / capacity
            parity = (-pool_gap) / capacity
            target = (-pool_gap + TARGET_NET_EXCESS_PP / 100) / capacity
            proofs = [(TARGET_ABS_T / math.sqrt(years) * te - pool_gap) / capacity
                      for te in te_vs_bench.values()]
            print(f'      tc={transfer:.2f}  '
                  f'beat the POOL provably: IC={beat_pool:.3f}   |   '
                  f'reach QQQ parity: IC={parity:.3f}   '
                  f'QQQ+{TARGET_NET_EXCESS_PP:.0f}pp: IC={target:.3f}   '
                  f'prove vs QQQ: IC={min(proofs):.3f}-{max(proofs):.3f}')


if __name__ == '__main__':
    main()
