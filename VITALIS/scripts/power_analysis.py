"""Read-only statistical-power diagnostic backing docs/review/11.

Recomputes tracking error against the QQQ total-return proxy from the frozen
P004-corrected ledgers, then converts it into the sample length that would be
needed to separate a hypothesised excess return from zero. No simulation,
parameter search, remote request, or change to prior run artifacts.
"""
import csv
import math
from pathlib import Path

RUN = Path('runs/20260913T230559016875Z-pit-0f145816')
VARIANTS = ('M10', 'M20', 'M10-risk15', 'Q10', 'Q20')
HYPOTHETICAL_EXCESS_PP = (1.0, 2.0, 3.0, 5.0)
TARGET_ABS_T = 2.0
TRADING_DAYS_PER_YEAR = 252
QQQ_CAGR = 0.1477          # docs/review/10, primary USD300k/10bps/$828 scenario
QQQ_MAX_DRAWDOWN = 0.534
DRAWDOWN_CEILING = 0.30    # docs/review/02 research acceptance ceiling


def read_nav(path):
    with path.open() as handle:
        return {row['date']: float(row['nav_usd']) for row in csv.DictReader(handle)}


def returns_on(series, dates):
    values = [series[d] for d in dates]
    return [values[i] / values[i - 1] - 1 for i in range(1, len(values))]


def mean_sd(values):
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    return mean, sd


def main():
    benchmark = read_nav(RUN / 'QQQ-total-return-proxy-nav.csv')
    dates = sorted(benchmark)
    benchmark_returns = returns_on(benchmark, dates)
    sessions = len(benchmark_returns)
    years = sessions / TRADING_DAYS_PER_YEAR
    bench_mean, bench_sd = mean_sd(benchmark_returns)

    print(f'sessions={sessions} years={years:.2f}')
    print(f'QQQ-TR annual_vol={bench_sd * math.sqrt(TRADING_DAYS_PER_YEAR) * 100:.2f}%')
    print()
    print(f'{"variant":12s}{"ann_vol":>9s}{"te":>9s}{"excess":>9s}'
          f'{"ir":>8s}{"t":>8s}{"corr":>7s}{"yrs_for_|t|=2":>15s}')

    tracking_errors = []
    for variant in VARIANTS:
        series = read_nav(RUN / variant / 'nav.csv')
        missing = [d for d in dates if d not in series]
        if missing:
            raise ValueError(f'{variant}: {len(missing)} benchmark sessions missing')
        strategy_returns = returns_on(series, dates)
        excess = [s - b for s, b in zip(strategy_returns, benchmark_returns)]
        strat_mean, strat_sd = mean_sd(strategy_returns)
        excess_mean, excess_sd = mean_sd(excess)

        tracking_error = excess_sd * math.sqrt(TRADING_DAYS_PER_YEAR)
        annual_excess = excess_mean * TRADING_DAYS_PER_YEAR
        information_ratio = annual_excess / tracking_error
        t_stat = information_ratio * math.sqrt(years)
        years_needed = (TARGET_ABS_T / information_ratio) ** 2
        covariance = sum(
            (s - strat_mean) * (b - bench_mean)
            for s, b in zip(strategy_returns, benchmark_returns)
        ) / (len(strategy_returns) - 1)
        correlation = covariance / (strat_sd * bench_sd)
        tracking_errors.append(tracking_error)

        print(f'{variant:12s}'
              f'{strat_sd * math.sqrt(TRADING_DAYS_PER_YEAR) * 100:8.2f}%'
              f'{tracking_error * 100:8.2f}%'
              f'{annual_excess * 100:8.2f}%'
              f'{information_ratio:8.3f}{t_stat:8.2f}{correlation:7.3f}'
              f'{years_needed:15.1f}')

    print()
    print('Years of history needed to reach |t|=2 on a hypothetical true excess:')
    for tracking_error in sorted(tracking_errors):
        row = '  '.join(
            f'+{pp:.0f}pp: {(TARGET_ABS_T / (pp / 100 / tracking_error)) ** 2:7.0f}y'
            for pp in HYPOTHETICAL_EXCESS_PP
        )
        print(f'  te={tracking_error * 100:5.2f}%  {row}')

    print()
    print('Excess return needed to reach |t|=2 within the available sample:')
    for tracking_error in sorted(tracking_errors):
        needed_ir = TARGET_ABS_T / math.sqrt(years)
        print(f'  te={tracking_error * 100:5.2f}%  ir={needed_ir:.3f}  '
              f'excess={needed_ir * tracking_error * 100:.2f}pp')

    print()
    benchmark_calmar = QQQ_CAGR / QQQ_MAX_DRAWDOWN
    required_calmar = QQQ_CAGR / DRAWDOWN_CEILING
    print(f'QQQ-TR calmar={benchmark_calmar:.3f}; joint acceptance floor '
          f'calmar>={required_calmar:.3f} ({required_calmar / benchmark_calmar:.2f}x)')


if __name__ == '__main__':
    main()
