"""Paired circular block-bootstrap intervals for a strategy-vs-benchmark comparison.

Per docs/review/04-validation-protocol.md section 4: comparisons must resample the
same time blocks for both series (preserving their shared market path), and block
length must be fixed before looking at results, not chosen to flatter one outcome.

This describes sampling uncertainty in one fixed historical path under one fixed
rule set. It is not a significance test that by itself clears look-ahead bias,
survivorship bias, or multiple-comparison risk: 04 still requires registering every
configuration actually run and applying a DSR-style correction across all of them.
"""

import math
import random
import statistics


def daily_returns(nav_rows, initial):
    values = [initial] + [row["nav_usd"] for row in nav_rows]
    return [b / a - 1 for a, b in zip(values, values[1:])]


def _path_metrics(returns):
    value, high, worst = 1.0, 1.0, 0.0
    for r in returns:
        value *= 1 + r
        high = max(high, value)
        worst = min(worst, value / high - 1)
    cagr = value ** (252 / len(returns)) - 1
    vol = statistics.stdev(returns) * math.sqrt(252) if len(returns) > 1 else 0.0
    sharpe = statistics.mean(returns) * 252 / vol if vol else None
    return cagr, sharpe, worst


def _circular_block_indices(n, block_length, rng):
    """One resample's index path: whole blocks with wraparound, then truncated to n."""
    indices = []
    while len(indices) < n:
        start = rng.randrange(n)
        indices.extend((start + i) % n for i in range(block_length))
    return indices[:n]


def _percentiles(values, points=(0.05, 0.50, 0.95)):
    if not values:
        return None
    ordered = sorted(values)

    def one(p):
        k = (len(ordered) - 1) * p
        floor, ceil = math.floor(k), math.ceil(k)
        if floor == ceil:
            return ordered[int(k)]
        return ordered[floor] + (ordered[ceil] - ordered[floor]) * (k - floor)

    return {f"p{int(p * 100):02}": one(p) for p in points}


def paired_block_bootstrap(strategy_returns, benchmark_returns, block_trading_days, replicates, seed):
    """Resample paired (strategy, benchmark) daily returns as circular blocks and
    return percentile intervals for the CAGR, Sharpe, and max-drawdown differentials.

    Requires equal-length, date-aligned daily return series (same session order).
    Deterministic for a fixed seed, so results are reproducible from frozen config.
    """
    if len(strategy_returns) != len(benchmark_returns):
        raise ValueError("Paired bootstrap requires equal-length, date-aligned return series")
    n = len(strategy_returns)
    if n < block_trading_days:
        raise ValueError("Block length exceeds available sessions")
    rng = random.Random(seed)
    cagr_diffs, sharpe_diffs, drawdown_diffs = [], [], []
    for _ in range(replicates):
        idx = _circular_block_indices(n, block_trading_days, rng)
        s_cagr, s_sharpe, s_dd = _path_metrics([strategy_returns[i] for i in idx])
        b_cagr, b_sharpe, b_dd = _path_metrics([benchmark_returns[i] for i in idx])
        cagr_diffs.append(s_cagr - b_cagr)
        drawdown_diffs.append(s_dd - b_dd)
        if s_sharpe is not None and b_sharpe is not None:
            sharpe_diffs.append(s_sharpe - b_sharpe)

    def scaled_pp(values):
        pct = _percentiles(values)
        return {k: v * 100 for k, v in pct.items()} if pct else None

    return {
        "block_trading_days": block_trading_days, "replicates": replicates, "seed": seed,
        "sessions": n,
        "cagr_diff_pp": scaled_pp(cagr_diffs),
        "max_drawdown_diff_pp": scaled_pp(drawdown_diffs),
        "sharpe_diff": _percentiles(sharpe_diffs),
        "sharpe_undefined_replicate_count": replicates - len(sharpe_diffs),
    }
