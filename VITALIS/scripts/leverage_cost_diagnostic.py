"""R011 direction 1 diagnostic: constant-leverage QQQ exposure net of real financing.

Replays the frozen QQQ total-return proxy path with daily-rebalanced constant
leverage, charging financing at the real FRED DGS3MO short rate plus a spread,
plus an optional fund expense ratio. Read-only: no simulation of stock
selection, no parameter search, no remote request, no change to prior artifacts.

This measures a leverage/risk decision, not stock-selection alpha, and the
window it can cover starts in 2005 -- see the protocol for why that matters.
"""
import csv
import json
from pathlib import Path

RUN = Path('runs/20260913T230559016875Z-pit-0f145816')
YAHOO_QQQ = Path('data/public-yahoo/QQQ-1999-01-01-2026-09-20.json')
FRED = Path('data/public-fred/DGS3MO-1999-01-01-2026-09-19.json')
TRADING_DAYS_PER_YEAR = 252
LEVERAGES = (1.0, 1.2, 1.5, 2.0, 3.0)
# Expense ratios are charged on the value of each sleeve actually held, not on
# the whole account regardless of instrument -- an earlier version overcharged
# blended exposures by up to ~37bps/yr, which is larger than the margin under test.
PLAIN_ETF_EXPENSE_BPS = 20       # QQQ
LEVERAGED_ETF_EXPENSE_BPS = 95   # QLD, 2x daily
LEVERAGED_ETF_MULTIPLE = 2.0
INSTRUMENTS = ('etf_blend', 'broker_margin', 'gross_no_cost')
SUB_WINDOWS = (('1999-2026 full', '1999-01-01', '2027-01-01'),
               ('1999-2002 dot-com', '1999-01-01', '2003-01-01'),
               ('2003-2007', '2003-01-01', '2008-01-01'),
               ('2008-2014', '2008-01-01', '2015-01-01'),
               ('2015-2025', '2015-01-01', '2026-01-01'),
               ('2016-2026 (QLD-like 10y)', '2016-06-01', '2026-06-01'))


def benchmark_returns(source='yahoo'):
    """Daily total-return series. 'yahoo' is the full QQQ history from 1999-03;
    'pit' is the frozen P004 proxy, kept as a cross-check on the overlap."""
    if source == 'pit':
        with (RUN / 'QQQ-total-return-proxy-nav.csv').open() as handle:
            nav = {row['date']: float(row['nav_usd']) for row in csv.DictReader(handle)}
    else:
        from vitalis.data import normalize
        bars, issues = normalize(json.loads(YAHOO_QQQ.read_text()))
        if issues:
            raise ValueError(f'{len(issues)} invalid bars in the QQQ snapshot')
        nav = {day: bar['adjclose'] for day, bar in bars.items()}
    dates = sorted(nav)
    return [(dates[i], nav[dates[i]] / nav[dates[i - 1]] - 1) for i in range(1, len(dates))]


def short_rate_by_day():
    csv_text = json.loads(FRED.read_text())['payload']['csv']
    out, current = {}, None
    for line in csv_text.splitlines()[1:]:
        day, value = line.split(',')
        if value.strip():
            current = float(value) / 100.0
        if current is not None:
            out[day] = current
    return out


def annual_expense_bps(instrument, leverage):
    """Expense charged on the account, given how the exposure is actually built.

    etf_blend:     hold w in a 2x ETF and 1-w in a plain ETF, w = leverage - 1.
                   Each sleeve's expense applies to that sleeve only.
    broker_margin: hold leverage x notional of the plain ETF on margin, so the
                   plain expense applies to the levered notional.
    gross_no_cost: no fund expense at all (idealised upper bound).
    """
    if instrument == 'gross_no_cost':
        return 0.0
    if instrument == 'broker_margin':
        return leverage * PLAIN_ETF_EXPENSE_BPS
    levered_sleeve = max(0.0, (leverage - 1.0) / (LEVERAGED_ETF_MULTIPLE - 1.0))
    if levered_sleeve > 1.0:
        return float('nan')  # cannot reach this leverage with a 2x sleeve alone
    return (levered_sleeve * LEVERAGED_ETF_EXPENSE_BPS
            + (1.0 - levered_sleeve) * PLAIN_ETF_EXPENSE_BPS)


def replay(returns, rates, leverage, spread_bps, expense_bps):
    """Daily-rebalanced constant leverage. Returns (CAGR, max drawdown)."""
    wealth, peak, max_drawdown, last_rate = 1.0, 1.0, 0.0, 0.0
    for day, market in returns:
        last_rate = rates.get(day, last_rate)
        financing = (leverage - 1) * (last_rate + spread_bps / 1e4) / TRADING_DAYS_PER_YEAR
        wealth *= 1 + leverage * market - financing - expense_bps / 1e4 / TRADING_DAYS_PER_YEAR
        if wealth <= 0:
            return -1.0, -1.0
        peak = max(peak, wealth)
        max_drawdown = min(max_drawdown, wealth / peak - 1)
    years = len(returns) / TRADING_DAYS_PER_YEAR
    return wealth ** (1 / years) - 1, max_drawdown


