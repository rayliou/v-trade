"""Meaningful accounting and causality checks; all fixtures are synthetic."""

import copy
import unittest

from vitalis.data import normalize
from vitalis.engine import choose, percentile, rank_signals, simulate


class EngineTests(unittest.TestCase):
    def config(self):
        return {"evaluation_start": "2025-01-02", "evaluation_end": "2025-01-06",
                "symbols": {"A": "x"}, "minimum_adv_usd": 0,
                "sector_weight_cap": 0.3, "volatility_target": 0.15,
                "annual_system_cash_cost_usd": 0}

    def test_split_and_dividend_preserve_real_wealth(self):
        dates = ["2024-12-31", "2025-01-02", "2025-01-03", "2025-01-06"]
        series = {d: {"open": 100, "close": 100, "split": 1,
                      "dividend": 0, "adjclose": 100, "dollar_volume": 1e8} for d in dates}
        series["2025-01-03"].update(open=50, close=50, split=2)
        series["2025-01-06"].update(open=49, close=49, dividend=1)
        summary, nav, trades, holdings, *_ = simulate({"QQQ": series}, dates, self.config(), 1000, 0, "QQQ")
        self.assertEqual([r["nav_usd"] for r in nav], [1000, 1000, 1000])
        self.assertEqual(summary["dividends_usd"], 20)
        self.assertEqual(holdings[-1]["quantity"], 20)
        self.assertEqual(trades[0]["signal_date"], "2024-12-31")

    def test_next_open_and_cost_are_not_same_close(self):
        dates = ["2024-12-31", "2025-01-02"]
        series = {d: {"open": 100, "close": 110, "split": 1, "dividend": 0,
                      "adjclose": 110, "dollar_volume": 1e8} for d in dates}
        config = self.config()
        config["evaluation_end"] = "2025-01-02"
        summary, nav, trades, *_ = simulate({"QQQ": series}, dates, config, 1000, 10, "QQQ")
        self.assertEqual(trades[0]["price_usd"], 100)
        self.assertEqual(trades[0]["quantity"], 9)
        self.assertAlmostEqual(summary["execution_cost_usd"], 0.9)
        self.assertAlmostEqual(nav[0]["cash_usd"], 99.1)
        self.assertAlmostEqual(nav[0]["nav_usd"], 1089.1)

    def test_ranking_ignores_future_prices(self):
        dates = [f"session-{i:03}" for i in range(270)]
        bars = {s: {d: {"adjclose": 100 + i * slope, "dollar_volume": 1e8}
                    for i, d in enumerate(dates)} for s, slope in (("A", 1), ("B", 0.5))}
        before = rank_signals(bars, dates, 252, bars, 0)
        changed = copy.deepcopy(bars)
        for d in dates[253:]:
            changed["B"][d]["adjclose"] = 1e9
        self.assertEqual(before, rank_signals(changed, dates, 252, changed, 0))
        self.assertEqual(before[0]["symbol"], "A")

    def test_hysteresis_and_sector_cap_leave_cash(self):
        ranking = [{"symbol": s, "rank": i + 1} for i, s in enumerate("ABCDEF")]
        sectors = {s: "x" for s in "ABCDEF"}
        self.assertEqual(choose(ranking, ["D"], 2, sectors, 0.5), ["D"])

    def test_percentile_ties_use_average_rank(self):
        self.assertEqual(percentile({"A": 1, "B": 1, "C": 2}), {"A": 0.25, "B": 0.25, "C": 1.0})

    def test_provider_split_units_reconstruct_nominal_prices(self):
        payload = {"chart": {"result": [{"meta": {"currency": "USD"},
                    "timestamp": [1735830000, 1735916400],
                    "events": {"splits": {"x": {"date": 1735916400, "numerator": 2, "denominator": 1}}},
                    "indicators": {"quote": [{"open": [50, 50], "close": [50, 50], "volume": [200, 200]}],
                                   "adjclose": [{"adjclose": [50, 50]}]}}]}}
        bars, _ = normalize({"symbol": "A", "payload": payload})
        first, second = sorted(bars)
        self.assertEqual(bars[first]["open"], 100)
        self.assertEqual(bars[second]["split"], 2)
        self.assertEqual(bars[second]["open"], 50)


if __name__ == "__main__":
    unittest.main()
