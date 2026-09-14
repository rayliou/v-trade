"""Point-in-time SIC reconstruction: synthetic logic + a real-data proof."""

import unittest
from pathlib import Path

from vitalis.sic_history import (
    historical_sic, load_sic_changes, sic_by_ticker_asof, validate_sic_chains,
)
from vitalis.universe import security_master


class HistoricalSicTests(unittest.TestCase):
    def test_walks_backward_through_multiple_recorded_changes(self):
        changes = {"X": [("2020-01-01", "1000", "2000"), ("2021-01-01", "2000", "3000")]}
        self.assertEqual(historical_sic("X", "3000", changes, "2019-06-01"), "1000")
        self.assertEqual(historical_sic("X", "3000", changes, "2020-06-01"), "2000")
        self.assertEqual(historical_sic("X", "3000", changes, "2021-06-01"), "3000")

    def test_change_dated_exactly_on_asof_is_already_in_effect(self):
        changes = {"X": [("2020-01-01", "1000", "2000")]}
        self.assertEqual(historical_sic("X", "2000", changes, "2020-01-01"), "2000")

    def test_date_before_earliest_change_uses_the_earliest_known_code(self):
        changes = {"X": [("2020-01-01", "1000", "2000")]}
        self.assertEqual(historical_sic("X", "2000", changes, "1999-01-01"), "1000")

    def test_ticker_with_no_recorded_changes_returns_current_code_unconditionally(self):
        self.assertEqual(historical_sic("Y", "9999", {}, "1990-01-01"), "9999")

    def test_unknown_current_siccode_returns_none_rather_than_guessing(self):
        self.assertIsNone(historical_sic("Z", None, {}, "2020-01-01"))

    def test_sic_by_ticker_asof_applies_across_every_ticker(self):
        changes = {"X": [("2020-06-01", "1000", "2000")]}
        current = {"X": "2000", "Y": "5000"}
        result = sic_by_ticker_asof(current, changes, "2020-01-01")
        self.assertEqual(result, {"X": "1000", "Y": "5000"})


class ValidateSicChainsTests(unittest.TestCase):
    def test_clean_chain_matches_current_siccode(self):
        changes = {"X": [("2020-01-01", "1000", "2000"), ("2021-01-01", "2000", "3000")]}
        result = validate_sic_chains(changes, {"X": "3000"})
        self.assertEqual(result, [{"ticker": "X", "changes": 2, "chain_gap_at": None,
                                   "current_siccode_known": True, "matches_current_siccode": True}])

    def test_gap_between_consecutive_links_is_reported(self):
        # 2021 link starts from "9999", not the prior link's "2000" -- a break.
        changes = {"X": [("2020-01-01", "1000", "2000"), ("2021-01-01", "9999", "3000")]}
        result = validate_sic_chains(changes, {"X": "3000"})
        self.assertEqual(result[0]["chain_gap_at"], "2021-01-01")
        self.assertFalse(result[0]["matches_current_siccode"])

    def test_chain_final_code_disagreeing_with_master_is_reported_not_hidden(self):
        changes = {"X": [("2020-01-01", "1000", "2000")]}
        result = validate_sic_chains(changes, {"X": "9999"})  # master disagrees with the chain
        self.assertFalse(result[0]["matches_current_siccode"])

    def test_ticker_missing_from_security_master_is_reported(self):
        changes = {"X": [("2020-01-01", "1000", "2000")]}
        result = validate_sic_chains(changes, {})
        self.assertFalse(result[0]["current_siccode_known"])
        self.assertFalse(result[0]["matches_current_siccode"])


class LoadSicChangesUnpairedTests(unittest.TestCase):
    def test_unpaired_from_or_to_rows_are_excluded_and_reported_separately(self):
        # Exercised against the real bulk file in RealDataProofTests below;
        # here we only check the function's contract shape via a tiny fixture
        # written to a real temporary zip, since load_sic_changes reads a zip.
        import csv
        import io
        import tempfile
        import zipfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "actions.csv.zip"
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["date", "action", "ticker", "name", "value", "contraticker", "contraname"])
            writer.writerow(["2020-01-01", "sicchangefrom", "X", "X CORP", "1000", "N/A", "N/A"])
            writer.writerow(["2020-01-01", "sicchangeto", "X", "X CORP", "2000", "N/A", "N/A"])
            writer.writerow(["2020-02-01", "sicchangefrom", "Y", "Y CORP", "3000", "N/A", "N/A"])
            # Y's sicchangeto row is deliberately missing -> unpaired.
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("actions.csv", buffer.getvalue())
            changes, unpaired = load_sic_changes(path)
            self.assertEqual(changes, {"X": [("2020-01-01", "1000", "2000")]})
            self.assertEqual(unpaired, [("Y", "2020-02-01")])


class RealDataProofTests(unittest.TestCase):
    """Cross-checks every ticker's real SIC-change chain against its real
    current classification. Skips if the local licensed cache is absent.
    """

    def setUp(self):
        self.actions_path = Path("data/authorized/sharadar/actions-bulk-full.csv.zip")
        self.tickers_path = Path("data/authorized/sharadar/tickers-bulk-full.csv.zip")
        if not self.actions_path.exists() or not self.tickers_path.exists():
            self.skipTest("no local authorized Sharadar bulk cache present")

    def test_recorded_sic_chains_mostly_reconcile_with_current_classification(self):
        master = security_master(self.tickers_path)
        current_siccode = {info["ticker"]: info["siccode"] for info in master.values()}
        changes, unpaired = load_sic_changes(self.actions_path)
        self.assertGreater(len(changes), 100, "expected a substantial number of tickers with recorded SIC history")
        results = validate_sic_chains(changes, current_siccode)
        matched = sum(1 for r in results if r["matches_current_siccode"])
        match_rate = matched / len(results)
        # Not 100%: some tickers' chains cover a ticker that has since been
        # reused, delisted, or renamed since the change log entry, which the
        # security master (a current snapshot) cannot always resolve back to.
        # This is registered, not silently expected to be perfect.
        # Real measured rate is 98.2% (2525/2572 as of 2026-09-13); bound left
        # with margin below that so a real regression still trips this test
        # without being brittle to the vendor's log growing over time.
        self.assertGreater(match_rate, 0.95, f"only {match_rate:.1%} of {len(results)} SIC chains matched")

    def test_p001_universe_has_reconstructable_historical_sic(self):
        import json
        master = security_master(self.tickers_path)
        current_siccode = {info["ticker"]: info["siccode"] for info in master.values()}
        changes, _ = load_sic_changes(self.actions_path)
        with open("config/prototype-v1.json") as stream:
            symbols = list(json.load(stream)["symbols"])
        sic_2021 = sic_by_ticker_asof(current_siccode, changes, "2021-01-04")
        for symbol in symbols:
            self.assertIn(symbol, sic_2021)
            self.assertIsNotNone(sic_2021[symbol], f"{symbol} has no resolvable SIC as of 2021-01-04")


if __name__ == "__main__":
    unittest.main()