def rolling_windows(returns, rates, years, step_sessions=21):
    """Distribution of leveraged-vs-unleveraged outcomes over every rolling window.

    Windows overlap heavily, so the win rate is NOT a count of independent
    trials: 27.5 years of history holds roughly 2-3 independent 10-year
    windows regardless of how finely they are stepped.
    """
    span = years * TRADING_DAYS_PER_YEAR
    rows = []
    for start in range(0, len(returns) - span, step_sessions):
        segment = returns[start:start + span]
        base, _ = replay(segment, rates, 1.0, 0, PLAIN_ETF_EXPENSE_BPS)
        rows.append((segment[0][0], {lev: replay(segment, rates, lev, 50, annual_expense_bps('etf_blend', lev))
                                     for lev in (1.2, 1.5, 2.0)}, base))
    return rows


def main():
    returns, rates = benchmark_returns('yahoo'), short_rate_by_day()
    print(f'QQQ total return (Yahoo full history), {returns[0][0]} .. {returns[-1][0]} '
          f'({len(returns) / TRADING_DAYS_PER_YEAR:.1f}y), daily-rebalanced constant leverage')
    print(f'{"lev":>5}  {"instrument":<14}{"spread_bps":>11}{"expense_bps":>12}'
          f'{"CAGR":>9}{"max_dd":>11}{"vs 1.0x":>10}')
    baseline, _ = replay(returns, rates, 1.0, 0, PLAIN_ETF_EXPENSE_BPS)
    for leverage in LEVERAGES:
        for instrument, spread in (('etf_blend', 50), ('broker_margin', 150),
                                   ('gross_no_cost', 0)):
            expense = annual_expense_bps(instrument, leverage)
            if expense != expense:
                print(f'{leverage:5.1f}  {instrument:<14}{spread:11d}'
                      f'{"n/a":>12}{"unreachable with a 2x sleeve":>30}')
                continue
            annual, drawdown = replay(returns, rates, leverage, spread, expense)
            print(f'{leverage:5.1f}  {instrument:<14}{spread:11d}{expense:12.1f}'
                  f'{annual * 100:8.2f}%{drawdown * 100:10.4f}%'
                  f'{(annual - baseline) * 100:+9.2f}pp')
    print(f'  baseline 1.0x with the plain {PLAIN_ETF_EXPENSE_BPS}bps expense: '
          f'{baseline * 100:.4f}% CAGR')

    print('\nSub-window sensitivity (50bps spread, 95bps expense above 1.0x):')
    for label, low, high in SUB_WINDOWS:
        window = [(d, r) for d, r in returns if low <= d < high]
        if not window:
            continue
        cells = []
        for leverage in (1.0, 1.5, 2.0):
            annual, drawdown = replay(window, rates, leverage, 50, annual_expense_bps('etf_blend', leverage))
            cells.append(f'{leverage:.1f}x {annual * 100:6.2f}% (dd {drawdown * 100:6.1f}%)')
        print(f'  {label:26s} ' + '   '.join(cells))

    for years in (5, 10, 15):
        rows = rolling_windows(returns, rates, years)
        print(f'\nRolling {years}-year windows, stepped monthly: n={len(rows)} overlapping '
              f'(~{len(returns) / TRADING_DAYS_PER_YEAR / years:.1f} independent)')
        print(f'{"lev":>5}{"win rate":>10}{"median":>10}{"p10":>9}{"p90":>9}{"worst dd":>10}')
        for leverage in (1.2, 1.5, 2.0):
            excess = sorted(cells[leverage][0] - base for _, cells, base in rows)
            worst = min(cells[leverage][1] for _, cells, _ in rows)
            quantile = lambda q: excess[int(q * (len(excess) - 1))]
            print(f'{leverage:5.1f}{sum(1 for e in excess if e > 0) / len(excess) * 100:9.0f}%'
                  f'{quantile(0.5) * 100:9.2f}pp{quantile(0.1) * 100:8.2f}'
                  f'{quantile(0.9) * 100:9.2f}{worst * 100:9.1f}%')

    overlap = benchmark_returns('pit')
    lo, hi = overlap[0][0], overlap[-1][0]
    same = [(d, r) for d, r in returns if lo <= d <= hi]
    a, _ = replay(same, rates, 1.0, 0, 0)
    b, _ = replay(overlap, rates, 1.0, 0, 0)
    print(f'\nCross-check on the overlap {lo}..{hi}: '
          f'Yahoo {a * 100:.2f}% vs frozen P004 proxy {b * 100:.2f}% CAGR')


if __name__ == '__main__':
    main()
