"""Public macro reference series: immutable caching and forward-fill onto trading days.

Used only for account-level cash-yield accounting (what uninvested cash could actually
have earned), never as a trading signal. Because no decision depends on this series,
same-day availability lag in the vendor's own publication schedule is not a lookahead
problem the way it would be for a ranking input.
"""

import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from .data import fingerprint


def download_series(series_id, start, end, cache_dir, offline=False):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{series_id}-{start}-{end}.json"
    if target.exists():
        envelope = json.loads(target.read_text())
        if envelope["payload_sha256"] != fingerprint(envelope["payload"]):
            raise ValueError(f"Cached payload checksum failed: {series_id}")
        return envelope
    if offline:
        raise FileNotFoundError(f"Offline cache missing: {target}")
    query = urllib.parse.urlencode({"id": series_id, "cosd": start, "coed": end})
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "VITALIS-research-prototype/0.1"})
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read().decode("utf-8")
    header = f"observation_date,{series_id}"
    if not raw.startswith(header):
        raise ValueError(f"Unexpected FRED CSV header for {series_id}")
    payload = {"csv": raw}
    envelope = {
        "series_id": series_id, "url": url, "requested_start": start, "requested_end": end,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload_sha256": fingerprint(payload), "payload": payload,
    }
    # Exclusive creation prevents silently replacing a historical snapshot.
    with target.open("x") as stream:
        json.dump(envelope, stream)
    time.sleep(0.15)
    return envelope


def normalize_series(envelope):
    """Parse FRED's CSV into {date: percent}. Unpublished observations are omitted,
    not treated as zero; the caller must forward-fill onto its own trading calendar.
    """
    series_id = envelope["series_id"]
    lines = envelope["payload"]["csv"].strip("\n").split("\n")[1:]
    values = {}
    for line in lines:
        day, _, raw_value = line.partition(",")
        date.fromisoformat(day)
        if raw_value in ("", "."):
            continue
        value = float(raw_value)
        if value < 0:
            raise ValueError(f"Negative {series_id} observation: {day}")
        if day in values:
            raise ValueError(f"Duplicate {series_id} observation: {day}")
        values[day] = value
    return values


def daily_rate_by_trading_day(percent_by_date, trading_days):
    """Forward-fill a percent-per-annum series onto an explicit trading-day calendar.

    The vendor omits bond-market holidays that are still equity trading days (e.g.
    Veterans Day, the July 4th half day); the most recently published rate carries
    forward. Missing coverage before the first published observation is a hard
    error rather than an assumed rate.
    """
    known = sorted(percent_by_date)
    if not known:
        raise ValueError("No cash-yield observations available")
    if trading_days and trading_days[0] < known[0]:
        raise ValueError(f"Cash-yield series does not cover {trading_days[0]}")
    lookup, cursor, last = {}, 0, None
    for day in trading_days:
        while cursor < len(known) and known[cursor] <= day:
            last = known[cursor]
            cursor += 1
        lookup[day] = percent_by_date[last] / 100.0
    return lookup
