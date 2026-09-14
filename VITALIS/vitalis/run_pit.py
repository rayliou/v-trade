"""Long-history, point-in-time-universe backtest of the exact same fixed
momentum rule P001 already runs (docs/review/03), but on real data instead
of a fixed 30-survivor sample: a real monthly-changing eligible universe
(vitalis/universe.py), real Sharadar prices (vitalis/sharadar_prices.py)
instead of Yahoo, and a much longer window (2005-2025 instead of 2021-2025).

This is the single test docs/review/09's audit and the 2026-09-13 follow-up
discussion identified as the highest-value next step: it simultaneously (a)
removes the survivorship bias in P001's 30-name sample, and (b) roughly
quadruples the number of independent time blocks available to the paired
block-bootstrap CI, which is exactly what a wide, zero-crossing interval on
a short sample needs to become more informative.

Pre-registered before running (see docs/review/08-decisions-and-coverage.md):
this run tests the *same* rule (12-1/6-1 momentum, top-10 equal weight,
monthly rebalance, hysteresis) already frozen in config/prototype-v1.json.
Its result is reported regardless of outcome -- a weak or negative result is
not grounds to silently try a different rule shape in the same run.

A second, separately pre-registered candidate (docs/review/08, same date as
the momentum-only run's follow-up discussion) also runs here: `Q10`/`Q20`
use docs/review/03 section 2's S1 formula, Total Score = 0.5*momentum +
0.5*quality, with the 50/50 weight fixed in that document *before* any
result was seen, not tuned after this run's numbers came in. Quality is
computed from real, point-in-time ART fundamentals (vitalis/pit.py) and
real historical SIC (vitalis/sic_history.py), scoped each month to that
month's own eligible pool -- the first time quality.py has been run against
the real universe rather than the original 30-symbol demo.

2005 start date: real AAPL data cross-checked with vitalis.data.check_action_bridge
shows 255 discrepancies concentrated entirely in 1998-2004 (all resolved
from 2005 onward), so the evaluation window starts no earlier than that to
stay on the clean side of that boundary. See docs/review/08.

Every independent, CPU-bound step here (per-ticker price normalization
across ~800 real tickers, the monthly eligibility screen across ~260
months, and the four strategy-variant simulations) runs across a
ProcessPoolExecutor rather than sequentially -- this machine's core count
makes that worthwhile, and none of these tasks depend on each other's
output. Large shared read-only data (bars, master, marketcap/dollar-volume
history) is sent to each worker exactly once via a pool initializer,
not re-pickled per task, so parallelizing does not itself become the
bottleneck.
"""

import argparse
import csv
import hashlib
import io
import json
import os
import sys
import traceback
import zipfile
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .data import check_action_bridge, download, fingerprint, normalize
from .local_cache import read_cache, write_cache
from .engine import downside_capture_ratio, metrics, simulate
from .macro import daily_rate_by_trading_day, download_series, normalize_series
from .run import write_csv
from .sharadar_prices import find_gap_free_tickers, normalize_ticker
from .stats import daily_returns, paired_block_bootstrap
from .pit import fundamentals_asof, normalize_fundamentals
from .quality import quality_scores
from .research_audit import (
    classify_bridge, diagnose_ledger, execution_month, finish_catalog,
    held_event_dates, pin_inputs, register_run, sha256_file, shift_month_end_inputs,
)
from .sic_history import load_sic_changes, sic_by_ticker_asof
from .universe import (
    ELIGIBLE_CATEGORIES, ELIGIBLE_EXCHANGES, distinct_trading_days,
    load_marketcap_snapshots, month_end_dates, monthly_universe, security_master,
)


def _load_ticker_rows(zip_path, tickers):
    """One streaming pass over a bulk CSV, bucketing rows by ticker for the
    requested set. Mirrors vitalis.universe's loaders but keeps full rows
    (not just one field) since both prices and actions are needed here.
    """
    wanted = set(tickers)
    by_ticker = {t: [] for t in wanted}
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(zf.namelist()[0]) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
            for row in reader:
                if row["ticker"] in wanted:
                    by_ticker[row["ticker"]].append(row)
    return by_ticker


