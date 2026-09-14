"""Credential hygiene, tier registry, quota cap, and retention-deadline logic.

No network access and no real key: download_table's HTTP path is exercised in
sample_audit.py against the public sample endpoint, not here.
"""

import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from vitalis.sharadar import (
    TABLE_TIERS, _redact_api_key, api_key, check_and_record_quota,
    check_retention, download_bulk_table, download_table,
)


class SharadarTests(unittest.TestCase):
    def test_api_key_is_read_only_from_environment(self):
        os.environ.pop("SHARADAR_API_KEY", None)
        with self.assertRaises(ValueError):
            api_key()
        os.environ["SHARADAR_API_KEY"] = "secret-value"
        try:
            self.assertEqual(api_key(), "secret-value")
        finally:
            del os.environ["SHARADAR_API_KEY"]

    def test_redact_strips_api_key_but_keeps_other_params(self):
        url = "https://api.sharadar.com/v1.0/data/tickers?api_key=secret&ticker=AAPL&limit=10"
        redacted = _redact_api_key(url)
        self.assertNotIn("secret", redacted)
        self.assertIn("ticker=AAPL", redacted)
        self.assertIn("limit=10", redacted)

    def test_unregistered_table_is_rejected_before_any_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                download_table("not_a_real_table", {}, tmp)

    def test_download_table_rejects_api_key_in_params(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                download_table("tickers", {"api_key": "x"}, tmp)

    def test_every_tiered_table_has_a_valid_tier(self):
        self.assertTrue(TABLE_TIERS)
        self.assertTrue(all(tier in ("A", "B", "C") for tier in TABLE_TIERS.values()))
        self.assertEqual(TABLE_TIERS["insiders"], "C")
        self.assertEqual(TABLE_TIERS["holdings"], "C")

    def test_quota_cap_blocks_before_the_request_and_counts_only_real_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "request-quota.json"
            path.write_text(json.dumps({"2026-09-13": 200}))
            with self.assertRaises(ValueError):
                check_and_record_quota(tmp, today="2026-09-13")
            # A different day is unaffected.
            today, used, _ = check_and_record_quota(tmp, today="2026-09-14")
            self.assertEqual(used, 0)

    def test_retention_is_none_while_subscription_is_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(check_retention({"terminated_at": None}, tmp))

    def test_retention_deadline_is_thirty_days_after_termination(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "fundamentals-abc.json").write_text("{}")
            status = {"terminated_at": "2026-01-01"}
            before = check_retention(status, tmp, today=date(2026, 1, 30))
            self.assertFalse(before["past_deadline"])
            self.assertEqual(before["must_delete_now"], [])
            after = check_retention(status, tmp, today=date(2026, 2, 1))
            self.assertTrue(after["past_deadline"])
            self.assertEqual(len(after["must_delete_now"]), 1)

    def test_bulk_rejects_unregistered_table_and_bad_years_before_any_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                download_bulk_table("not_a_real_table", "full", tmp)
            with self.assertRaises(ValueError):
                download_bulk_table("tickers", "20", tmp)

    def test_bulk_reuses_cache_when_zip_and_provenance_both_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "tickers-bulk-full.csv.zip"
            zip_path.write_bytes(b"fake-zip-bytes")
            provenance_path = Path(tmp) / "tickers-bulk-full.provenance.json"
            import hashlib
            digest = hashlib.sha256(b"fake-zip-bytes").hexdigest()
            provenance_path.write_text(json.dumps({"sha256": digest, "table": "tickers"}))
            result = download_bulk_table("tickers", "full", tmp)
            self.assertEqual(result["sha256"], digest)

    def test_retention_excludes_the_quota_ledger_from_deletion_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "request-quota.json").write_text("{}")
            result = check_retention({"terminated_at": "2020-01-01"}, tmp, today=date(2020, 6, 1))
            self.assertEqual(result["must_delete_now"], [])


if __name__ == "__main__":
    unittest.main()
