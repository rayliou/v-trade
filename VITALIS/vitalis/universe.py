"""Point-in-time historical universe construction from real Sharadar bulk
tables: S&P 500 membership (cross-validated against the vendor's own quarterly
snapshots), a security master, and the docs/review/03 section 1 market-cap and
liquidity eligibility screen. Together these are a candidate implementation of
docs/prototype/historical-data-contract.md's `universe_evidence.csv` and
`securities.csv`, not a finished one — see each function's docstring for what
it does and does not establish, and docs/review/08-decisions-and-coverage.md
for the registered decision on whether/when this replaces P001's 30-name
survivor sample.

## S&P 500 membership

The sp500 table has three kinds of rows: `historical` (quarterly snapshots,
1998-03-31 onward, one row per constituent), `added`/`removed` (individual
point-in-time transition events, 1957 onward, each carrying a reason), and
`current` (today's snapshot). The `added` events do not fully cover the
original 1957 constituent list, so this module never reconstructs backward
past the earliest reliable anchor; it only walks forward from a known
snapshot using the event log, and separately proves that walk against every
subsequent quarterly snapshot the vendor publishes. This is a candidate
historical universe for cross-checking VITALIS's broader target universe
(docs/review/03: 100-200 large, liquid names), matching docs/review/04
candidate C0/C1 design ("Experiment A: only within contemporary S&P 500
membership") — it is not a claim that VITALIS should invest only in the S&P 500.

## Security master and eligibility

The bulk `tickers` table tags each row with the old Nasdaq Data Link table
code it came from: `SEP` (equity price coverage — the row carrying
exchange/isdelisted/category/first-last price date), `SF1` (fundamentals),
`SF2` (insiders), `SF3B` (institutional holdings), `SFP` (funds). Only `SEP`
rows describe tradable equity and are used to build the security master.

The eligibility screen only has each security's *current* exchange and
category, not a historical listing-venue history — a security that changed
exchanges is filtered by where it trades today, not where it traded on the
eligibility date. This is a known, explicitly accepted gap (see docs/review/03:
"当时有效上市"), not a silent one.
"""

import bisect
import csv
import io
import zipfile
from datetime import date


def load_sp500_table(zip_path):
    """Returns (events, quarterly_snapshots).
    events: sorted list of (date, action, ticker) for action in ("added", "removed").
    quarterly_snapshots: {date: frozenset(tickers)} from action == "historical" rows.
    """
    events, snapshots = [], {}
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                date.fromisoformat(row["date"])
                if row["action"] in ("added", "removed"):
                    events.append((row["date"], row["action"], row["ticker"]))
                elif row["action"] == "historical":
                    snapshots.setdefault(row["date"], set()).add(row["ticker"])
    events.sort(key=lambda e: e[0])
    return events, {d: frozenset(t) for d, t in snapshots.items()}


def reconstruct_membership(events, anchor_date, anchor_members, asof_date):
    """Walk (anchor_date, asof_date] applying add/remove toggles from `events`,
    starting from `anchor_members`. Forward-only: asof_date must not precede
    anchor_date, because the added-event log does not reliably cover removals
    that happened before the earliest event it records.
    """
    if asof_date < anchor_date:
        raise ValueError("reconstruct_membership only walks forward from a known anchor")
    members = set(anchor_members)
    for event_date, action, ticker in events:
        if event_date <= anchor_date or event_date > asof_date:
            continue
        if action == "added":
            members.add(ticker)
        elif action == "removed":
            members.discard(ticker)
    return members


def validate_against_quarterly_snapshots(events, quarterly_snapshots):
    """Walk forward from each vendor quarterly snapshot to the next using only
    the event log, and check it lands on exactly what the vendor's own next
    snapshot says. Returns one record per consecutive quarter pair so any
    mismatch is visible rather than silently trusted — matches this project's
    existing check_action_bridge()/compare_sample() cross-check pattern.
    """
    ordered_dates = sorted(quarterly_snapshots)
    results = []
    for previous, current in zip(ordered_dates, ordered_dates[1:]):
        reconstructed = reconstruct_membership(events, previous, quarterly_snapshots[previous], current)
        actual = quarterly_snapshots[current]
        results.append({
            "from": previous, "to": current, "matched": reconstructed == actual,
            "extra_in_reconstruction": sorted(reconstructed - actual),
            "missing_from_reconstruction": sorted(actual - reconstructed),
        })
    return results


# --- Security master -------------------------------------------------------

