"""Checksummed local derived snapshots. No remote I/O or untrusted pickle."""

import gzip
import json
import os
from pathlib import Path

from .research_audit import sha256_file


def read_cache(cache_dir, key):
    path = Path(cache_dir) / f'{key}.json.gz'
    metadata = path.with_suffix('.metadata.json')
    if not path.exists() or not metadata.exists():
        return None
    record = json.loads(metadata.read_text())
    if record['key'] != key or sha256_file(path) != record['sha256']:
        raise ValueError('Derived cache checksum/key mismatch')
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return json.load(stream)


def write_cache(cache_dir, key, value):
    root = Path(cache_dir); root.mkdir(parents=True, exist_ok=True)
    path = root / f'{key}.json.gz'
    metadata = path.with_suffix('.metadata.json')
    if path.exists() and metadata.exists():
        read_cache(root, key)  # never silently overwrite a valid snapshot
        return
    partial = root / f'{key}.{os.getpid()}.partial'
    try:
        with gzip.open(partial, 'wt', encoding='utf-8', compresslevel=1) as stream:
            # One top-level entry at a time limits temporary serialized memory.
            stream.write('{')
            for i, (name, item) in enumerate(value.items()):
                if i:
                    stream.write(',')
                stream.write(json.dumps(name) + ':')
                stream.write(json.dumps(item, allow_nan=False, separators=(',', ':')))
            stream.write('}')
        digest = sha256_file(partial)
        # Current research CLI is a single coordinator. Shared producer leases
        # and concurrent cache publishers are deliberately not implemented here.
        partial.replace(path)
        with metadata.open('x') as stream:
            json.dump({'key': key, 'sha256': digest, 'bytes': path.stat().st_size}, stream)
    finally:
        partial.unlink(missing_ok=True)
