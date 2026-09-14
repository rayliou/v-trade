"""build_quality_by_review_month(): real-data proof only (tightly coupled to
the real bulk fundamentals/actions files; the underlying primitives --
pit.py, sic_history.py, quality.py -- already have their own unit tests)."""

import json
import unittest
from pathlib import Path

from vitalis.run_pit import build_quality_by_review_month
from vitalis.universe import distinct_trading_days, month_end_dates, security_master


class BuildQualityByReviewMonthTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = Path("data/authorized/sharadar")
        required = ["tickers-bulk-full.csv.zip", "daily-bulk-full.csv.zip",
                   "actions-bulk-full.csv.zip", "fundamentals-bulk-full.csv.zip"]
        if not all((self.data_dir / name).exists() for name in required):
            self.skipTest("no local authorized Sharadar bulk cache present")

    def test_real_quality_scores_are_sensible_for_the_p001_universe(self):
        master = security_master(self.data_dir / "tickers-bulk-full.csv.zip")
        all_days = distinct_trading_days(self.data_dir / "daily-bulk-full.csv.zip")
        trading_days_sorted = sorted(d for d in all_days if d <= "2025-12-31")
        months = [d for d in month_end_dates(all_days) if d[:7] == "2024-01"]
        with open("config/prototype-v1.json") as stream:
            symbols = list(json.load(stream)["symbols"])
        symbols_by_review_month = {m[:7]: {s: "x" for s in symbols} for m in months}

        result = build_quality_by_review_month(
            self.data_dir, symbols, master, months, trading_days_sorted, symbols_by_review_month)
        self.assertEqual(set(result), {"2024-01"})
        scores = result["2024-01"]
        for score in scores.values():
            self.assertTrue(0.0 <= score <= 1.0)
        # Sanity against already-established real findings (08 decision log,
        # 2026-09-13 quality-factor entries): NVDA highest, a real bank near
        # the bottom half via the neutral-0.5 fallback rather than excluded.
        ranked = sorted(scores, key=lambda t: -scores[t])
        self.assertEqual(ranked[0], "NVDA")
        for bank in ("JPM", "BAC"):
            if bank in scores:
                self.assertAlmostEqual(scores[bank], 0.5)

    def test_a_reportperiod_after_filing_date_is_dropped_not_a_crash(self):
        """Regression: NGVT has a real ART row filed 2015-12-10 for report
        period 2015-12-31 -- the filing predates its own claimed period end,
        most likely a spin-off-era pro-forma artifact (Ingevity's 2015-2016
        separation from WestRock). pit.normalize_fundamentals() correctly
        rejects that as invalid; build_quality_by_review_month() must drop
        it explicitly rather than let one bad row crash the whole pass.
        """
        master = security_master(self.data_dir / "tickers-bulk-full.csv.zip")
        all_days = distinct_trading_days(self.data_dir / "daily-bulk-full.csv.zip")
        trading_days_sorted = sorted(d for d in all_days if d <= "2016-06-30")
        months = [d for d in month_end_dates(all_days) if d[:7] == "2016-01"]
        symbols_by_review_month = {m[:7]: {"NGVT": "x"} for m in months}

        result = build_quality_by_review_month(
            self.data_dir, ["NGVT"], master, months, trading_days_sorted, symbols_by_review_month)
        self.assertEqual(set(result), {"2016-01"})


if __name__ == "__main__":
    unittest.main()