ELIGIBLE_CATEGORIES = {
    "Domestic Common Stock", "Domestic Common Stock Primary Class", "Domestic Common Stock Secondary Class",
}
ELIGIBLE_EXCHANGES = {"NASDAQ", "NYSE", "NYSEMKT"}  # NYSEMKT = NYSE American


def security_master(tickers_zip_path):
    """One row per permaticker, from the `SEP` (equity price coverage) tag
    only — the tag carrying exchange/isdelisted/category/first-last price
    date. A permaticker with no `SEP` row has no tradable price history
    (only fundamentals/insiders/holdings/funds coverage) and is excluded.
    """
    result = {}
    with zipfile.ZipFile(tickers_zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                if row["table"] != "SEP":
                    continue
                permaticker = row["permaticker"]
                if permaticker in result:
                    raise ValueError(f"Duplicate SEP row for permaticker {permaticker}")
                result[permaticker] = {
                    "permaticker": permaticker, "ticker": row["ticker"], "name": row["name"],
                    "exchange": row["exchange"], "isdelisted": row["isdelisted"] == "Y",
                    "category": row["category"], "currency": row["currency"],
                    "siccode": row["siccode"] or None, "sector": row["sector"] or None,
                    "firstpricedate": row["firstpricedate"] or None,
                    "lastpricedate": row["lastpricedate"] or None,
                    "relatedtickers": row["relatedtickers"].split() if row["relatedtickers"] else [],
                }
    return result


# --- Trading calendar and bulk-table streaming loaders ----------------------

def distinct_trading_days(csv_zip_path, date_field="date"):
    """One streaming pass collecting every distinct date string in a bulk
    table. Used both as a trading calendar and to derive month-end dates.
    """
    days = set()
    with zipfile.ZipFile(csv_zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                days.add(row[date_field])
    return days


def month_end_dates(distinct_dates):
    """The latest observed trading date in each calendar month present in
    `distinct_dates` — an empirical month-end, not an assumed exchange holiday
    calendar.
    """
    by_month = {}
    for day in distinct_dates:
        key = day[:7]
        if key not in by_month or day > by_month[key]:
            by_month[key] = day
    return sorted(by_month.values())


def load_marketcap_snapshots(daily_zip_path, target_dates):
    """One streaming pass over the (large) `daily` bulk table, keeping only
    rows whose date is in `target_dates` (e.g. the month-end dates). Returns
    {ticker: {date: marketcap}}. Non-positive/missing market cap is dropped,
    not treated as zero.
    """
    target = set(target_dates)
    result = {}
    with zipfile.ZipFile(daily_zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                if row["date"] not in target:
                    continue
                raw_value = row["marketcap"]
                if raw_value in ("", "N/A"):
                    continue
                value = float(raw_value)
                if value <= 0:
                    continue
                result.setdefault(row["ticker"], {})[row["date"]] = value
    return result


def load_dollar_volume(stocks_zip_path, tickers, start_date, end_date):
    """One streaming pass over the (large) `stocks` bulk table, keeping only
    rows for `tickers` within [start_date, end_date]. Returns
    {ticker: {date: dollar_volume}}.

    Both `close` and `volume` in this table are split-adjusted, so dollar
    volume must pair them with each other. Pairing the *nominal* `closeunadj`
    with split-adjusted volume (as this did before) overstates a pre-split
    session by exactly that name's future split factor -- measured at 4.00x
    on AAPL's 2020-08-03 session against its later 4:1 split. That is worse
    than a units bug: the size of the error is a function of a future event,
    so it systematically inflates the apparent liquidity of names that went on
    to split, biasing any screen built on it. Same defect class as the one
    fixed in vitalis.sharadar_prices during P004 (registered there as E-ADV);
    this second code path was missed then because run_pit.py derives dollar
    volume from the already-corrected bars instead of calling this.
    """
    wanted = set(tickers)
    result = {}
    with zipfile.ZipFile(stocks_zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                if row["ticker"] not in wanted or not (start_date <= row["date"] <= end_date):
                    continue
                close, volume = row["close"], row["volume"]
                if close in ("", "N/A") or volume in ("", "N/A"):
                    continue
                closing, shares = float(close), float(volume)
                if closing <= 0 or shares < 0:
                    continue
                result.setdefault(row["ticker"], {})[row["date"]] = closing * shares
    return result


def trailing_average_dollar_volume(dollar_volume_by_date, trading_days_sorted, asof_date, window):
    """Mean dollar volume over the `window` trading sessions ending at or
    before `asof_date`, using only `trading_days_sorted` (the real calendar,
    not a naive N-calendar-day lookback). Returns None if fewer than `window`
    sessions of history exist yet, rather than a lookback into data that
    predates the security's own listing.

    Locates the window with a binary search (`trading_days_sorted` is sorted
    ascending) rather than rescanning the whole calendar per call. Same
    result as the earlier linear-scan version, just not O(len(trading_days))
    per call -- that only mattered for candidate-scale (hundreds of tickers)
    but made a whole-market screen (P006's tens of thousands) impractically
    slow: a full-history rescan on every one of ~17,000 tickers x 259 months
    x 2 windows.
    """
    position = bisect.bisect_right(trading_days_sorted, asof_date)
    if position < window:
        return None
    recent_days = trading_days_sorted[position - window:position]
    values = [dollar_volume_by_date[d] for d in recent_days if d in dollar_volume_by_date]
    if len(values) < window:
        return None
    return sum(values) / len(values)


# --- Monthly point-in-time universe -----------------------------------------

def group_share_classes(master):
    """Groups permatickers that are share classes of the same issuer, using
    the `relatedtickers` field. Returns {permaticker: group_id} where
    group_id is the smallest ticker string in the group (deterministic).
    A permaticker with no related tickers is its own singleton group.
    """
    ticker_to_permaticker = {info["ticker"]: p for p, info in master.items()}
    group_of = {}
    for permaticker, info in master.items():
        if permaticker in group_of:
            continue
        related_permatickers = [ticker_to_permaticker[t] for t in info["relatedtickers"]
                                if t in ticker_to_permaticker]
        group_members = {permaticker, *related_permatickers}
        group_id = min(master[p]["ticker"] for p in group_members)
        for member in group_members:
            group_of[member] = group_id
    return group_of


def monthly_universe(month_end, master, marketcap_by_ticker, dollar_volume_by_ticker,
                     trading_days_sorted, max_issuers=200, minimum_trading_days=252,
                     minimum_adv_usd=20_000_000, adv_window=63):
    """docs/review/03 section 1's eligibility screen for one month-end date.

    Returns {"month_end", "selected": [ticker,...], "waterfall": {...}} where
    `waterfall` is the count surviving each filter stage in order, so a
    smaller-than-expected result is explainable rather than a bare number —
    matching docs/review/05's "覆盖率应同时报分母" requirement. `selected`
    is capped at `max_issuers` by market cap but is never padded to reach it;
    a month with fewer qualifying names reports its true count.

    A ticker known to have delisted (`isdelisted`) is not excluded solely for
    that reason — its `lastpricedate` and the month-end date jointly gate it
    naturally (its market cap/volume data simply won't extend past that date).
    """
    waterfall = {"tickers_with_marketcap_this_month": 0}
    candidates = {}
    for info in master.values():
        ticker = info["ticker"]
        if ticker not in marketcap_by_ticker or month_end not in marketcap_by_ticker[ticker]:
            continue
        waterfall["tickers_with_marketcap_this_month"] += 1
        if info["category"] not in ELIGIBLE_CATEGORIES:
            continue
        if info["exchange"] not in ELIGIBLE_EXCHANGES:
            continue
        if not info["firstpricedate"] or info["firstpricedate"] > month_end:
            continue
        history = [d for d in trading_days_sorted if info["firstpricedate"] <= d <= month_end]
        if len(history) < minimum_trading_days:
            continue
        candidates[ticker] = marketcap_by_ticker[ticker][month_end]
    waterfall["after_category_exchange_history_filter"] = len(candidates)

    liquid = {}
    for ticker, marketcap in candidates.items():
        adv = trailing_average_dollar_volume(dollar_volume_by_ticker.get(ticker, {}),
                                             trading_days_sorted, month_end, adv_window)
        if adv is not None and adv >= minimum_adv_usd:
            liquid[ticker] = marketcap
    waterfall["after_liquidity_filter"] = len(liquid)

    ticker_to_permaticker = {info["ticker"]: p for p, info in master.items()}
    group_of = group_share_classes(master)
    best_in_group = {}
    for ticker, marketcap in liquid.items():
        group = group_of.get(ticker_to_permaticker[ticker], ticker)
        current_best = best_in_group.get(group)
        if current_best is None or marketcap > liquid[current_best]:
            best_in_group[group] = ticker
    deduped = {t: liquid[t] for t in best_in_group.values()}
    waterfall["after_same_issuer_dedup"] = len(deduped)

    ranked = sorted(deduped, key=lambda t: -deduped[t])
    selected = ranked[:max_issuers]
    waterfall["selected"] = len(selected)
    return {"month_end": month_end, "selected": selected, "waterfall": waterfall}


def volume_spike_ratio(dollar_volume_by_date, trading_days_sorted, asof_date,
                       short_window=5, long_window=60):
    """P006's attention proxy: recent turnover relative to the name's own norm.

    Ranking on raw dollar volume would just re-select the mega caps the
    already-stopped market-cap line held, so P006 registered a *relative*
    burst instead. Returns None when either window is incomplete or the
    baseline is zero, so an unrankable name is dropped rather than silently
    scored. Both windows end at `asof_date`, which the caller sets to the
    signal session -- never the execution session.

    This stands in for the options volume the original design wanted; that
    data is not licensed here, and this substitute is not a verified
    equivalent (see the P006 entry in docs/review/08-decisions-and-coverage.md).
    """
    recent = trailing_average_dollar_volume(dollar_volume_by_date, trading_days_sorted,
                                            asof_date, short_window)
    baseline = trailing_average_dollar_volume(dollar_volume_by_date, trading_days_sorted,
                                              asof_date, long_window)
    if recent is None or not baseline:
        return None
    return recent / baseline


def monthly_hot_universe(month_end, master, marketcap_by_ticker, dollar_volume_by_ticker,
                         trading_days_sorted, max_issuers=100, minimum_trading_days=252,
                         minimum_adv_usd=20_000_000, adv_window=63,
                         short_window=5, long_window=60):
    """P006's pool: the same docs/review/03 section 1 eligibility waterfall as
    monthly_universe(), ranked by volume_spike_ratio() instead of market cap.

    Every filter stage, the liquidity floor and the same-issuer dedup are
    deliberately identical to monthly_universe() so that a P006-vs-stopped-line
    comparison differs in the ranking key and nothing else. Dedup still keeps
    the larger market-cap share class, not the spikier one: which listing is
    the real one is a property of the issuer, not of this month's turnover.

    Like monthly_universe() the result is capped but never padded, and
    `waterfall` reports the count surviving each stage.
    """
    waterfall = {"tickers_with_marketcap_this_month": 0}
    candidates = {}
    for info in master.values():
        ticker = info["ticker"]
        if ticker not in marketcap_by_ticker or month_end not in marketcap_by_ticker[ticker]:
            continue
        waterfall["tickers_with_marketcap_this_month"] += 1
        if info["category"] not in ELIGIBLE_CATEGORIES:
            continue
        if info["exchange"] not in ELIGIBLE_EXCHANGES:
            continue
        if not info["firstpricedate"] or info["firstpricedate"] > month_end:
            continue
        history = [d for d in trading_days_sorted if info["firstpricedate"] <= d <= month_end]
        if len(history) < minimum_trading_days:
            continue
        candidates[ticker] = marketcap_by_ticker[ticker][month_end]
    waterfall["after_category_exchange_history_filter"] = len(candidates)

    liquid = {}
    for ticker, marketcap in candidates.items():
        adv = trailing_average_dollar_volume(dollar_volume_by_ticker.get(ticker, {}),
                                             trading_days_sorted, month_end, adv_window)
        if adv is not None and adv >= minimum_adv_usd:
            liquid[ticker] = marketcap
    waterfall["after_liquidity_filter"] = len(liquid)

    ticker_to_permaticker = {info["ticker"]: p for p, info in master.items()}
    group_of = group_share_classes(master)
    best_in_group = {}
    for ticker, marketcap in liquid.items():
        group = group_of.get(ticker_to_permaticker[ticker], ticker)
        current_best = best_in_group.get(group)
        if current_best is None or marketcap > liquid[current_best]:
            best_in_group[group] = ticker
    deduped = list(best_in_group.values())
    waterfall["after_same_issuer_dedup"] = len(deduped)

    spikes = {}
    for ticker in deduped:
        ratio = volume_spike_ratio(dollar_volume_by_ticker.get(ticker, {}), trading_days_sorted,
                                   month_end, short_window, long_window)
        if ratio is not None:
            spikes[ticker] = ratio
    waterfall["with_computable_spike_ratio"] = len(spikes)

    ranked = sorted(spikes, key=lambda t: (-spikes[t], t))
    selected = ranked[:max_issuers]
    waterfall["selected"] = len(selected)
    return {"month_end": month_end, "selected": selected, "waterfall": waterfall,
            "spike_ratio": {t: spikes[t] for t in selected}}
