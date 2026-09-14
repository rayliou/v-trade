"""Paired block-bootstrap: pairing, determinism, and input validation."""

import unittest

from vitalis.stats import daily_returns, paired_block_bootstrap


class StatsTests(unittest.TestCase):
    def test_identical_series_has_zero_diff_at_every_percentile(self):
        # A varied, non-constant series so path-dependent drawdown is nontrivial;
        # if strategy and benchmark blocks were resampled independently rather
        # than with the same shared indices, differing block orders would almost
        # certainly produce a nonzero max-drawdown differential somewhere.
        returns = [0.01, -0.02, 0.03, -0.01, 0.015, -0.03, 0.02, -0.005, 0.01, -0.02] * 30
        result = paired_block_bootstrap(returns, list(returns), block_trading_days=21,
                                        replicates=200, seed=7)
        for point in ("p05", "p50", "p95"):
            self.assertAlmostEqual(result["cagr_diff_pp"][point], 0.0)
            self.assertAlmostEqual(result["max_drawdown_diff_pp"][point], 0.0)
            self.assertAlmostEqual(result["sharpe_diff"][point], 0.0)

    def test_same_seed_is_reproducible(self):
        returns = [0.01, -0.02, 0.015, 0.0, -0.01] * 60
        other = [0.012, -0.018, 0.01, 0.002, -0.008] * 60
        first = paired_block_bootstrap(returns, other, block_trading_days=21, replicates=150, seed=42)
        second = paired_block_bootstrap(returns, other, block_trading_days=21, replicates=150, seed=42)
        self.assertEqual(first, second)

    def test_mismatched_length_and_oversized_block_are_rejected(self):
        with self.assertRaises(ValueError):
            paired_block_bootstrap([0.01, 0.02], [0.01], block_trading_days=1, replicates=10, seed=1)
        with self.assertRaises(ValueError):
            paired_block_bootstrap([0.01, 0.02], [0.01, 0.02], block_trading_days=5, replicates=10, seed=1)

    def test_daily_returns_matches_manual_compounding(self):
        nav = [{"nav_usd": 110.0}, {"nav_usd": 121.0}]
        result = daily_returns(nav, 100.0)
        self.assertAlmostEqual(result[0], 0.1)
        self.assertAlmostEqual(result[1], 0.1)

    def test_a_fund_ruined_to_exactly_zero_reads_as_zero_return_not_a_crash(self):
        """Regression: engine.simulate() can drive NAV to exactly zero and
        cap it there once a fund is ruined (see docs/review/08, 2026-09-14);
        this function feeds run_p006.py's bootstrap and must not divide by
        that zero on the following, still-zero session.
        """
        nav = [{"nav_usd": 50.0}, {"nav_usd": 0.0}, {"nav_usd": 0.0}]
        result = daily_returns(nav, 100.0)
        self.assertAlmostEqual(result[0], -0.5)
        self.assertEqual(result[1], -1.0)
        self.assertEqual(result[2], 0.0)


if __name__ == "__main__":
    unittest.main()
