"""S&P 500 point-in-time reconstruction: synthetic logic + a real-data proof."""

import unittest
from pathlib import Path

from vitalis.universe import (
    ELIGIBLE_CATEGORIES, ELIGIBLE_EXCHANGES, group_share_classes, load_sp500_table,
    month_end_dates, monthly_universe, reconstruct_membership, trailing_average_dollar_volume,
    validate_against_quarterly_snapshots,
)


class ReconstructionTests(unittest.TestCase):
    def test_walks_forward_applying_add_and_remove_in_date_order(self):
        events = [("2020-02-01", "removed", "B"), ("2020-01-15", "added", "C"),
                  ("2020-03-01", "added", "D")]  # deliberately out of order
        result = reconstruct_membership(events, "2020-01-01", {"A", "B"}, "2020-02-15")
        self.assertEqual(result, {"A", "C"})

    def test_event_on_the_anchor_date_itself_is_excluded(self):
        # The anchor's own membership snapshot already reflects that date;
        # replaying an event dated exactly on it would double-count it.
        events = [("2020-01-01", "added", "X")]
        result = reconstruct_membership(events, "2020-01-01", {"A"}, "2020-01-02")
        self.assertEqual(result, {"A"})

    def test_event_on_the_asof_date_itself_is_included(self):
        events = [("2020-01-02", "added", "X")]
        result = reconstruct_membership(events, "2020-01-01", {"A"}, "2020-01-02")
        self.assertEqual(result, {"A", "X"})

    def test_cannot_walk_backward_from_the_anchor(self):
        with self.assertRaises(ValueError):
            reconstruct_membership([], "2020-02-01", {"A"}, "2020-01-01")

    def test_validate_reports_a_mismatch_rather_than_hiding_it(self):
        snapshots = {"2020-01-01": frozenset({"A", "B"}), "2020-04-01": frozenset({"A", "C"})}
        events = [("2020-02-01", "added", "C")]  # missing the removal of B: should mismatch
        results = validate_against_quarterly_snapshots(events, snapshots)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["matched"])
        self.assertEqual(results[0]["extra_in_reconstruction"], ["B"])
        self.assertEqual(results[0]["missing_from_reconstruction"], [])


class MonthEndDatesTests(unittest.TestCase):
    def test_keeps_the_latest_date_per_calendar_month(self):
        dates = {"2020-01-15", "2020-01-31", "2020-02-10", "2020-02-28", "2020-01-03"}
        self.assertEqual(month_end_dates(dates), ["2020-01-31", "2020-02-28"])


class TrailingAverageDollarVolumeTests(unittest.TestCase):
    def test_averages_exactly_the_trailing_window_ending_at_asof(self):
        days = ["2020-01-0" + str(i) for i in range(1, 6)]  # 5 sessions
        volumes = {d: 10.0 for d in days}
        volumes[days[-1]] = 30.0  # last day differs, should be included in a 2-day window
        result = trailing_average_dollar_volume(volumes, days, days[-1], window=2)
        self.assertAlmostEqual(result, (10.0 + 30.0) / 2)

    def test_none_when_fewer_sessions_than_the_window_exist_yet(self):
        days = ["2020-01-01", "2020-01-02"]
        volumes = {d: 10.0 for d in days}
        self.assertIsNone(trailing_average_dollar_volume(volumes, days, days[-1], window=5))

    def test_none_when_some_sessions_in_the_window_are_missing_volume(self):
        days = ["2020-01-01", "2020-01-02", "2020-01-03"]
        volumes = {"2020-01-01": 10.0, "2020-01-03": 10.0}  # 01-02 missing
        self.assertIsNone(trailing_average_dollar_volume(volumes, days, days[-1], window=3))


class GroupShareClassesTests(unittest.TestCase):
    def master(self, entries):
        return {p: {"ticker": t, "relatedtickers": rel} for p, (t, rel) in entries.items()}

    def test_related_tickers_share_a_deterministic_group_id(self):
        master = self.master({
            "1": ("BRK.A", ["BRK.B"]), "2": ("BRK.B", ["BRK.A"]), "3": ("AAPL", []),
        })
        groups = group_share_classes(master)
        self.assertEqual(groups["1"], groups["2"])
        self.assertEqual(groups["1"], "BRK.A")  # deterministic: min ticker in the group
        self.assertNotEqual(groups["3"], groups["1"])

    def test_singleton_with_no_related_tickers_is_its_own_group(self):
        master = self.master({"1": ("AAPL", [])})
        self.assertEqual(group_share_classes(master)["1"], "AAPL")


