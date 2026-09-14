"""Point-in-time SIC (Standard Industrial Classification) history from real
Sharadar `sicchangefrom`/`sicchangeto` action pairs, self-validated against
each ticker's current classification.

This is what actually closes the gap docs/prototype/historical-data-contract.md
and vitalis/universe.py's module docstring both flag: `tickers.csv` only ever
carries a security's *current* SIC code, so vitalis/quality.py's SIC-based
peer grouping has so far only ever run against a present-day snapshot, not
the "当时可得" (known-as-of-that-time) label docs/review/03 section 2 requires.
`historical_sic()` supplies a proper as-of value; nothing in vitalis/quality.py
itself needs to change — it already just takes a plain {ticker: sic_code} dict.

Each SIC reclassification appears in the bulk `actions` table as two rows
sharing the same (ticker, date): one `sicchangefrom` (the old code) and one
`sicchangeto` (the new code). Coverage is bounded by how far back Sharadar's
own action log extends for a given ticker: a date before a ticker's earliest
recorded change uses that earliest known code as a reasonable default (a
security's original classification does not typically change until it
actually reclassifies) -- this is a stated assumption, not a proof that no
earlier, unrecorded change ever happened.
"""

import csv
import io
import zipfile


def _normalize_siccode(value):
    """The bulk `actions` table gives SIC values as floats-in-a-string
    ("5990.0"); `tickers.csv` gives them as plain integer strings ("5990").
    Comparing the two formats as raw strings always fails silently -- this
    normalizes both to the same canonical integer-string form.
    """
    if value in (None, "", "N/A"):
        return None
    return str(int(float(value)))


def load_sic_changes(actions_zip_path):
    """One streaming pass over the bulk `actions` table, pairing same-
    (ticker, date) sicchangefrom/sicchangeto rows. Returns {ticker: [(date,
    from_code, to_code), ...]}, each ticker's list sorted by date, SIC codes
    normalized via `_normalize_siccode`. A row whose pair partner is missing
    (an unpaired sicchangefrom or sicchangeto) is dropped from the chain and
    reported separately rather than silently guessed at, since a chain built
    from it would misrepresent an unknown code as a specific one.
    """
    from_by_key, to_by_key = {}, {}
    with zipfile.ZipFile(actions_zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                if row["action"] == "sicchangefrom":
                    from_by_key[(row["ticker"], row["date"])] = _normalize_siccode(row["value"])
                elif row["action"] == "sicchangeto":
                    to_by_key[(row["ticker"], row["date"])] = _normalize_siccode(row["value"])

    unpaired = sorted(set(from_by_key) ^ set(to_by_key))
    changes = {}
    for ticker, date in set(from_by_key) & set(to_by_key):
        changes.setdefault(ticker, []).append((date, from_by_key[(ticker, date)], to_by_key[(ticker, date)]))
    for ticker in changes:
        changes[ticker].sort(key=lambda change: change[0])
    return changes, unpaired


def validate_sic_chains(changes_by_ticker, current_siccode_by_ticker):
    """For every ticker with recorded changes: confirm each link's to_code
    matches the next link's from_code (no gap in the chain), and that the
    chain's final to_code matches the ticker's current SIC code from the
    security master. Returns one diagnostic record per such ticker, so a
    mismatch is visible rather than trusted -- matches this project's
    existing check_action_bridge()/validate_against_quarterly_snapshots()
    cross-check convention. A ticker absent from current_siccode_by_ticker
    (delisted, dropped from the master) is reported, not skipped.
    """
    results = []
    for ticker, ordered_changes in changes_by_ticker.items():
        gap_at = None
        for (_, _, to_code), (next_date, next_from_code, _) in zip(ordered_changes, ordered_changes[1:]):
            if to_code != next_from_code:
                gap_at = next_date
                break
        current = _normalize_siccode(current_siccode_by_ticker.get(ticker))
        final_to_code = ordered_changes[-1][2]
        results.append({
            "ticker": ticker, "changes": len(ordered_changes), "chain_gap_at": gap_at,
            "current_siccode_known": current is not None,
            "matches_current_siccode": gap_at is None and current is not None and final_to_code == current,
        })
    return results


def historical_sic(ticker, current_siccode, changes_by_ticker, asof_date):
    """The SIC code known to have applied to `ticker` as of `asof_date`,
    walking backward from `current_siccode` and undoing every recorded
    change dated strictly after `asof_date`. None if `current_siccode`
    itself is unknown (e.g. no SEP-tagged security-master row).

    `current_siccode` is normalized the same way load_sic_changes() normalizes
    the action log, so a caller passing either tickers.csv's plain-integer
    form or actions.csv's floating-point-string form gets a consistent result.
    """
    code = _normalize_siccode(current_siccode)
    if code is None:
        return None
    for date, from_code, to_code in reversed(changes_by_ticker.get(ticker, [])):
        if date <= asof_date:
            break
        code = from_code
    return code


def sic_by_ticker_asof(current_siccode_by_ticker, changes_by_ticker, asof_date):
    """historical_sic() applied across every ticker in current_siccode_by_ticker."""
    return {
        ticker: historical_sic(ticker, siccode, changes_by_ticker, asof_date)
        for ticker, siccode in current_siccode_by_ticker.items()
    }
