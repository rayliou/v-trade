"""Point-in-time candidate universe CLI: docs/review/03 section 1's eligibility
screen applied to real, licensed Sharadar bulk data.

This is a research artifact, not a P001/P003 result by itself — see
docs/review/08-decisions-and-coverage.md for the registered decision on
whether/when it replaces P001's 30-name survivor sample, and each function's
docstring in vitalis/universe.py for what this screen does and does not
establish (current-only exchange/category, no PIT SIC history yet).

Reads only from the local, licensed, git-ignored data/authorized/sharadar/
bulk cache — never touches the network. Run vitalis.sharadar's
download_bulk_table() first if that cache is not present.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .universe import (
    ELIGIBLE_CATEGORIES, ELIGIBLE_EXCHANGES, distinct_trading_days, load_dollar_volume,
    load_marketcap_snapshots, load_sp500_table, month_end_dates, monthly_universe,
    reconstruct_membership, security_master,
)


def file_sha256(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def prefilter_candidates(marketcap_by_ticker, ticker_info, months, buffer_size):
    """Per month: category/exchange/history-eligible tickers ranked by market
    cap, top `buffer_size` as a bound on how many tickers need dollar-volume
    history loaded, before the real liquidity filter narrows to the final
    (typically much smaller) selection.
    """
    per_month, union = {}, set()
    for month_end in months:
        pool = []
        for ticker, snapshots in marketcap_by_ticker.items():
            if month_end not in snapshots:
                continue
            info = ticker_info.get(ticker)
            if not info or info["category"] not in ELIGIBLE_CATEGORIES or info["exchange"] not in ELIGIBLE_EXCHANGES:
                continue
            if not info["firstpricedate"] or info["firstpricedate"] > month_end:
                continue
            pool.append((ticker, snapshots[month_end]))
        pool.sort(key=lambda kv: -kv[1])
        top = [t for t, _ in pool[:buffer_size]]
        per_month[month_end] = top
        union.update(top)
    return per_month, union


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/authorized/sharadar")
    parser.add_argument("--output-dir", default="runs")
    parser.add_argument("--start-month", default="2019-06", help="first YYYY-MM month-end to include")
    parser.add_argument("--end-month", default="2025-12", help="last YYYY-MM month-end to include")
    parser.add_argument("--max-issuers", type=int, default=200)
    parser.add_argument("--minimum-trading-days", type=int, default=252)
    parser.add_argument("--minimum-adv-usd", type=float, default=20_000_000)
    parser.add_argument("--adv-window", type=int, default=63)
    parser.add_argument("--prefilter-buffer", type=int, default=300,
                        help="top-N by market cap kept per month before the liquidity filter")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    tickers_zip = data_dir / "tickers-bulk-full.csv.zip"
    daily_zip = data_dir / "daily-bulk-full.csv.zip"
    stocks_zip = data_dir / "stocks-bulk-full.csv.zip"
    sp500_zip = data_dir / "sp500-bulk-full.csv.zip"
    for path in (tickers_zip, daily_zip, stocks_zip):
        if not path.exists():
            print(f"Missing required bulk file: {path}. Run vitalis.sharadar.download_bulk_table() first.",
                 file=sys.stderr)
            return 2

    config = {k: v for k, v in vars(args).items()}
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-universe-" + config_hash[:8]
    run = Path(args.output_dir) / run_id
    run.mkdir(parents=True, exist_ok=False)
    (run / "config.json").write_text(json.dumps(config, indent=2))

    print("Building security master...", flush=True)
    master = security_master(tickers_zip)
    ticker_info = {info["ticker"]: info for info in master.values()}
    print(f"  {len(master)} securities with price coverage", flush=True)

    print("Collecting trading calendar from daily.csv...", flush=True)
    all_days = distinct_trading_days(daily_zip)
    trading_days_sorted = sorted(all_days)
    months = [d for d in month_end_dates(all_days) if args.start_month <= d[:7] <= args.end_month]
    if not months:
        print("No month-end dates in the requested range.", file=sys.stderr)
        return 2
    print(f"  {len(months)} month-end dates: {months[0]} to {months[-1]}", flush=True)

    print("Loading market cap snapshots (single pass over daily.csv)...", flush=True)
    marketcap_by_ticker = load_marketcap_snapshots(daily_zip, months)

    print("Pre-filtering candidates per month...", flush=True)
    _, candidate_union = prefilter_candidates(marketcap_by_ticker, ticker_info, months, args.prefilter_buffer)
    print(f"  {len(candidate_union)} distinct tickers need dollar-volume history", flush=True)

    print("Loading dollar volume for the candidate union (single pass over stocks.csv)...", flush=True)
    dollar_volume_by_ticker = load_dollar_volume(
        stocks_zip, candidate_union, trading_days_sorted[0], months[-1])

    print("Running the eligibility screen for each month...", flush=True)
    results = [
        monthly_universe(month_end, master, marketcap_by_ticker, dollar_volume_by_ticker,
                         trading_days_sorted, max_issuers=args.max_issuers,
                         minimum_trading_days=args.minimum_trading_days,
                         minimum_adv_usd=args.minimum_adv_usd, adv_window=args.adv_window)
        for month_end in months
    ]
    (run / "monthly_universe.json").write_text(json.dumps(results, indent=2))

    diagnostics = {
        "months": len(results),
        "selected_count_min": min(len(r["selected"]) for r in results),
        "selected_count_max": max(len(r["selected"]) for r in results),
        "month_over_month_name_changes": [
            len(set(a["selected"]) ^ set(b["selected"])) for a, b in zip(results, results[1:])
        ],
    }
    if sp500_zip.exists():
        events, snapshots = load_sp500_table(sp500_zip)
        anchor_candidates = [d for d in snapshots if d <= results[0]["month_end"]]
        if anchor_candidates:
            anchor = max(anchor_candidates)
            sp500_overlap = []
            for r in results:
                sp500_members = reconstruct_membership(events, anchor, snapshots[anchor], r["month_end"])
                ours = set(r["selected"])
                sp500_overlap.append({
                    "month_end": r["month_end"], "ours": len(ours), "sp500": len(sp500_members),
                    "overlap": len(ours & sp500_members),
                })
            diagnostics["sp500_overlap_by_month"] = sp500_overlap
    (run / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))

    manifest = {
        "run_id": run_id, "config_sha256": config_hash,
        "source_checksums": {
            "tickers": file_sha256(tickers_zip), "daily": file_sha256(daily_zip),
            "stocks": file_sha256(stocks_zip),
            **({"sp500": file_sha256(sp500_zip)} if sp500_zip.exists() else {}),
        },
        "status": "completed",
    }
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote {len(results)} month-end universe snapshots to {run}", flush=True)
    print(f"Selected count: min={diagnostics['selected_count_min']}, max={diagnostics['selected_count_max']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
