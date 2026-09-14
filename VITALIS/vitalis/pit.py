"""Conservative financial availability; this does not certify vendor PIT history."""

from bisect import bisect_right
from datetime import date
import math


def normalize_fundamentals(rows, sessions):
    """Expose AR observations only after the next trading session has closed.

    Dates represent end-of-day research cutoffs. With no filing time or actual
    historical delivery time, delay one whole session strictly after filing.
    Report period and download/update date must never substitute for filing date.
    Security identity remains the vendor ticker until a stable mapping is supplied.
    """
    if sessions != sorted(set(sessions)):
        raise ValueError("Sessions must be unique and sorted")
    output, keys = [], set()
    for row in rows:
        if row["dimension"] not in ("ARQ", "ARY", "ART"):
            raise ValueError("Restated MR observations are not accepted as PIT inputs")
        filing, period = row["date"], row["reportperiod"]
        date.fromisoformat(filing)
        date.fromisoformat(period)
        if period > filing or not sessions or filing < sessions[0]:
            raise ValueError("Invalid period or insufficient availability calendar")
        key = (row["ticker"], row["dimension"], filing, period)
        if key in keys:
            raise ValueError("Duplicate financial observation; resolve revisions explicitly")
        keys.add(key)
        index = bisect_right(sessions, filing)
        if index == len(sessions):
            raise ValueError("Calendar must extend beyond the latest filing")
        normalized = dict(row, available_on_close=sessions[index], filing_date=filing)
        for field in ("roic", "roa", "ncfo", "netinc", "assets", "de",
                     "opinc", "revenue", "assetsavg", "debt"):
            value = row.get(field)
            if value in (None, "", "N/A"):
                normalized[field] = None
            else:
                normalized[field] = float(value)
                if not math.isfinite(normalized[field]):
                    raise ValueError(f"Nonfinite fundamental: {field}")
        output.append(normalized)
    return output


def fundamentals_asof(rows, cutoff, dimension="ART"):
    """Return the newest known reporting period, then its latest known filing."""
    date.fromisoformat(cutoff)
    selected = {}
    for row in rows:
        if row["dimension"] != dimension or row["available_on_close"] > cutoff:
            continue
        ticker = row["ticker"]
        key = (row["reportperiod"], row["filing_date"])
        if ticker not in selected or key > (
            selected[ticker]["reportperiod"], selected[ticker]["filing_date"]
        ):
            selected[ticker] = row
    return selected
