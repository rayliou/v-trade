"""Regression checks for temporal leakage, offline isolation and provenance."""

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from vitalis.data import download
from vitalis.macro import download_series
from vitalis.research_audit import (
    classify_bridge, execution_month, held_event_dates, pin_inputs,
    shift_month_end_inputs, sha256_file,
)
from vitalis.sharadar_prices import normalize_ticker


class ResearchAuditTests(unittest.TestCase):
    def test_generic_artifacts_do_not_parse_themselves_as_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run = root/'run'; run.mkdir()
            artifacts = [root/'rows.json', root/'snapshot.json.gz', root/'script.py']
            for path, content in zip(artifacts, [b'[1,2]', b'compressed bytes', b'print(1)']):
                path.write_bytes(content)
            pinned = pin_inputs(run, artifacts, root/'catalog.sqlite')
            self.assertEqual(len(pinned['source_artifacts']), 3)

    def test_derived_cache_is_idempotent_and_detects_corruption(self):
        from vitalis.local_cache import read_cache, write_cache
        with tempfile.TemporaryDirectory() as tmp:
            payload = {'bars': {'A': {'2024-01-02': {'close': 10}}}}
            write_cache(tmp, 'snapshot', payload)
            path = Path(tmp) / 'snapshot.json.gz'
            first = path.read_bytes()
            self.assertEqual(read_cache(tmp, 'snapshot'), payload)
            write_cache(tmp, 'snapshot', {'bars': 'cannot overwrite'})
            self.assertEqual(path.read_bytes(), first)
            path.write_bytes(b'truncated')
            with self.assertRaisesRegex(ValueError, 'checksum/key mismatch'):
                read_cache(tmp, 'snapshot')

    def test_month_end_is_only_available_for_next_execution_month(self):
        self.assertEqual(execution_month('2024-12-31'), '2025-01')
        inputs = {'2024-12': {'A': .2}, '2025-01': {'B': .9}}
        shifted = shift_month_end_inputs(inputs)
        self.assertEqual(shifted['2025-01'], {'A': .2})
        inputs['2025-01'] = {'FUTURE': 1}
        self.assertEqual(shift_month_end_inputs(inputs)['2025-01'], shifted['2025-01'])
        self.assertNotIn('2024-12', shifted)

    def test_offline_missing_price_and_cash_cache_never_open_network(self):
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.urlopen') as remote:
            with self.assertRaises(FileNotFoundError):
                download('QQQ', '2004-01-01', '2026-09-13', tmp, offline=True)
            with self.assertRaises(FileNotFoundError):
                download_series('DGS3MO', '2004-01-01', '2026-09-13', tmp, offline=True)
            remote.assert_not_called()

    def test_adjusted_price_times_adjusted_volume_preserves_dollar_volume(self):
        # A 4:1 split changes nominal price/quantity but not dollar turnover.
        rows = [{'date': '2020-01-02', 'open': '25', 'close': '25',
                 'closeadj': '24', 'closeunadj': '100', 'volume': '4000'}]
        bars, _ = normalize_ticker(rows, [])
        self.assertEqual(bars['2020-01-02']['dollar_volume'], 100000)
        self.assertEqual(bars['2020-01-02']['close'], 100)

    def test_snapshot_rejects_wrong_source_hash_and_registers_valid_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'stocks-bulk-full.csv.zip'
            source.write_bytes(b'local source')
            sidecar = root / 'stocks-bulk-full.provenance.json'
            sidecar.write_text(json.dumps({'sha256': 'wrong'}))
            run = root / 'run'; run.mkdir()
            with self.assertRaisesRegex(ValueError, 'Source hash mismatch'):
                pin_inputs(run, [source], root / 'catalog.sqlite')
            sidecar.write_text(json.dumps({'sha256': sha256_file(source)}))
            pinned = pin_inputs(run, [source], root / 'catalog.sqlite')
            self.assertEqual(pinned['source_artifacts'][0]['sha256'], sha256_file(source))
            with closing(sqlite3.connect(root / 'catalog.sqlite')) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM artifact').fetchone()[0], 1)
            self.assertTrue((run / 'code/research_audit.py').exists())

    def test_action_context_does_not_silently_resolve_and_prior_holdings_count(self):
        exposure = held_event_dates([{'date': '2024-01-02', 'symbol': 'A', 'quantity': 2}],
                                   ['2024-01-02', '2024-01-03'])
        issues = [{'ticker': 'A', 'date': '2024-01-03',
                   'cash_action_return': 0, 'adjusted_return': -.1}]
        actions = {'A': [{'date': '2024-01-03', 'action': 'spinoff', 'value': 'B'}]}
        result = classify_bridge(issues, actions, '2024-01-01', '2024-12-31', {'M10': exposure})
        self.assertEqual(result[0]['held_variants'], ['M10'])
        self.assertEqual(result[0]['category'], 'spinoff_context_unresolved')
        self.assertFalse(result[0]['resolved'])


if __name__ == '__main__':
    unittest.main()