def _normalize_one_ticker(args):
    """Worker for the price-normalization pool: pure CPU work on one
    ticker's own rows (small per-task payload), independent of every other
    ticker, so this is embarrassingly parallel across the candidate union.
    """
    ticker, stock_rows, actions_rows = args
    ticker_bars, issues = normalize_ticker(stock_rows, actions_rows)
    bridge_issues = check_action_bridge(ticker_bars)
    return ticker, ticker_bars, issues, bridge_issues


def build_real_bars(data_dir, candidate_tickers, data_start, data_end, max_workers=None):
    """Real Sharadar bars for `candidate_tickers`, restricted to
    [data_start, data_end]. Returns (bars, issues, bridge_issues). The file
    streaming itself is one sequential pass per file (I/O-bound, not worth
    parallelizing); normalizing each ticker's own rows afterward is CPU-bound
    and independent per ticker, so that part runs across a process pool.
    """
    stocks_by_ticker = _load_ticker_rows(data_dir / "stocks-bulk-full.csv.zip", candidate_tickers)
    actions_by_ticker = _load_ticker_rows(data_dir / "actions-bulk-full.csv.zip", candidate_tickers)
    tasks = []
    for ticker in candidate_tickers:
        stock_rows = [r for r in stocks_by_ticker[ticker] if data_start <= r["date"] <= data_end]
        if stock_rows:
            tasks.append((ticker, stock_rows, actions_by_ticker[ticker]))
    bars, all_issues, bridge_issues = {}, [], []
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        for ticker, ticker_bars, issues, bridge in pool.map(_normalize_one_ticker, tasks, chunksize=8):
            bars[ticker] = ticker_bars
            all_issues.extend({"ticker": ticker, **i} for i in issues)
            bridge_issues.extend({"ticker": ticker, **i} for i in bridge)
    return bars, all_issues, bridge_issues


def build_quality_by_review_month(data_dir, candidate_tickers, master, months, trading_days_sorted,
                                  symbols_by_review_month, details_output=None):
    """docs/review/03 section 2's quality score, computed once per month
    (real, point-in-time: ART fundamentals as of that month-end, real
    historical SIC as of that month-end), with the peer group for SIC
    percentiling scoped to that month's own eligible pool -- not the whole
    21-year candidate union, which would let a company's percentile shift
    just because some *other* month's roster changed, not because its own
    peers this month did.

    Returns {"YYYY-MM": {ticker: quality_score}}.
    """
    ticker_info = {info["ticker"]: info for info in master.values()}
    current_siccode = {t: info["siccode"] for t, info in ticker_info.items()}
    changes, _ = load_sic_changes(data_dir / "actions-bulk-full.csv.zip")

    lower_bound, upper_bound = trading_days_sorted[0], trading_days_sorted[-1]
    rows_by_ticker = _load_ticker_rows(data_dir / "fundamentals-bulk-full.csv.zip", candidate_tickers)
    art_rows = [
        row for rows in rows_by_ticker.values() for row in rows
        if row["dimension"] == "ART" and lower_bound <= row["date"] < upper_bound
    ]
    normalized = normalize_fundamentals(art_rows, trading_days_sorted)

    quality_by_month = {}
    for month_end in months:
        month_key = month_end[:7]
        eligible = symbols_by_review_month.get(month_key, {})
        if not eligible:
            continue
        latest = fundamentals_asof(normalized, month_end, dimension="ART")
        rows_for_month = {t: latest[t] for t in eligible if t in latest}
        sic_for_month = sic_by_ticker_asof(
            {t: current_siccode.get(t) for t in eligible}, changes, month_end)
        # Retain explicit N/A for every eligible ticker, including no filing.
        scores = quality_scores({t: rows_for_month.get(t, {}) for t in eligible}, sic_for_month)
        if details_output is not None:
            details_output[month_key] = scores
        quality_by_month[month_key] = {t: entry["quality"] for t, entry in scores.items()}
    return quality_by_month


