"""Convert real Sharadar `stocks` + `actions` bulk data into the exact same
normalized bars schema vitalis/data.normalize() produces from Yahoo, so
vitalis/engine.py's rank_signals()/simulate()/etc. run against it unchanged.

Field conventions, verified against real AAPL rows around its 2020-08-31 4:1
split (see tests/test_sharadar_prices.py):
  - `open`/`close` in the bulk stocks table are split-adjusted but not
    dividend-adjusted (continuous across a split).
  - `closeunadj` is the true nominal historical traded price (a 4x jump on
    the split date, needing no reconstruction -- unlike Yahoo, which only
    gives a fully split-adjusted close and requires multiplying by the
    product of all *future* split ratios to recover the nominal price).
  - `closeadj` is the fully split-and-dividend-adjusted total-return-style
    close, used the same way Yahoo's adjclose is used elsewhere.
  - The `actions` table's `dividend` value is expressed in *current*
    (fully split-adjusted) share terms -- confirmed empirically: AAPL's real
    2020-02-07 dividend of $0.1925 in this table is exactly $0.77 / 4, and
    $0.77/share was AAPL's real pre-split quarterly dividend. This needs the
    same forward-split-factor scaling vitalis/data.py already applies to
    Yahoo's dividend field, to express it in nominal terms as of that date.

Because `closeunadj` is already nominal (no reconstruction needed for
price), only the *dividend* field needs the future-split multiplication this
module borrows from vitalis/data.py's normalize().
"""

import math

NOMINAL_OPEN_MIN_RATIO = 1e-6  # guards a division by an unexpectedly-zero close


def find_gap_free_tickers(bars_by_ticker, trading_days_sorted):
    """A ticker's bars are "gap-free" if every real market trading day
    between its own first and last observed date is present -- absence
    before listing or after delisting is not a gap, only a missing day
    *within* its own active window is.

    vitalis/engine.py's simulate() has no trading-halt handling: a held
    position with even one missing day inside its active window raises a
    bare KeyError deep in the day loop rather than a clear, actionable
    error. Real 20+ year, multi-hundred-ticker histories do have occasional
    genuine halts (bankruptcy proceedings, M&A-related suspensions, data
    provider gaps) that a hand-picked 30-name sample never surfaces. Rather
    than teach the engine to model a halt (freeze the position? mark to
    last price? both are modeling choices this project has not registered),
    this excludes such a ticker from the eligible pool entirely -- a
    conservative, disclosed choice, not a silent one.

    Returns (gap_free_tickers: set, gaps: {ticker: [missing dates]}) so the
    excluded count and the specific gaps are both available to report.
    """
    gap_free, gaps = set(), {}
    for ticker, ticker_bars in bars_by_ticker.items():
        if not ticker_bars:
            continue
        first, last = min(ticker_bars), max(ticker_bars)
        expected = [d for d in trading_days_sorted if first <= d <= last]
        missing = [d for d in expected if d not in ticker_bars]
        if missing:
            gaps[ticker] = missing
        else:
            gap_free.add(ticker)
    return gap_free, gaps


def normalize_ticker(stocks_rows, actions_rows):
    """stocks_rows: real `stocks` bulk rows for one ticker (dicts with
    date/open/close/volume/closeadj/closeunadj). actions_rows: real
    `actions` bulk rows for the same ticker with action in ("split", "dividend").

    Returns (bars, issues) in the same shape as vitalis.data.normalize():
    bars[date] = {"open", "close", "adjclose", "dollar_volume", "split", "dividend"}.
    """
    splits = {}
    for row in actions_rows:
        if row["action"] != "split":
            continue
        ratio = float(row["value"])
        if not math.isfinite(ratio) or ratio <= 0:
            raise ValueError(f"Invalid split ratio: {row}")
        splits[row["date"]] = ratio
    raw_dividends = {row["date"]: float(row["value"]) for row in actions_rows if row["action"] == "dividend"}

    bars, issues = {}, []
    for row in stocks_rows:
        day = row["date"]
        values = [row["open"], row["close"], row["volume"], row["closeadj"], row["closeunadj"]]
        if any(v in (None, "", "N/A") for v in values):
            issues.append({"date": day, "issue": "invalid_bar"})
            continue
        opening, closing, volume, adjclose, closeunadj = map(float, values)
        if not all(math.isfinite(v) for v in (opening, closing, volume, adjclose, closeunadj)):
            issues.append({"date": day, "issue": "nonfinite_bar"})
            continue
        if min(opening, closing, adjclose, closeunadj) <= 0 or volume < 0:
            raise ValueError(f"Invalid price/volume: {day} {row}")
        if day in bars:
            raise ValueError(f"Duplicate daily bar: {day}")
        # Nominal open: closeunadj is already the true traded close for the
        # day, so the same day's open/close split-adjustment ratio recovers
        # the nominal open (splits apply uniformly across a session's OHLC).
        nominal_ratio = closeunadj / closing if closing > NOMINAL_OPEN_MIN_RATIO else 1.0
        # Dividends are in current (fully split-adjusted) share terms; scale
        # by the product of splits strictly after this date to express the
        # nominal-at-the-time amount, matching vitalis.data.normalize()'s
        # treatment of Yahoo's dividend field.
        future_split_factor = math.prod(ratio for split_date, ratio in splits.items() if split_date > day)
        bars[day] = {
            "open": opening * nominal_ratio,
            "close": closeunadj,
            "adjclose": adjclose,
            # Both source close and volume are split-adjusted; nominal close
            # multiplied by adjusted volume overstates pre-split liquidity.
            "dollar_volume": closing * volume,
            "split": splits.get(day, 1.0),
            "dividend": raw_dividends.get(day, 0.0) * future_split_factor,
        }
    return bars, issues
