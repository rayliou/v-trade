"""Build/reuse P005 recipient quotes from existing local bulk files only.

PYTHONPATH=. python3 scripts/prepare_p005_recipients.py
Recipient quotes support entitlements and disposal; they never expand ranking.
"""
import bisect
import csv
import io
import json
import zipfile
from pathlib import Path

from vitalis.data import download, normalize
from vitalis.local_cache import read_cache
from vitalis.research_audit import sha256_file


def main():
    root = Path('data/authorized/sharadar')
    parent = Path('runs/20260913T230115679698Z-pit-170d681b')
    output = root / 'p005-recipient-source-rows.json'
    metadata = output.with_suffix('.metadata.json')
    builder = root / 'p005-recipient-cache-builder.py'
    if output.exists() or metadata.exists():
        if not output.exists() or not metadata.exists():
            raise ValueError('Partial recipient snapshot; preserve and inspect it')
        record = json.loads(metadata.read_text())
        checks = {'source_sha256': root / 'stocks-bulk-full.csv.zip',
                  'actions_sha256': root / 'actions-bulk-full.csv.zip',
                  'parent_manifest_sha256': parent / 'manifest.json',
                  'payload_sha256': output, 'builder_sha256': builder}
        if any(sha256_file(path) != record[key] for key, path in checks.items()):
            raise ValueError('Recipient snapshot/source mismatch; do not overwrite it')
        print('Verified existing immutable P005 recipient snapshot')
        return
    manifest = json.loads((parent / 'manifest.json').read_text())
    cached = read_cache(root / 'derived-cache', manifest['derived_cache_keys']['bars'])
    known = set(cached['bars']); del cached
    bars, _ = normalize(download('QQQ', '2004-01-01', '2026-09-13', 'data/public-yahoo', offline=True))
    dates = sorted(bars)
    wanted = {}
    with zipfile.ZipFile(root / 'actions-bulk-full.csv.zip') as zf:
        reader = csv.DictReader(io.TextIOWrapper(zf.open(zf.namelist()[0])))
        for row in reader:
            if (row['ticker'] in known and row['action'] in ['spinoff', 'acquisitionstock']
                    and '2005-01-03' <= row['date'] <= '2025-12-31'):
                symbol = row['contraticker']
                index = bisect.bisect_left(dates, row['date']) + (row['action'] == 'acquisitionstock')
                wanted.setdefault(symbol, set()).update(dates[max(0, index - 2):index + 4])
    rows = {symbol: [] for symbol in wanted if symbol not in known}
    print(f'Scanning local stock zip for {len(rows)} recipient securities', flush=True)
    with zipfile.ZipFile(root / 'stocks-bulk-full.csv.zip') as zf:
        reader = csv.DictReader(io.TextIOWrapper(zf.open(zf.namelist()[0])))
        for row in reader:
            if row['ticker'] in rows and row['date'] in wanted[row['ticker']]:
                rows[row['ticker']].append(row)
    with output.open('x') as stream:
        json.dump({'requested_dates': {symbol: sorted(wanted[symbol]) for symbol in rows},
                   'rows': rows}, stream, separators=(',', ':'))
    with builder.open('xb') as stream:
        stream.write(Path(__file__).read_bytes())
    with metadata.open('x') as stream:
        json.dump({'source_sha256': sha256_file(root / 'stocks-bulk-full.csv.zip'),
                   'actions_sha256': sha256_file(root / 'actions-bulk-full.csv.zip'),
                   'parent_manifest_sha256': sha256_file(parent / 'manifest.json'),
                   'payload_sha256': sha256_file(output), 'builder_sha256': sha256_file(builder),
                   'purpose': 'P005 entitlement-only prices, never add recipient to ranking universe'}, stream, indent=2)
    print(f'Prepared {sum(map(len, rows.values()))} recipient quote rows')


if __name__ == '__main__':
    main()