# --- Monthly eligibility screen worker pool ---------------------------------
# Module-level globals populated once per worker process via the pool
# initializer, so the (potentially large) shared inputs are pickled once per
# worker, not once per one of ~260 month tasks.
_universe_worker_state = {}


def _init_universe_worker(master, marketcap_by_ticker, dollar_volume_by_ticker, trading_days_sorted,
                          max_issuers, minimum_trading_days, minimum_adv_usd, adv_window):
    _universe_worker_state.update(
        master=master, marketcap_by_ticker=marketcap_by_ticker,
        dollar_volume_by_ticker=dollar_volume_by_ticker, trading_days_sorted=trading_days_sorted,
        max_issuers=max_issuers, minimum_trading_days=minimum_trading_days,
        minimum_adv_usd=minimum_adv_usd, adv_window=adv_window)


def _compute_month(month_end):
    s = _universe_worker_state
    return monthly_universe(month_end, s["master"], s["marketcap_by_ticker"], s["dollar_volume_by_ticker"],
                            s["trading_days_sorted"], max_issuers=s["max_issuers"],
                            minimum_trading_days=s["minimum_trading_days"],
                            minimum_adv_usd=s["minimum_adv_usd"], adv_window=s["adv_window"])


def run_monthly_universe_screen(months, master, marketcap_by_ticker, dollar_volume_by_ticker,
                                trading_days_sorted, max_issuers, minimum_trading_days,
                                minimum_adv_usd, adv_window, max_workers=None):
    with ProcessPoolExecutor(
        max_workers=max_workers, initializer=_init_universe_worker,
        initargs=(master, marketcap_by_ticker, dollar_volume_by_ticker, trading_days_sorted,
                 max_issuers, minimum_trading_days, minimum_adv_usd, adv_window),
    ) as pool:
        return list(pool.map(_compute_month, months, chunksize=4))


# --- Per-variant simulation worker pool --------------------------------------
_simulate_worker_state = {}


def _init_simulate_worker(bars, dates, sim_config, capital_usd, cost_bps, cash_annual_rate,
                          symbols_by_review_month, quality_by_review_month):
    _simulate_worker_state.update(
        bars=bars, dates=dates, sim_config=sim_config, capital_usd=capital_usd, cost_bps=cost_bps,
        cash_annual_rate=cash_annual_rate, symbols_by_review_month=symbols_by_review_month,
        quality_by_review_month=quality_by_review_month)


def _simulate_one_variant(variant):
    s = _simulate_worker_state
    return variant, simulate(s["bars"], s["dates"], s["sim_config"], s["capital_usd"], s["cost_bps"],
                             variant, cash_annual_rate=s["cash_annual_rate"],
                             symbols_by_review_month=s["symbols_by_review_month"],
                             quality_by_review_month=s["quality_by_review_month"])


def _simulate_cost_scenario(task):
    capital, cost_bps, annual_fee, variant = task
    s = _simulate_worker_state
    config = dict(s["sim_config"], annual_system_cash_cost_usd=annual_fee)
    result = simulate(s["bars"], s["dates"], config, capital, cost_bps, variant,
                      cash_annual_rate=s["cash_annual_rate"],
                      symbols_by_review_month=s["symbols_by_review_month"],
                      quality_by_review_month=s["quality_by_review_month"])
    reference, _ = total_return_reference(s["bars"]["QQQ"], s["dates"],
        config["evaluation_start"], config["evaluation_end"], capital, cost_bps)
    result[0].update(annual_system_cash_cost_usd=annual_fee,
                     excess_cagr_pp=(result[0]["cagr"] - reference["cagr"]) * 100,
                     qqq_reference_cagr=reference["cagr"])
    return task, result


