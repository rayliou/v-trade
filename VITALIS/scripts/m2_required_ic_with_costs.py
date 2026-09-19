"""Fold M2's measured costs back into the P009 power table.

Reads the two frozen JSON products (the small-cap power inputs and the cost
calibration) and recomputes the required information coefficient with a
transaction-cost term. No scan, no strategy run, no new data.
"""
import json
import math
from pathlib import Path

POWER = Path('runs/m1-smallcap-power.json')
COSTS = Path('runs/m2-smallcap-cost-calibration.json')
OUT = Path('runs/m2-required-ic-with-costs.json')

TRANSFER_COEFFICIENT = 0.40       # Grinold-Clarke mid-range for this constraint set
TARGET_ABS_T = 2.0
TARGET_EXCESS = 0.02
CEILING_SCREEN = 'adv>=$5000k, end price required'
LITERATURE_IC = (0.02, 0.05)


def main():
    power, costs = json.loads(POWER.read_text()), json.loads(COSTS.read_text())
    years, gap = power['years'], power['pool_gap']
    tracking = power['implied_te_vs_qqq']['20']
    raw_ceiling = power['ceilings']['20']
    screened = costs['ceilings'][CEILING_SCREEN]['ceiling_pct_per_year'] / 100
    capacity = TRANSFER_COEFFICIENT * screened
    detection = TARGET_ABS_T / math.sqrt(years) * tracking

    print(f'perfect-foresight ceiling: raw {raw_ceiling * 100:.1f}%/yr  ->  '
          f'{screened * 100:.1f}%/yr after "{CEILING_SCREEN}"  '
          f'({(screened / raw_ceiling - 1) * 100:+.1f}%)')
    print(f'pool gap {gap * 100:+.2f}pp   implied TE vs QQQ {tracking * 100:.2f}%   '
          f'tc {TRANSFER_COEFFICIENT:.2f}   capacity {capacity * 100:.0f}%/yr\n')

    print(f'{"turnover":>10}{"cost pp/yr":>12}{"QQQ parity":>13}{"QQQ+2pp":>10}'
          f'{"prove vs QQQ":>15}{"vs literature":>16}')
    table = {}
    reference = costs['costs']['300000_20']['annual_cost_pp']
    for label in sorted(reference, key=lambda k: float(k.rstrip('%'))):
        cost = reference[label] / 100
        row = {'cost_pp': reference[label],
               'qqq_parity': (-gap + cost) / capacity,
               'qqq_plus_2pp': (-gap + cost + TARGET_EXCESS) / capacity,
               'prove_vs_qqq': (detection - gap + cost) / capacity}
        table[label] = row
        verdict = ('parity inside' if row['qqq_parity'] <= LITERATURE_IC[1]
                   else 'all above range')
        print(f'{label:>10}{reference[label]:11.2f}p{row["qqq_parity"]:13.3f}'
              f'{row["qqq_plus_2pp"]:10.3f}{row["prove_vs_qqq"]:15.3f}{verdict:>16}')

    print(f'\nPublished cross-sectional signals report about '
          f'{LITERATURE_IC[0]:.2f}-{LITERATURE_IC[1]:.2f} in sample, before the '
          f'35-58% post-publication decay in McLean-Pontiff.')
    OUT.write_text(json.dumps({'transfer_coefficient': TRANSFER_COEFFICIENT,
                               'ceiling_screen': CEILING_SCREEN,
                               'screened_ceiling': screened, 'pool_gap': gap,
                               'implied_te_vs_qqq': tracking,
                               'account': '300000_20', 'required_ic': table}, indent=2))
    print(f'written: {OUT}')


if __name__ == '__main__':
    main()
