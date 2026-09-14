"""Cross-source close-price comparison: synthetic logic + a real-data proof."""

import glob
import unittest
import zipfile
import csv
import io
from pathlib import Path

from vitalis.data import download, normalize
from vitalis.reconcile import compare_closes


class CompareClosesTests(unittest.TestCase):
    def test_matching_closes_produce_no_discrepancy(self):
        yahoo = {"2020-01-02": {"close": 100.0}}
        sharadar = {"2020-01-02": {"closeunadj": "100.0001"}}
        result = compare_closes(yahoo, sharadar)
        self.assertEqual(result["compared_dates"], 1)
        self.assertEqual(result["discrepancies"], [])

    def test_large_relative_difference_is_reported_not_hidden(self):
        yahoo = {"2020-01-02": {"close": 110.0}}
        sharadar = {"2020-01-02": {"closeunadj": "100.0"}}
        result = compare_closes(yahoo, sharadar, relative_tolerance=0.001)
        self.assertEqual(len(result["discrepancies"]), 1)
        self.assertAlmostEqual(result["discrepancies"][0]["relative_error"], 0.1)

    def test_dates_present_in_only_one_source_are_listed_not_dropped(self):
        yahoo = {"2020-01-02": {"close": 100.0}, "2020-01-03": {"close": 101.0}}
        sharadar = {"2020-01-02": {"closeunadj": "100.0"}}
        result = compare_closes(yahoo, sharadar)
        self.assertEqual(result["compared_dates"], 1)
        self.assertEqual(result["yahoo_only_dates"], ["2020-01-03"])
        self.assertEqual(result["sharadar_only_dates"], [])

    def test_invalid_sharadar_close_is_flagged_not_silently_skipped(self):
        yahoo = {"2020-01-02": {"close": 100.0}}
        sharadar = {"2020-01-02": {"closeunadj": "N/A"}}
        result = compare_closes(yahoo, sharadar)
        self.assertEqual(result["discrepancies"], [{"date": "2020-01-02", "issue": "invalid_sharadar_close"}])


class RealDataProofTests(unittest.TestCase):
    """Cross-checks the existing Yahoo adapter against real, licensed Sharadar
    stocks data for the P001 universe. Skips if the local licensed cache is
    not present.
    """

    def setUp(self):
        self.cache_dir = Path("data/authorized/sharadar")
        self.path = self.cache_dir / "stocks-bulk-full.csv.zip"
        if not self.path.exists():
            self.skipTest("no local authorized Sharadar stocks bulk file present")

    def test_aapl_closes_agree_with_yahoo_within_half_a_percent_almost_always(self):
        sharadar_by_date = {}
        with zipfile.ZipFile(self.path) as zf:
            with zf.open(zf.namelist()[0]) as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                for row in reader:
                    if row["ticker"] == "AAPL":
                        sharadar_by_date[row["date"]] = row
        if not sharadar_by_date:
            self.skipTest("no AAPL rows in the real bulk file")
        yahoo_path = Path("data/public-yahoo/AAPL-2020-01-01-2026-09-13.json")
        if not yahoo_path.exists():
            self.skipTest("no cached Yahoo AAPL data present")
        envelope = download("AAPL", "2020-01-01", "2026-09-13", "data/public-yahoo")
        yahoo_bars, _ = normalize(envelope)
        result = compare_closes(yahoo_bars, sharadar_by_date)
        self.assertGreater(result["compared_dates"], 1000)
        bad_fraction = len(result["discrepancies"]) / result["compared_dates"]
        self.assertLess(bad_fraction, 0.01, f"too many discrepancies: {result['discrepancies']}")


if __name__ == "__main__":
    unittest.main()