def total_return_reference(bars, dates, evaluation_start, evaluation_end, capital, cost_bps):
    sessions = [d for d in dates if evaluation_start <= d <= evaluation_end]
    first = bars[sessions[0]]
    adjusted_open = first["open"] * first["adjclose"] / first["close"]
    units = capital / (1 + cost_bps / 10000) / adjusted_open
    rows = [{"date": d, "nav_usd": units * bars[d]["adjclose"]} for d in sessions]
    summary = metrics(rows, capital)
    summary.update({"variant": "QQQ-total-return-proxy", "capital_usd": capital, "cost_bps": cost_bps})
    return summary, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/authorized/sharadar")
    parser.add_argument("--cache-dir", default="data/public-yahoo")
    parser.add_argument("--fred-cache-dir", default="data/public-fred")
    parser.add_argument("--benchmark-data-end", default="2026-09-13")
    parser.add_argument("--offline", action="store_true", default=True,
                        help="research always reads exact local caches; missing data blocks")
    parser.add_argument("--catalog-path", default="data/catalog.sqlite")
    parser.add_argument("--registry-path", default="docs/prototype/experiments.jsonl")
    parser.add_argument("--output-dir", default="runs")
    parser.add_argument("--universe-start-month", default="2004-06")
    parser.add_argument("--data-start", default="2004-01-01")
    parser.add_argument("--evaluation-start", default="2005-01-03")
    parser.add_argument("--evaluation-end", default="2025-12-31")
    parser.add_argument("--capital-usd", type=float, default=300_000)
    parser.add_argument("--cost-bps", type=float, default=10)
    parser.add_argument("--max-issuers", type=int, default=200)
    parser.add_argument("--minimum-trading-days", type=int, default=252)
    parser.add_argument("--minimum-adv-usd", type=float, default=20_000_000)
    parser.add_argument("--adv-window", type=int, default=63)
    parser.add_argument("--prefilter-buffer", type=int, default=300)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260913)
    parser.add_argument("--sector-weight-cap", type=float, default=0.30)
    parser.add_argument("--annual-system-cash-cost-usd", type=float, default=600)
    parser.add_argument("--cost-scenario-annual-fee-usd", type=float, default=828,
                        help="current monthly subscription annualized, excluding unconfirmed taxes")
    parser.add_argument("--max-workers", type=int, default=None,
                        help="defaults to os.cpu_count() via ProcessPoolExecutor")
    args = parser.parse_args()

    config = vars(args)
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-pit-" + config_hash[:8]
    run = Path(args.output_dir) / run_id
    run.mkdir(parents=True, exist_ok=False)
    (run / "config.json").write_text(json.dumps(config, indent=2))
    manifest = {"run_id": run_id, "config_sha256": config_hash, "status": "starting"}
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2))

    data_dir = Path(args.data_dir)
    print(f"Using up to {args.max_workers or os.cpu_count()} worker processes for parallel steps", flush=True)
    try:
        input_paths = [data_dir / f"{name}-bulk-full.csv.zip" for name in
                       ("tickers", "daily", "stocks", "actions", "fundamentals", "descriptions")]
        input_paths += [Path(args.cache_dir) / f"QQQ-{args.data_start}-{args.benchmark_data_end}.json",
                        Path(args.fred_cache_dir) / f"DGS3MO-{args.data_start}-{args.benchmark_data_end}.json"]
        print("Verifying local source hashes and freezing code...", flush=True)
        manifest.update(pin_inputs(run, input_paths, args.catalog_path))
        manifest.update(status="pinned", remote_requests=0,
                        timing_contract="as-of month-end M -> execution month M+1")
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
        cache_root = data_dir / 'derived-cache'
        source_hashes = {Path(a['path']).name: a['sha256'] for a in manifest['source_artifacts']}
        code_hashes = {a['name']: a['sha256'] for a in manifest['code_artifacts']}
        print("Building security master and trading calendar...", flush=True)
        master = security_master(data_dir / "tickers-bulk-full.csv.zip")
        ticker_info = {info["ticker"]: info for info in master.values()}
        calendar_key = fingerprint({'stage': 'calendar', 'source': source_hashes['daily-bulk-full.csv.zip'],
                                    'code': code_hashes['universe.py']})
        calendar_cache = read_cache(cache_root, calendar_key)
        if calendar_cache is None:
            all_days = distinct_trading_days(data_dir / "daily-bulk-full.csv.zip")
            write_cache(cache_root, calendar_key, {'days': sorted(all_days)})
        else:
            all_days = set(calendar_cache['days'])
        trading_days_sorted = sorted(d for d in all_days if d <= args.evaluation_end)
        months = [d for d in month_end_dates(all_days)
                 if args.universe_start_month <= d[:7] <= args.evaluation_end[:7]]
        print(f"  {len(months)} month-end dates: {months[0]} to {months[-1]}", flush=True)

        print("Loading market cap snapshots...", flush=True)
        marketcap_key = fingerprint({'stage': 'marketcap', 'source': source_hashes['daily-bulk-full.csv.zip'],
                                     'code': code_hashes['universe.py'], 'months': months})
        marketcap_cache = read_cache(cache_root, marketcap_key)
        if marketcap_cache is None:
            marketcap_by_ticker = load_marketcap_snapshots(data_dir / "daily-bulk-full.csv.zip", months)
            write_cache(cache_root, marketcap_key, {'marketcap': marketcap_by_ticker})
        else:
            marketcap_by_ticker = marketcap_cache['marketcap']

        print("Pre-filtering per-month candidates...", flush=True)
        candidate_union = set()
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
            candidate_union.update(t for t, _ in pool[:args.prefilter_buffer])
        candidate_union.add("QQQ")
        print(f"  {len(candidate_union)} distinct candidate tickers over the full window", flush=True)

        print("Building real Sharadar bars for the candidate union (parallel)...", flush=True)
        bars_key = fingerprint({'stage': 'bars', 'sources': {k: source_hashes[k] for k in
                               ('stocks-bulk-full.csv.zip', 'actions-bulk-full.csv.zip')},
                               'code': {k: code_hashes[k] for k in ('sharadar_prices.py', 'data.py')},
                               'tickers': sorted(candidate_union - {'QQQ'}),
                               'data_start': args.data_start, 'data_end': args.evaluation_end})
        bars_cache = read_cache(cache_root, bars_key)
        if bars_cache is None:
            bars, issues, bridge_issues = build_real_bars(
                data_dir, candidate_union - {"QQQ"}, args.data_start, args.evaluation_end, args.max_workers)
            write_cache(cache_root, bars_key, {'bars': bars, 'issues': issues, 'bridge_issues': bridge_issues})
        else:
            bars, issues, bridge_issues = (bars_cache[k] for k in ('bars', 'issues', 'bridge_issues'))
        del bars_cache
        manifest['derived_cache_keys'] = {'calendar': calendar_key, 'marketcap': marketcap_key, 'bars': bars_key}
        print(f"  {len(bars)} tickers with usable bars, {len(issues)} bar issues, "
              f"{len(bridge_issues)} action-bridge discrepancies", flush=True)

        print("Fetching real QQQ total-return benchmark (Yahoo)...", flush=True)
        qqq_envelope = download("QQQ", args.data_start, args.benchmark_data_end, args.cache_dir, offline=True)
        bars["QQQ"], qqq_issues = normalize(qqq_envelope)
        issues.extend({"ticker": "QQQ", **i} for i in qqq_issues)
        dates = sorted(bars["QQQ"])

        print("Excluding any candidate with an internal trading-history gap...", flush=True)
        gap_free, gaps = find_gap_free_tickers({t: b for t, b in bars.items() if t != "QQQ"}, dates)
        if gaps:
            print(f"  excluded {len(gaps)} tickers with a gap inside their own active window "
                  f"(e.g. {sorted(gaps)[0]}: {gaps[sorted(gaps)[0]][:3]}...)", flush=True)
        (run / "gap_excluded_tickers.json").write_text(json.dumps(gaps, indent=2))
        if gaps:
            # Future internal gaps must not determine historical eligibility.
            raise ValueError("Internal price gaps require explicit halt handling; cannot exclude using future data")

        print("Computing dollar-volume history for the liquidity screen (from real bars)...", flush=True)
        dollar_volume_by_ticker = {
            t: {d: b["dollar_volume"] for d, b in ticker_bars.items()} for t, ticker_bars in bars.items()
        }

        print("Running the monthly eligibility screen (parallel across months)...", flush=True)
        universe_diagnostics = run_monthly_universe_screen(
            months, master, marketcap_by_ticker, dollar_volume_by_ticker, trading_days_sorted,
            args.max_issuers, args.minimum_trading_days, args.minimum_adv_usd, args.adv_window,
            args.max_workers)
        symbols_by_review_month = {
            result["month_end"][:7]: {t: (ticker_info[t]["sector"] or "Unknown") for t in result["selected"]}
            for result in universe_diagnostics
        }
        (run / "universe_diagnostics.json").write_text(json.dumps(universe_diagnostics, indent=2))
        (run / "review_timing.json").write_text(json.dumps([
            {"as_of": result["month_end"], "execution_month": execution_month(result["month_end"])}
            for result in universe_diagnostics], indent=2))

        print("Computing real point-in-time quality scores (docs/review/03 section 2)...", flush=True)
        quality_details = {}
        quality_by_review_month = build_quality_by_review_month(
            data_dir, candidate_union - {"QQQ"}, master, months, trading_days_sorted,
            symbols_by_review_month, details_output=quality_details)
        quality_by_review_month = shift_month_end_inputs(quality_by_review_month)
        quality_details = shift_month_end_inputs(quality_details)
        symbols_by_review_month = shift_month_end_inputs(symbols_by_review_month)
        (run / "quality_details.json").write_text(json.dumps(quality_details, indent=2))
        (run / "quality_by_review_month_sample.json").write_text(json.dumps(
            {k: v for k, v in list(quality_by_review_month.items())[:3]}, indent=2))

        print("Fetching cash-yield reference (FRED)...", flush=True)
        cash_yield_envelope = download_series("DGS3MO", args.data_start, args.benchmark_data_end,
                                             args.fred_cache_dir, offline=True)
        cash_annual_rate = daily_rate_by_trading_day(normalize_series(cash_yield_envelope), dates)

        print("Simulating (parallel across variants)...", flush=True)
        # Fallback dict for engine.simulate() if a review month were ever
        # missing from symbols_by_review_month (should not happen, since
        # `months` spans the full evaluation window) -- carries the real
        # per-ticker sector, not a placeholder, so it is a safe fallback
        # rather than a silent sector-cap corruption if it is ever used.
        static_symbols = {t: sector for month in symbols_by_review_month.values() for t, sector in month.items()}
        sim_config = {
            "evaluation_start": args.evaluation_start, "evaluation_end": args.evaluation_end,
            "symbols": static_symbols, "minimum_adv_usd": 0,  # liquidity already screened upstream
            "sector_weight_cap": args.sector_weight_cap, "volatility_target": 0.15,
            "annual_system_cash_cost_usd": args.annual_system_cash_cost_usd,
            "drawdown_research_limit": 0.30,
        }
        reference, ref_nav = total_return_reference(
            bars["QQQ"], dates, args.evaluation_start, args.evaluation_end, args.capital_usd, args.cost_bps)
        benchmark_returns = daily_returns(ref_nav, args.capital_usd)

        variants = ("QQQ", "QQQ-cash15", "M10", "M20", "M10-risk15", "Q10", "Q20")
        with ProcessPoolExecutor(
            max_workers=min(len(variants), args.max_workers or os.cpu_count() or 1),
            initializer=_init_simulate_worker,
            initargs=(bars, dates, sim_config, args.capital_usd, args.cost_bps, cash_annual_rate,
                     symbols_by_review_month, quality_by_review_month),
        ) as pool:
            variant_results = dict(pool.map(_simulate_one_variant, variants))

        results = [reference]
        primary_bootstrap = {}
        exposure, all_exits, all_unfilled, diagnostics = {}, [], [], {}
        write_csv(run / "QQQ-total-return-proxy-nav.csv", ref_nav)
        for variant in variants:
            summary, nav, trades, positions, decisions, warnings, contributions = variant_results[variant]
            summary["excess_cagr_pp"] = (summary["cagr"] - reference["cagr"]) * 100
            summary["sample_return_pass"] = summary["cagr"] > reference["cagr"]
            summary["sample_drawdown_pass"] = -summary["max_drawdown"] <= sim_config["drawdown_research_limit"]
            summary["sample_joint_pass"] = summary["sample_return_pass"] and summary["sample_drawdown_pass"]
            strategy_returns = daily_returns(nav, args.capital_usd)
            summary["downside_capture_vs_qqq_total_return"] = downside_capture_ratio(strategy_returns, benchmark_returns)
            results.append(summary)
            folder = run / variant
            folder.mkdir()
            for name, rows in (("nav", nav), ("trades", trades), ("holdings", positions),
                              ("risk-flags", warnings), ("contributions", contributions)):
                write_csv(folder / f"{name}.csv", rows)
            (folder / "decisions.json").write_text(json.dumps(decisions, indent=2))
            exposure[variant] = held_event_dates(positions, dates)
            all_exits.extend({"variant": variant, **w} for w in warnings
                             if w.get("flag") == "forced_exit_data_discontinued")
            all_unfilled.extend({"variant": variant, **w} for w in warnings
                                if w.get("flag") == "unfilled_order_no_execution_bar")
            diagnostics[variant] = diagnose_ledger(
                nav, contributions, args.capital_usd, ref_nav, positions,
                {t: i["sector"] or "Unknown" for t, i in ticker_info.items()}, quality_details)
            if variant.startswith("M") or variant.startswith("Q"):
                bootstrap = {
                    block: paired_block_bootstrap(strategy_returns, benchmark_returns, block_trading_days=block,
                                                  replicates=args.bootstrap_replicates, seed=args.bootstrap_seed)
                    for block in (21, 63)
                }
                (folder / "bootstrap.json").write_text(json.dumps(bootstrap, indent=2))
                primary_bootstrap[variant] = bootstrap
            forced_exits = sum(1 for w in warnings if w.get("flag") == "forced_exit_data_discontinued")
            print(f"  {variant}: CAGR {summary['cagr']:.2%}, vs QQQ {summary['excess_cagr_pp']:+.2f}pp, "
                  f"max_dd {summary['max_drawdown']:.2%}, forced_exits={forced_exits}", flush=True)

        print("Running separately labeled capital/cost scenarios (frozen strategy rules)...", flush=True)
        cases = [(capital, cost, args.cost_scenario_annual_fee_usd, variant)
                 for capital, cost in [(300000, 10), (200000, 10), (400000, 10),
                                       (200000, 25), (400000, 25)]
                 for variant in ("M10", "M20", "M10-risk15", "Q10", "Q20")]
        cost_summaries = []
        with ProcessPoolExecutor(
            max_workers=min(5, args.max_workers or os.cpu_count() or 1),
            initializer=_init_simulate_worker,
            initargs=(bars, dates, sim_config, args.capital_usd, args.cost_bps, cash_annual_rate,
                      symbols_by_review_month, quality_by_review_month),
        ) as pool:
            for task, result in pool.map(_simulate_cost_scenario, cases):
                capital, cost, fee, variant = task
                folder = run / 'cost-scenarios' / f'{capital}-{cost}bps-{fee}fee' / variant
                folder.mkdir(parents=True)
                summary, nav, trades, positions, decisions, warnings, contributions = result
                cost_summaries.append(summary)
                for name, rows in (("nav", nav), ("trades", trades), ("holdings", positions),
                                   ("risk-flags", warnings), ("contributions", contributions)):
                    write_csv(folder / f"{name}.csv", rows)
                (folder / 'decisions.json').write_text(json.dumps(decisions, indent=2))
        (run / 'cost_scenarios.json').write_text(json.dumps(cost_summaries, indent=2, allow_nan=False))

        (run / "summary.json").write_text(json.dumps(results, indent=2, allow_nan=False))
        (run / "bootstrap_by_variant.json").write_text(json.dumps(primary_bootstrap, indent=2))
        actions = _load_ticker_rows(data_dir / "actions-bulk-full.csv.zip", candidate_union)
        classified = classify_bridge(bridge_issues, actions, args.evaluation_start,
                                     args.evaluation_end, exposure)
        for exit_row in all_exits:
            center = datetime.fromisoformat(exit_row["date"]).date()
            exit_row["nearby_actions"] = [r for r in actions.get(exit_row["symbol"], [])
                if abs((datetime.fromisoformat(r["date"]).date() - center).days) <= 7
                and not r["action"].startswith("sicchange")]
            exit_row["settlement_verified"] = False
        evaluation_issues = [i for i in classified if i["in_evaluation"]]
        gates = {"month_end_timing": True, "source_checksums": True,
                 "price_completeness": not (issues or gaps),
                 "corporate_action_bridge": not evaluation_issues,
                 "economic_exit_settlement": not all_exits,
                 "execution_quote_coverage": not all_unfilled,
                 "historical_security_metadata": False}
        audit = {"bar_issues": issues, "action_bridge": classified, "exit_proxies": all_exits,
                 "unfilled_orders": all_unfilled, "gates": gates,
                 "bridge_total": len(classified), "bridge_in_evaluation": len(evaluation_issues),
                 "bridge_held_events": sum(bool(i["held_variants"]) for i in evaluation_issues),
                 "data_gate_pass": all(gates.values()),
                 "limitations": ["Action proximity does not certify economic settlement.",
                                  "Current exchange/category/sector snapshots remain a PIT limitation.",
                                  "SIC reconstructed chains have unresolved discrepancies."]}
        (run / "data_audit.json").write_text(json.dumps(audit, indent=2))
        (run / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
        decision = {
            "experiment_id": "P004-engineering-corrected-baseline", "run_id": run_id,
            "pre_registered": "M10/M20/M10-risk15: same rule as config/prototype-v1.json, real PIT "
                              "universe and prices, no tuning. Q10/Q20: docs/review/03 section 2's S1 "
                              "formula (0.5*momentum + 0.5*quality), weight fixed before any result seen.",
            "investment_decision": "insufficient_evidence",
            "engineering_decision": "completed_with_explicit_data_gaps",
            "data_gate_pass": audit["data_gate_pass"],
            "joint_sample_pass_variants": [r["variant"] for r in results if r.get("sample_joint_pass")],
            "acceptance_blockers": ["Unresolved corporate-action/exit and historical metadata gates",
                                    "Inspected historical period; multiple-comparison correction outstanding"],
            "action_bridge_discrepancies": len(bridge_issues),
        }
        (run / "decision.json").write_text(json.dumps(decision, indent=2))
        for artifact in manifest["source_artifacts"]:
            if sha256_file(artifact["path"]) != artifact["sha256"]:
                raise ValueError("Pinned source changed during research run")
        manifest.update(status="completed", output_artifacts=[
            {"path": str(p.relative_to(run)), "sha256": sha256_file(p)}
            for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'manifest.json'])
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
        finish_catalog(args.catalog_path, run_id, "completed")
        register_run(args.registry_path, {"experiment_id": decision["experiment_id"],
                     "run_id": run_id, "status": "completed", "config_sha256": config_hash,
                     "manifest_sha256": sha256_file(run / "manifest.json"),
                     "investment_decision": decision["investment_decision"]})
        print(f"\nWrote results to {run}", flush=True)
    except Exception as error:
        manifest.update(status="failed", error=f"{type(error).__name__}: {error}")
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
        finish_catalog(args.catalog_path, run_id, "failed")
        register_run(args.registry_path, {"experiment_id": "P004-engineering-corrected-baseline",
                     "run_id": run_id, "status": "failed", "config_sha256": config_hash,
                     "error": manifest["error"]})
        traceback.print_exc()
        print(manifest["error"], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
