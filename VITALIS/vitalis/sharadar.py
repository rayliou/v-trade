"""Authenticated Sharadar REST access under a Personal Use License.

Same endpoint the free public sample in sample_audit.py already exercises
(https://api.sharadar.com/v1.0/data/{table}), but with a real account key that
unlocks full entitlement instead of the vendor's 3-row public example.

License facts, independently fetched from https://sharadar.com/terms on
2026-09-13 (docs/review/07-evidence-register.md E10):
  - No commercial, professional, institutional, or organizational use, including
    "technology development for a business" — personal research/trading only.
  - Within 30 days of subscription termination, the license text calls for
    deleting every copy of Services Data (downloads, bulk files, caches,
    extracts, and any dataset that could reconstruct a Sharadar table) from
    every machine, keeping only research outputs, backtests, models, summary
    statistics, and trade logs that do not reconstruct the raw tables.
  - A 2026-08-07 pause/resume feature exists, but the vendor's post does not say
    whether raw-data retention during a pause is exempt from that clause (E17).

`check_retention()` below reports what that clause implies for a given
termination date; it does not delete anything and nothing in this module calls
it automatically. For this project's personal-use subscription, the user has
chosen to retain the downloaded data indefinitely regardless of subscription
status — record that decision here rather than pretending the code enforces
a policy it no longer does.

The API key is read ONLY from the SHARADAR_API_KEY environment variable. It must
never be passed as a CLI argument, written into config, or embedded in a cached
envelope, manifest, or log — every persisted URL has api_key stripped before it
touches disk (see data-source-onboarding.md: "签名URL、API key不写日志").
"""

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .data import fingerprint

BASE_URL = "https://api.sharadar.com/v1.0/data/"

# 2026-09-13 purchase-strategy decision (docs/review/08-decisions-and-coverage.md):
# Tier A feeds the ranking/portfolio engine once ingested, mapped, and validated.
# Tier B is downloaded and kept for validation/Phase-1.5 research but must not
# reach factor_snapshot/ranking until a dedicated look-ahead review clears it.
# Tier C is isolated entirely for now: 13F-derived holdings tables carry a public
# disclosure lag (institutions can report a quarter-end position ~45 days later)
# and must never be visible to the engine as of a date before it was actually
# public — mixing that in without an explicit availability model is a textbook
# look-ahead bias, not merely an unfinished feature.
TABLE_TIERS = {
    "tickers": "A", "fundamentals": "A", "daily": "A", "actions": "A",
    "stocks": "A", "sp500": "A", "descriptions": "A",
    "events": "B", "funds": "B", "metrics": "B",
    "insiders": "C", "holdings": "C", "holdings_ticker": "C", "holdings_investor": "C",
}

PROJECT_REQUESTS_PER_DAY_CAP = 200  # config/data-source-policy.json self-imposed cap
PROJECT_MIN_SECONDS_BETWEEN_REQUESTS = 1.0


def api_key():
    key = os.environ.get("SHARADAR_API_KEY")
    if not key:
        raise ValueError(
            "Set SHARADAR_API_KEY in the environment before calling download_table(); "
            "never pass the key as a CLI argument, config value, or file contents.")
    return key


def _redact_api_key(url):
    parsed = urllib.parse.urlsplit(url)
    kept = [(k, v) for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True) if k != "api_key"]
    return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(kept)))


def _quota_path(cache_dir):
    return Path(cache_dir) / "request-quota.json"


def check_and_record_quota(cache_dir, today=None):
    """Enforce the project's self-imposed 200-requests/UTC-day cap (not an
    official vendor limit — the getting-started/FAQ pages did not publish one).
    Raises before the request would be made; only records after a real call.
    """
    today = today or datetime.now(timezone.utc).date().isoformat()
    path = _quota_path(cache_dir)
    state = json.loads(path.read_text()) if path.exists() else {}
    used = state.get(today, 0)
    if used >= PROJECT_REQUESTS_PER_DAY_CAP:
        raise ValueError(f"Project daily Sharadar request cap reached ({PROJECT_REQUESTS_PER_DAY_CAP}) for {today}")
    return today, used, path


def _record_quota(path, today, used):
    state = json.loads(path.read_text()) if path.exists() else {}
    state[today] = used + 1
    path.write_text(json.dumps(state, indent=2))


