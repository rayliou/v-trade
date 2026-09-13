"""Public sample download, immutable caching, and explicit action normalization."""

import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def download(symbol, start, end, cache_dir):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{symbol}-{start}-{end}.json"
    if target.exists():
        envelope = json.loads(target.read_text())
        if envelope["payload_sha256"] != fingerprint(envelope["payload"]):
            raise ValueError(f"Cached payload checksum failed: {symbol}")
        return envelope
    timestamp = lambda day: int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())
    query = urllib.parse.urlencode({
        "period1": timestamp(start), "period2": timestamp(end), "interval": "1d",
        "events": "div,splits", "includeAdjustedClose": "true",
    })
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=25) as response:
        payload = json.load(response)
    if payload.get("chart", {}).get("error") or not payload.get("chart", {}).get("result"):
        raise ValueError(f"Yahoo returned no valid result: {symbol}")
    envelope = {
        "symbol": symbol, "url": url, "requested_start": start, "requested_end_exclusive": end,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload_sha256": fingerprint(payload), "payload": payload,
    }
    # Exclusive creation prevents silently replacing a historical snapshot.
    with target.open("x") as stream:
        json.dump(envelope, stream)
    time.sleep(0.15)
    return envelope


def normalize(envelope):
    result = envelope["payload"]["chart"]["result"][0]
    if result["meta"]["currency"] != "USD":
        raise ValueError(f"Non-USD instrument: {envelope['symbol']}")
    market_zone = ZoneInfo("America/New_York")
    day_of = lambda stamp: datetime.fromtimestamp(int(stamp), market_zone).date().isoformat()
    events = result.get("events", {})
    if events.get("capitalGains"):
        raise ValueError("Capital gain distributions need a dedicated adapter")
    splits = {}
    for event in events.get("splits", {}).values():
        ratio = float(event["numerator"]) / float(event["denominator"])
        if not math.isfinite(ratio) or ratio <= 0:
            raise ValueError("Invalid split ratio")
        splits[day_of(event["date"])] = ratio
    dividends = {day_of(e["date"]): float(e["amount"])
                 for e in events.get("dividends", {}).values()}
    quote = result["indicators"]["quote"][0]
    adjusted = result["indicators"]["adjclose"][0]["adjclose"]
    bars, issues = {}, []
    for i, stamp in enumerate(result["timestamp"]):
        day = day_of(stamp)
        date.fromisoformat(day)
        values = [quote[k][i] for k in ("open", "close", "volume")] + [adjusted[i]]
        if any(v is None or not math.isfinite(float(v)) for v in values):
            issues.append({"symbol": envelope["symbol"], "date": day, "issue": "invalid_bar"})
            continue
        opening, closing, volume, adjclose = map(float, values)
        if min(opening, closing, adjclose) <= 0 or volume < 0:
            raise ValueError(f"Invalid price/volume: {envelope['symbol']} {day}")
        # Yahoo OHLC/dividends are in split-adjusted units. Reconstruct nominal
        # historical units using ALL split events through the snapshot cutoff.
        future_split_factor = math.prod(r for d, r in splits.items() if d > day)
        if day in bars:
            raise ValueError(f"Duplicate daily bar: {day}")
        bars[day] = {
            "open": opening * future_split_factor,
            "close": closing * future_split_factor,
            "adjclose": adjclose,
            "dollar_volume": closing * volume,
            "split": splits.get(day, 1.0),
            "dividend": dividends.get(day, 0.0) * future_split_factor,
        }
    return bars, issues


def check_action_bridge(bars):
    """Detect large inconsistencies between nominal cash wealth and adjclose.

    Not independent source verification. Dividend reinvestment conventions may
    differ slightly; discrepancies above 0.2 percentage points are flagged.
    """
    issues = []
    dates = sorted(bars)
    for previous, current in zip(dates, dates[1:]):
        a, b = bars[previous], bars[current]
        cash_return = (b["close"] + b["dividend"]) * b["split"] / a["close"] - 1
        adjusted_return = b["adjclose"] / a["adjclose"] - 1
        if abs(cash_return - adjusted_return) > 0.002:
            issues.append({"date": current, "cash_action_return": cash_return,
                           "adjusted_return": adjusted_return})
    return issues