class MonthlyUniverseTests(unittest.TestCase):
    def test_full_waterfall_on_a_small_synthetic_market(self):
        from datetime import date, timedelta
        start = date(2019, 1, 1)
        trading_days = [(start + timedelta(days=i)).isoformat() for i in range(400)]  # > 252 sessions
        long_history_start = trading_days[0]
        master = {
            "1": {"ticker": "BIG", "category": "Domestic Common Stock", "exchange": "NASDAQ",
                  "firstpricedate": long_history_start, "relatedtickers": []},
            "2": {"ticker": "SMALLCAP", "category": "Domestic Common Stock", "exchange": "NYSE",
                  "firstpricedate": long_history_start, "relatedtickers": []},
            "3": {"ticker": "ILLIQUID", "category": "Domestic Common Stock", "exchange": "NASDAQ",
                  "firstpricedate": long_history_start, "relatedtickers": []},
            "4": {"ticker": "PREFERRED", "category": "Domestic Preferred Stock", "exchange": "NASDAQ",
                  "firstpricedate": long_history_start, "relatedtickers": []},
            "5": {"ticker": "NEWLISTING", "category": "Domestic Common Stock", "exchange": "NYSE",
                  "firstpricedate": trading_days[-5], "relatedtickers": []},
        }
        month_end = trading_days[-1]
        marketcap_by_ticker = {
            "BIG": {month_end: 5_000_000_000}, "SMALLCAP": {month_end: 1_000_000_000},
            "ILLIQUID": {month_end: 2_000_000_000}, "PREFERRED": {month_end: 3_000_000_000},
            "NEWLISTING": {month_end: 4_000_000_000},
        }
        dollar_volume_by_ticker = {
            "BIG": {d: 25_000_000 for d in trading_days},
            "SMALLCAP": {d: 21_000_000 for d in trading_days},
            "ILLIQUID": {d: 1_000_000 for d in trading_days},  # fails liquidity
        }
        result = monthly_universe(month_end, master, marketcap_by_ticker, dollar_volume_by_ticker,
                                  trading_days, max_issuers=200, minimum_trading_days=252,
                                  minimum_adv_usd=20_000_000, adv_window=63)
        self.assertEqual(result["selected"], ["BIG", "SMALLCAP"])
        self.assertEqual(result["waterfall"]["tickers_with_marketcap_this_month"], 5)
        # PREFERRED (category) and NEWLISTING (insufficient history) both excluded here.
        self.assertEqual(result["waterfall"]["after_category_exchange_history_filter"], 3)
        self.assertEqual(result["waterfall"]["after_liquidity_filter"], 2)
        self.assertEqual(result["waterfall"]["after_same_issuer_dedup"], 2)

    def test_max_issuers_caps_by_marketcap_without_padding_a_short_list(self):
        trading_days = [f"2020-01-{i:02}" for i in range(1, 20)]
        master = {str(i): {"ticker": f"T{i}", "category": "Domestic Common Stock", "exchange": "NYSE",
                           "firstpricedate": trading_days[0], "relatedtickers": []} for i in range(3)}
        month_end = trading_days[-1]
        marketcap_by_ticker = {f"T{i}": {month_end: 1_000_000_000 * (i + 1)} for i in range(3)}
        dollar_volume_by_ticker = {f"T{i}": {month_end: 0.0} for i in range(3)}
        result = monthly_universe(month_end, master, marketcap_by_ticker, dollar_volume_by_ticker,
                                  trading_days, max_issuers=2, minimum_trading_days=1,
                                  minimum_adv_usd=0, adv_window=1)
        self.assertEqual(len(result["selected"]), 2)
        self.assertEqual(result["selected"], ["T2", "T1"])  # highest market cap first

    def test_same_issuer_dedup_keeps_the_higher_marketcap_class(self):
        trading_days = [f"2020-01-{i:02}" for i in range(1, 20)]
        master = {
            "1": {"ticker": "DUAL.A", "category": "Domestic Common Stock Primary Class",
                  "exchange": "NYSE", "firstpricedate": trading_days[0], "relatedtickers": ["DUAL.B"]},
            "2": {"ticker": "DUAL.B", "category": "Domestic Common Stock Secondary Class",
                  "exchange": "NYSE", "firstpricedate": trading_days[0], "relatedtickers": ["DUAL.A"]},
        }
        month_end = trading_days[-1]
        marketcap_by_ticker = {"DUAL.A": {month_end: 1_000}, "DUAL.B": {month_end: 5_000}}
        dollar_volume_by_ticker = {"DUAL.A": {month_end: 0.0}, "DUAL.B": {month_end: 0.0}}
        result = monthly_universe(month_end, master, marketcap_by_ticker, dollar_volume_by_ticker,
                                  trading_days, max_issuers=200, minimum_trading_days=1,
                                  minimum_adv_usd=0, adv_window=1)
        self.assertEqual(result["selected"], ["DUAL.B"])

    def test_eligible_category_and_exchange_sets_match_the_registered_decision(self):
        self.assertIn("Domestic Common Stock", ELIGIBLE_CATEGORIES)
        self.assertNotIn("ADR Common Stock", ELIGIBLE_CATEGORIES)
        self.assertNotIn("Domestic Preferred Stock", ELIGIBLE_CATEGORIES)
        self.assertIn("NYSEMKT", ELIGIBLE_EXCHANGES)
        self.assertNotIn("NYSEARCA", ELIGIBLE_EXCHANGES)


class RealDataProofTests(unittest.TestCase):
    """Sanity-checks the module against the real, licensed Sharadar sp500 bulk
    table (data/authorized/sharadar/, git-ignored). Skips if not present.
    """

    def setUp(self):
        self.path = Path("data/authorized/sharadar/sp500-bulk-full.csv.zip")
        if not self.path.exists():
            self.skipTest("no local authorized Sharadar sp500 bulk file present")

    def test_every_quarterly_transition_reconstructs_exactly_from_events(self):
        events, snapshots = load_sp500_table(self.path)
        self.assertGreater(len(snapshots), 100)
        results = validate_against_quarterly_snapshots(events, snapshots)
        mismatches = [r for r in results if not r["matched"]]
        self.assertEqual(mismatches, [], f"{len(mismatches)}/{len(results)} quarterly transitions did not "
                         "reconstruct exactly from the added/removed event log alone")

    def test_p001_evaluation_window_membership_is_reconstructable(self):
        events, snapshots = load_sp500_table(self.path)
        anchor = max(d for d in snapshots if d <= "2021-01-04")
        members = reconstruct_membership(events, anchor, snapshots[anchor], "2021-01-04")
        # Sanity: a real large-cap constituent list, not an empty or trivial set.
        self.assertGreater(len(members), 400)
        self.assertIn("AAPL", members)


if __name__ == "__main__":
    unittest.main()
