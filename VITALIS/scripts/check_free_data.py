"""Probe documented public samples; no private keys, trades, or purchases.

Run: python3 scripts/check_free_data.py
Exit 0: all probes passed. Exit 2: at least one probe is unavailable/invalid.
Passing only establishes sample access, never complete history or strategy value.
"""

import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone


PROBES = (
    ("stocks", "AAPL", ("ticker", "date", "closeadj", "closeunadj")),
    ("funds", "QQQ", ("ticker", "date", "closeadj", "closeunadj")),
    ("fundamentals", "AAPL", ("ticker", "date", "reportperiod", "dimension")),
)


def probe(table, ticker, required_fields):
    query = {
        "ticker": ticker, "from": "2025-01-01", "to": "2025-12-31",
        "limit": 3, "format": "json",
    }
    if table == "fundamentals":
        query["dimension"] = "ARQ"
    result = {
        "table": table, "ticker": ticker, "query": query,
        "source": "https://api.sharadar.com/v1.0/data/" + table,
        "credential_type": "vendor-published public test-api-key",
        "required_fields": list(required_fields),
    }
    url = result["source"] + "?" + urllib.parse.urlencode(
        dict(query, api_key="test-api-key")
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "VITALIS-research-prototype/0.1"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result["http_status"] = response.status
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError("Sample response exceeds the one-megabyte limit")
        payload = json.loads(raw)
        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not rows:
            raise ValueError("Expected a nonempty data array")
        for row in rows:
            if not isinstance(row, dict) or not set(required_fields) <= row.keys():
                raise ValueError("Sample is missing required fields")
            if row["ticker"] != ticker:
                raise ValueError("Unexpected ticker returned")
            if not query["from"] <= row["date"] <= query["to"]:
                raise ValueError("Sample date outside the requested range")
            if table == "fundamentals" and row["dimension"] != "ARQ":
                raise ValueError("Expected as-reported quarterly data")
        result.update({
            "status": "sample_access_passed", "sample_rows": len(rows),
            "sample_first_date": min(row["date"] for row in rows),
            "sample_last_date": max(row["date"] for row in rows),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
        })
    except urllib.error.HTTPError as error:
        result.update(status="http_error", http_status=error.code)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        result.update(status="transport_error", detail=str(error))
    except (ValueError, TypeError, KeyError) as error:
        result.update(status="invalid_sample", detail=str(error))
    return result


def main():
    results = [probe(*spec) for spec in PROBES]
    complete = all(row["status"] == "sample_access_passed" for row in results)
    print(json.dumps({
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "public sample access check, not a historical data audit or backtest",
        "result": "samples_accessible" if complete else "sample_access_incomplete",
        "formal_strategy_validation_ready": False,
        "probes": results,
        "remaining_requirements": [
            "QQQ total-return history access if its probe fails",
            "full requested history and corporate-action reconciliation",
            "point-in-time universe including delisted securities",
            "as-of fundamentals and realistic transaction accounting",
        ],
    }, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    sys.exit(main())
