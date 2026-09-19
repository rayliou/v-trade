"""Ex-ante power calculation for the P009 L1 shape, using small-cap parameters.

Mirrors review module 11 section 8.3, but every input is measured on the
rank 1000-3000 pool itself rather than carried over from the top-200 shape.
Module 11 section 8 warns explicitly against scaling the large-cap table by
the gap ratio: small caps have both a wider cross-section (which helps a
signal) and a bigger deficit to QQQ (which hurts), and the two do not cancel
in any predictable way.

Reads the return-vector cache written by m1_smallcap_pool_benchmark.py, so it
rescans nothing. Signal strength (IC) is a grid of ASSUMPTIONS, not an
estimate from this data. Not a backtest and not investment evidence.
"""
import gzip
import json
import math
import random
from pathlib import Path
from statistics import NormalDist

CACHE = Path('runs/m1-primary-band-returns.json.gz')
OUT = Path('runs/m1-smallcap-power.json')
COUNTS = (20, 40)                      # P009 L1 frozen holding counts
TRANSFER_COEFFICIENTS = (1.00, 0.60, 0.40)
REBALANCES_PER_YEAR = 12
TARGET_ABS_T = 2.0
TARGET_NET_EXCESS = 0.02
RANDOM_DRAWS_PER_WINDOW = 200
RANDOM_SEED = 0


def annualise(period_returns):
    wealth = 1.0
    for value in period_returns:
        wealth *= 1 + value
    return wealth ** (REBALANCES_PER_YEAR / len(period_returns)) - 1


def annual_sd(values):
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1)) \
        * math.sqrt(REBALANCES_PER_YEAR)


def main():
    payload = json.loads(gzip.open(CACHE, 'rt').read())
    windows = payload['windows']
    years = len(windows) / REBALANCES_PER_YEAR
    pool = [sum(w['returns']) / len(w['returns']) for w in windows]
    bench = [w['benchmark'] for w in windows]
    sizes = sorted(len(w['returns']) for w in windows)

    pool_gap = annualise(pool) - annualise(bench)
    pool_te = annual_sd([p - b for p, b in zip(pool, bench)])
    dispersions = sorted(annual_sd([r]) if False else
                         math.sqrt(sum((r - sum(w['returns']) / len(w['returns'])) ** 2
                                       for r in w['returns']) / (len(w['returns']) - 1))
                         for w in windows)

    print(f'rank {payload["band"][0]}-{payload["band"][1]}, convention '
          f'{payload["convention"]}, {len(windows)} windows ({years:.1f}y), '
          f'median pool size {sizes[len(sizes) // 2]:,}')
    print(f'  median cross-sectional sd of 21-session returns '
          f'{dispersions[len(dispersions) // 2] * 100:.2f}%   '
          f'(top-200 shape measured 6.18%)')
    print(f'  pool CAGR {annualise(pool) * 100:.2f}%  vs QQQ {annualise(bench) * 100:.2f}%'
          f'  gap {pool_gap * 100:+.2f}pp   pool-vs-QQQ TE {pool_te * 100:.2f}%')

    rng = random.Random(RANDOM_SEED)
    ceilings, active_risks, tracking = {}, {}, {}
    for count in COUNTS:
        spreads, diffs = [], []
        for w in windows:
            values = w['returns']
            if len(values) < count:
                continue
            mean = sum(values) / len(values)
            spreads.append(sum(sorted(values, reverse=True)[:count]) / count - mean)
            diffs.extend(sum(rng.sample(values, count)) / count - mean
                         for _ in range(RANDOM_DRAWS_PER_WINDOW))
        ceilings[count] = sum(spreads) / len(spreads) * REBALANCES_PER_YEAR
        active_risks[count] = annual_sd(diffs)
        # A book's tracking error against QQQ combines its active risk against
        # the pool with the pool's own deviation from QQQ. Treating the two as
        # independent is an assumption, stated here rather than measured.
        tracking[count] = math.sqrt(active_risks[count] ** 2 + pool_te ** 2)
        normal_lambda = (NormalDist().pdf(NormalDist().inv_cdf(1 - count / sizes[len(sizes) // 2]))
                         / (count / sizes[len(sizes) // 2]))
        print(f'  top-{count}: perfect-foresight excess over pool '
              f'{ceilings[count] * 100:7.1f}%/yr   active risk vs pool '
              f'{active_risks[count] * 100:5.2f}%   implied TE vs QQQ '
              f'{tracking[count] * 100:5.2f}%   (normal lambda {normal_lambda:.2f})')

    print(f'\nRequired information coefficient:')
    print(f'{"book":>6}{"tc":>6}{"beat pool":>12}{"QQQ parity":>13}'
          f'{"QQQ+2pp":>10}{"prove vs QQQ":>15}')
    results = {}
    for count in COUNTS:
        for transfer in TRANSFER_COEFFICIENTS:
            capacity = transfer * ceilings[count]
            row = {
                'beat_pool_provably': (TARGET_ABS_T / math.sqrt(years)
                                       * active_risks[count]) / capacity,
                'qqq_parity': (-pool_gap) / capacity,
                'qqq_plus_2pp': (-pool_gap + TARGET_NET_EXCESS) / capacity,
                'prove_vs_qqq': (TARGET_ABS_T / math.sqrt(years) * tracking[count]
                                 - pool_gap) / capacity,
            }
            results[f'top{count}_tc{transfer:.2f}'] = row
            print(f'{count:6d}{transfer:6.2f}{row["beat_pool_provably"]:12.3f}'
                  f'{row["qqq_parity"]:13.3f}{row["qqq_plus_2pp"]:10.3f}'
                  f'{row["prove_vs_qqq"]:15.3f}')

    OUT.write_text(json.dumps({
        'windows': len(windows), 'years': years,
        'median_pool_size': sizes[len(sizes) // 2],
        'median_cross_sectional_sd': dispersions[len(dispersions) // 2],
        'pool_cagr': annualise(pool), 'qqq_cagr': annualise(bench),
        'pool_gap': pool_gap, 'pool_te_vs_qqq': pool_te,
        'ceilings': ceilings, 'active_risk_vs_pool': active_risks,
        'implied_te_vs_qqq': tracking, 'required_ic': results}, indent=2))
    print(f'\nwritten: {OUT}')
    print('IC values are assumptions from the literature, not estimates from this data. '
          'Published cross-sectional equity signals report roughly 0.02-0.05 in sample, '
          'before post-publication decay.')


if __name__ == '__main__':
    main()