def download_table(table, params, cache_dir):
    """One authenticated, immutably cached request. `params` must not carry api_key.

    Caching is keyed by (table, params), so identical requests never re-spend
    quota; different limit/skip pages are distinct cache entries, matching the
    project's existing "满page继续分页,不作为完成标志" pagination discipline.
    """
    if table not in TABLE_TIERS:
        raise ValueError(f"Unregistered table (add it to TABLE_TIERS with a tier decision first): {table}")
    if "api_key" in params:
        raise ValueError("Pass params without api_key; it is attached only for the live request, never cached")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    request_key = fingerprint({"table": table, "params": params})
    target = cache_dir / f"{table}-{request_key[:16]}.json"
    if target.exists():
        envelope = json.loads(target.read_text())
        if envelope["payload_sha256"] != fingerprint(envelope["payload"]):
            raise ValueError(f"Cached payload checksum failed: {table}")
        return envelope
    today, used, quota_path = check_and_record_quota(cache_dir)
    query = dict(params, api_key=api_key(), format="json")
    url = BASE_URL + table + "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(url, headers={"User-Agent": "VITALIS-research-prototype/0.3"})
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)
    envelope = {
        "table": table, "tier": TABLE_TIERS[table], "url": _redact_api_key(url), "params": params,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload_sha256": fingerprint(payload), "payload": payload,
    }
    # Exclusive creation prevents silently replacing a historical snapshot.
    with target.open("x") as stream:
        json.dump(envelope, stream)
    _record_quota(quota_path, today, used)
    time.sleep(PROJECT_MIN_SECONDS_BETWEEN_REQUESTS)
    return envelope


def download_bulk_table(table, years, cache_dir):
    """Whole-table zip export (https://sharadar.com/docs/bulk): the same REST
    endpoint as download_table, but with years=5/10/full instead of row
    filters, redirecting to a time-limited signed download URL for a zipped
    CSV. This is the vendor-recommended path for a complete table — one
    request per table instead of one per ticker.

    Saved as a raw binary file plus a JSON provenance sidecar (a multi-hundred
    MB payload does not fit the small-JSON envelope download_table uses).
    Streamed to a .partial file and hashed while writing, then atomically
    renamed into place only after the full download succeeds, so an
    interrupted transfer can never be mistaken for a complete, checksummed
    snapshot (see docs/prototype/local-data-architecture.md: "文件先临时写入、
    校验后原子发布"). The redirected signed URL itself is never persisted.
    """
    if table not in TABLE_TIERS:
        raise ValueError(f"Unregistered table (add it to TABLE_TIERS with a tier decision first): {table}")
    if years not in ("5", "10", "full"):
        raise ValueError("years must be '5', '10', or 'full'")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    zip_path = cache_dir / f"{table}-bulk-{years}.csv.zip"
    provenance_path = cache_dir / f"{table}-bulk-{years}.provenance.json"
    if zip_path.exists() and provenance_path.exists():
        provenance = json.loads(provenance_path.read_text())
        if provenance["sha256"] != hashlib.sha256(zip_path.read_bytes()).hexdigest():
            raise ValueError(f"Cached bulk file checksum failed: {table}")
        return provenance
    today, used, quota_path = check_and_record_quota(cache_dir)
    url = BASE_URL + table + "?" + urllib.parse.urlencode({"api_key": api_key(), "years": years})
    request = urllib.request.Request(url, headers={"User-Agent": "VITALIS-research-prototype/0.3"})
    partial_path = zip_path.with_suffix(zip_path.suffix + ".partial")
    hasher = hashlib.sha256()
    with urllib.request.urlopen(request, timeout=300) as response, partial_path.open("wb") as stream:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            stream.write(chunk)
            hasher.update(chunk)
    size = partial_path.stat().st_size
    partial_path.rename(zip_path)
    provenance = {
        "table": table, "tier": TABLE_TIERS[table], "years": years,
        "requested_url": _redact_api_key(url),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "bytes": size, "sha256": hasher.hexdigest(),
    }
    provenance_path.write_text(json.dumps(provenance, indent=2))
    _record_quota(quota_path, today, used)
    time.sleep(PROJECT_MIN_SECONDS_BETWEEN_REQUESTS)
    return provenance


def check_retention(status, cache_dir, today=None):
    """Informational only: reports what the license's post-termination deletion
    clause (E10 term 10) would imply, given a recorded termination/pause date.
    Deletes nothing, and nothing in this module calls it automatically — this
    project's subscription is being retained indefinitely by user choice (see
    module docstring). Kept for whoever later needs the actual deadline math.

    status: {"terminated_at": "YYYY-MM-DD"} once recorded, else {"terminated_at": None}.
    Returns None while active (no deletion clock running); otherwise the
    30-day deadline and whether every cached file under cache_dir is past it.
    """
    terminated_at = status.get("terminated_at")
    if not terminated_at:
        return None
    today = today or date.today()
    deadline = date.fromisoformat(terminated_at) + timedelta(days=30)
    files = [str(p) for p in Path(cache_dir).rglob("*") if p.is_file() and p.name != "request-quota.json"]
    return {"deadline": deadline.isoformat(), "past_deadline": today > deadline,
            "must_delete_now": files if today > deadline else []}
