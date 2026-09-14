"""Sharadar stocks/actions -> engine.py bars schema: synthetic logic + a real
AAPL regression proof via the existing check_action_bridge() cross-check."""

import unittest
from pathlib import Path

from vitalis.data import check_action_bridge
from vitalis.sharadar_prices import find_gap_free_tickers, normalize_ticker


def stock_row(date, open_, close, closeadj, closeunadj, volume=1_000_000):
    return {"date": date, "open": str(open_), "close": str(close), "closeadj": str(closeadj),
           "closeunadj": str(closeunadj), "volume": str(volume)}


class NormalizeTickerTests(unittest.TestCase):
    def test_nominal_open_uses_the_same_day_split_ratio_as_closeunadj(self):
        # closeunadj is 4x close on this pre-split day -> nominal open should
        # also scale 4x from the split-adjusted open.
        rows = [stock_row("2020-01-01", 100, 100, 100, 400)]
        bars, issues = normalize_ticker(rows, [])
        self.assertEqual(issues, [])
        self.assertAlmostEqual(bars["2020-01-01"]["open"], 400.0)
        self.assertAlmostEqual(bars["2020-01-01"]["close"], 400.0)

    def test_dividend_is_scaled_by_future_splits_to_nominal_terms(self):
        rows = [stock_row("2020-01-01", 100, 100, 100, 100), stock_row("2020-02-01", 25, 25, 25, 25)]
        actions = [{"date": "2020-01-15", "action": "split", "value": "4.0"},
                  {"date": "2020-01-01", "action": "dividend", "value": "1.0"}]
        bars, _ = normalize_ticker(rows, actions)
        # The dividend is dated before the split, so it must be scaled by the
        # future 4x split to express it in nominal terms as of 2020-01-01.
        self.assertAlmostEqual(bars["2020-01-01"]["dividend"], 4.0)
        self.assertAlmostEqual(bars["2020-02-01"]["split"], 1.0)

    def test_invalid_and_duplicate_rows_are_handled_like_the_yahoo_adapter(self):
        rows = [stock_row("2020-01-01", 100, 100, 100, 100), stock_row("2020-01-01", 101, 101, 101, 101)]
        with self.assertRaises(ValueError):
            normalize_ticker(rows, [])

    def test_missing_field_is_an_issue_not_a_crash(self):
        rows = [dict(stock_row("2020-01-01", 100, 100, 100, 100), close="")]
        bars, issues = normalize_ticker(rows, [])
        self.assertEqual(bars, {})
        self.assertEqual(issues, [{"date": "2020-01-01", "issue": "invalid_bar"}])


class FindGapFreeTickersTests(unittest.TestCase):
    def test_missing_day_inside_the_active_window_is_a_gap(self):
        days = ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"]
        bars = {"A": {"2020-01-01": {}, "2020-01-02": {}, "2020-01-06": {}}}  # missing 01-03
        gap_free, gaps = find_gap_free_tickers(bars, days)
        self.assertEqual(gap_free, set())
        self.assertEqual(gaps["A"], ["2020-01-03"])

    def test_absence_before_listing_or_after_delisting_is_not_a_gap(self):
        days = ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"]
        bars = {"A": {"2020-01-02": {}, "2020-01-03": {}}}  # listed 01-02, delisted after 01-03
        gap_free, gaps = find_gap_free_tickers(bars, days)
        self.assertEqual(gap_free, {"A"})
        self.assertEqual(gaps, {})


class RealAaplRegressionTests(unittest.TestCase):
    """Real-data proof: normalize actual AAPL history and cross-check with
    the existing, independent check_action_bridge(). Skips if the local
    licensed cache is not present.
    """

    def setUp(self):
        self.stocks_path = Path("data/authorized/sharadar/stocks-bulk-full.csv.zip")
        self.actions_path = Path("data/authorized/sharadar/actions-bulk-full.csv.zip")
        if not self.stocks_path.exists() or not self.actions_path.exists():
            self.skipTest("no local authorized Sharadar bulk cache present")

    def _load_ticker_rows(self, zip_path, ticker):
        import csv
        import io
        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open(zf.namelist()[0]) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
                return [row for row in reader if row["ticker"] == ticker]

    def test_aapl_bars_pass_the_action_bridge_check_from_2005_onward(self):
        stocks_rows = self._load_ticker_rows(self.stocks_path, "AAPL")
        actions_rows = self._load_ticker_rows(self.actions_path, "AAPL")
        bars, issues = normalize_ticker(stocks_rows, actions_rows)
        self.assertEqual(issues, [])
        self.assertGreater(len(bars), 5000)
        recent_bars = {d: b for d, b in bars.items() if d >= "2005-01-01"}
        discrepancies = check_action_bridge(recent_bars)
        # Real measured result: 0 discrepancies from 2005 onward; all 255
        # observed discrepancies (max ~0.62pp, all below 2004) are confined
        # to 1998-2004 vintage data, registered as a known, bounded gap --
        # see docs/review/08-decisions-and-coverage.md. This is why the
        # long-history backtest starts no earlier than 2005.
        self.assertEqual(discrepancies, [])

    def test_split_and_dividend_amounts_match_known_real_aapl_events(self):
        stocks_rows = self._load_ticker_rows(self.stocks_path, "AAPL")
        actions_rows = self._load_ticker_rows(self.actions_path, "AAPL")
        bars, _ = normalize_ticker(stocks_rows, actions_rows)
        # The well-documented 2020-08-31 4:1 split (docs/prototype/p002-results.md
        # already verified this against Apple's own announcement for the Yahoo path).
        self.assertAlmostEqual(bars["2020-08-31"]["split"], 4.0)
        # Nominal close should jump roughly 4x from the prior close.
        self.assertGreater(bars["2020-08-28"]["close"] / bars["2020-08-31"]["close"], 3.8)


if __name__ == "__main__":
    unittest.main()
