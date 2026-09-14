"""Independent cross-source price reconciliation: the existing Yahoo adapter
(vitalis/data.py) against real, licensed Sharadar stocks/actions data, for the
same tickers and dates. This is what resolves — with actual independent data,
not another public sample — the known_limitations item every P001 report has
carried since the first run: "Yahoo historical corporate actions and
adjustment factors not reconciled to an independent source".
"""

import math


def compare_closes(yahoo_bars, sharadar_rows_by_date, relative_tolerance=0.0005):
    """yahoo_bars: {date: {"close": nominal_close, ...}} from vitalis.data.normalize.
    sharadar_rows_by_date: {date: {"closeunadj": str, ...}} from the real
    Sharadar `stocks` bulk table, keyed by date for the same ticker.

    Mirrors vitalis.sample_audit.compare_sample()'s convention: report the
    comparable range and every discrepancy explicitly, rather than a single
    pass/fail. Dates present in only one source are listed, not silently
    dropped from the denominator.
    """
    common_dates = sorted(set(yahoo_bars) & set(sharadar_rows_by_date))
    errors, bad = [], []
    for day in common_dates:
        yahoo_close = yahoo_bars[day]["close"]
        raw = sharadar_rows_by_date[day]["closeunadj"]
        sharadar_close = float(raw) if raw not in ("", "N/A") else None
        if sharadar_close is None or sharadar_close <= 0 or not math.isfinite(sharadar_close):
            bad.append({"date": day, "issue": "invalid_sharadar_close"})
            continue
        error = abs(yahoo_close / sharadar_close - 1)
        errors.append(error)
        if error > relative_tolerance:
            bad.append({"date": day, "issue": "close_mismatch", "relative_error": error,
                       "yahoo_close": yahoo_close, "sharadar_close": sharadar_close})
    return {
        "compared_dates": len(common_dates),
        "yahoo_only_dates": sorted(set(yahoo_bars) - set(sharadar_rows_by_date)),
        "sharadar_only_dates": sorted(set(sharadar_rows_by_date) - set(yahoo_bars)),
        "max_relative_error": max(errors, default=None),
        "mean_relative_error": (sum(errors) / len(errors)) if errors else None,
        "discrepancies": bad,
    }
