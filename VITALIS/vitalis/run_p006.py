"""P006: hot-volume-spike pool, 1-month formation, quality-threshold exclusion,
3/5-name concentrated holdings (docs/review/08-decisions-and-coverage.md,
"P006预注册"). A separate hypothesis from the stopped P001-P005 market-cap
momentum line, explicitly user-authorized after that line's closeout --
see the P006 registration entry for exactly which parameters are frozen and
why, and for the acceptance criteria fixed before this ever ran.

Reuses run_pit.py's provenance pinning, price normalization, quality
scoring, simulation workers and audit/reporting machinery; the only
genuinely new pipeline stage is the candidate universe itself, built from a
whole-market relative-volume screen (vitalis.universe.monthly_hot_universe)
instead of a market-cap screen. That screen's own liquidity/eligibility
ranking is authoritative -- unlike run_pit.py's two-step prefilter-by-cap
then refine-by-bars-volume, there is only one pass here, because
monthly_hot_universe() already ranks by the exact same real dollar-volume
figures (vitalis.universe.load_dollar_volume(), now sharing the P004-fixed
close*volume convention with sharadar_prices.py) that a bars-based refinement
would otherwise recompute.
"""

import argparse
import hashlib
import json
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .data import download, fingerprint, normalize
from .local_cache import read_cache, write_cache
from .engine import downside_capture_ratio, simulate
from .macro import daily_rate_by_trading_day, download_series, normalize_series
from .quality import excluded_by_quality_threshold
from .run import write_csv
from .run_pit import (
    _init_simulate_worker, _load_ticker_rows, _simulate_cost_scenario, _simulate_one_variant,
    build_quality_by_review_month, build_real_bars, total_return_reference,
)
from .sharadar_prices import find_gap_free_tickers
from .stats import daily_returns, paired_block_bootstrap
from .research_audit import (
    classify_bridge, diagnose_ledger, execution_month, finish_catalog,
    held_event_dates, pin_inputs, register_run, sha256_file, shift_month_end_inputs,
)
from .universe import (
    ELIGIBLE_CATEGORIES, ELIGIBLE_EXCHANGES, distinct_trading_days, load_dollar_volume,
    load_marketcap_snapshots, month_end_dates, monthly_hot_universe, security_master,
)


def build_hot_universe(data_dir, master, months, trading_days_sorted, max_issuers,
                       minimum_trading_days, minimum_adv_usd, adv_window,
                       short_window, long_window):
    """Whole-market volume-spike screen across every month, one pass.

    Deliberately serial, not a ProcessPoolExecutor pool like run_pit.py's
    market-cap screen: the expensive part is the single one-time
    load_dollar_volume() scan (whole eligible market, ~48s/~3.5GB measured
    against the real bulk file), not the per-month computation once that is
    loaded (~0.8s/month measured, ~210s for the full 259-month history).
    Spreading that across worker processes would instead multiply the
    ~3.5GB structure by worker count via each spawned process's own pickled
    copy, for no real speed benefit -- the reverse of run_pit.py's tradeoff,
    where the bars pickled once per worker are far smaller.
    """
    ticker_info = {info["ticker"]: info for info in master.values()}
    eligible = [t for t, info in ticker_info.items()
               if info["category"] in ELIGIBLE_CATEGORIES and info["exchange"] in ELIGIBLE_EXCHANGES]
    print(f"  {len(eligible)} category/exchange-eligible tickers before liquidity/history screening",
         flush=True)
    marketcap_by_ticker = load_marketcap_snapshots(data_dir / "daily-bulk-full.csv.zip", months)
    volume_by_ticker = load_dollar_volume(data_dir / "stocks-bulk-full.csv.zip", eligible,
                                          trading_days_sorted[0], trading_days_sorted[-1])
    results = []
    for i, month_end in enumerate(months):
        results.append(monthly_hot_universe(
            month_end, master, marketcap_by_ticker, volume_by_ticker, trading_days_sorted,
            max_issuers=max_issuers, minimum_trading_days=minimum_trading_days,
            minimum_adv_usd=minimum_adv_usd, adv_window=adv_window,
            short_window=short_window, long_window=long_window))
        if (i + 1) % 50 == 0:
            print(f"  ...screened {i + 1}/{len(months)} months", flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/authorized/sharadar")
    parser.add_argument("--cache-dir", default="data/public-yahoo")
    parser.add_argument("--fred-cache-dir", default="data/public-fred")
    parser.add_argument("--benchmark-data-end", default="2026-09-13")
    parser.add_argument("--catalog-path", default="data/catalog.sqlite")
    parser.add_argument("--registry-path", default="docs/prototype/experiments.jsonl")
    parser.add_argument("--output-dir", default="runs")
    parser.add_argument("--universe-start-month", default="2004-06")
    parser.add_argument("--data-start", default="2004-01-01")
    parser.add_argument("--evaluation-start", default="2005-01-03")
    parser.add_argument("--evaluation-end", default="2025-12-31")
    parser.add_argument("--capital-usd", type=float, default=300_000)
    parser.add_argument("--cost-bps", type=float, default=25,
                        help="P006's registered PRIMARY acceptance cost -- higher than P001-P005's "
                             "10bps because a hot, high-turnover pool's real spreads/impact are "
                             "expected to be worse; 10bps is also reported but only as a diagnostic")
    parser.add_argument("--secondary-cost-bps", type=float, default=10)
    parser.add_argument("--max-issuers", type=int, default=100)
    parser.add_argument("--minimum-trading-days", type=int, default=252)
    parser.add_argument("--minimum-adv-usd", type=float, default=20_000_000)
    parser.add_argument("--adv-window", type=int, default=63)
    parser.add_argument("--short-volume-window", type=int, default=5)
    parser.add_argument("--long-volume-window", type=int, default=60)
    parser.add_argument("--quality-exclude-fraction", type=float, default=0.25)
    parser.add_argument("--drawdown-research-limit", type=float, default=0.50,
                        help="P006's user-set limit, widened from P001-P005's 0.30 because a "
                             "3-5 name concentrated book cannot realistically clear 0.30")
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260913)
    parser.add_argument("--sector-weight-cap", type=float, default=1.0,
                        help="P001-P005 froze 0.30 for 10-20-name diversified books; a single H3 "
                             "position alone is already 1/3=33.3%%, so 0.30 makes H3 structurally "
                             "unable to ever hold anything (found before any real H3 result existed, "
                             "see docs/review/08-decisions-and-coverage.md's 2026-09-14 entry). "
                             "Concentration is this candidate's premise, not a risk to cap against, "
                             "so this runner leaves it uncapped by default.")
    parser.add_argument("--annual-system-cash-cost-usd", type=float, default=828)
    parser.add_argument("--max-workers", type=int, default=None,
                        help="defaults to os.cpu_count() via ProcessPoolExecutor")
    args = parser.parse_args()

    config = vars(args)
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-p006-" + config_hash[:8]
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
        cache_root = data_dir / "derived-cache"
        source_hashes = {Path(a["path"]).name: a["sha256"] for a in manifest["source_artifacts"]}
        code_hashes = {a["name"]: a["sha256"] for a in manifest["code_artifacts"]}

        print("Building security master and trading calendar...", flush=True)
        master = security_master(data_dir / "tickers-bulk-full.csv.zip")
        ticker_info = {info["ticker"]: info for info in master.values()}
        all_days = distinct_trading_days(data_dir / "daily-bulk-full.csv.zip")
        trading_days_sorted = sorted(d for d in all_days if d <= args.evaluation_end)
        months = [d for d in month_end_dates(all_days)
                 if args.universe_start_month <= d[:7] <= args.evaluation_end[:7]]
        print(f"  {len(months)} month-end dates: {months[0]} to {months[-1]}", flush=True)

        print("Screening the whole eligible market for monthly volume-spike pools "
             f"(short={args.short_volume_window}d/long={args.long_volume_window}d, real Sharadar "
             "volume, one pass)...", flush=True)
        hot_key = fingerprint({"stage": "hot_universe",
                               "sources": {k: source_hashes[k] for k in
                                          ("daily-bulk-full.csv.zip", "stocks-bulk-full.csv.zip")},
                               "code": {k: code_hashes[k] for k in ("universe.py",)},
                               "months": months, "max_issuers": args.max_issuers,
                               "minimum_trading_days": args.minimum_trading_days,
                               "minimum_adv_usd": args.minimum_adv_usd, "adv_window": args.adv_window,
                               "short_window": args.short_volume_window,
                               "long_window": args.long_volume_window})
        hot_cache = read_cache(cache_root, hot_key)
        if hot_cache is None:
            universe_diagnostics = build_hot_universe(
                data_dir, master, months, trading_days_sorted, args.max_issuers,
                args.minimum_trading_days, args.minimum_adv_usd, args.adv_window,
                args.short_volume_window, args.long_volume_window)
            write_cache(cache_root, hot_key, {"universe": universe_diagnostics})
        else:
            universe_diagnostics = hot_cache["universe"]
        (run / "universe_diagnostics.json").write_text(json.dumps(universe_diagnostics, indent=2))
        (run / "review_timing.json").write_text(json.dumps([
            {"as_of": result["month_end"], "execution_month": execution_month(result["month_end"])}
            for result in universe_diagnostics], indent=2))

        candidate_union = {t for result in universe_diagnostics for t in result["selected"]}
        candidate_union.add("QQQ")
        print(f"  {len(candidate_union)} distinct tickers were ever selected across all "
             f"{len(months)} months", flush=True)

        print("Building real Sharadar bars for the ever-selected union (parallel)...", flush=True)
        bars_key = fingerprint({"stage": "bars", "sources": {k: source_hashes[k] for k in
                               ("stocks-bulk-full.csv.zip", "actions-bulk-full.csv.zip")},
                               "code": {k: code_hashes[k] for k in ("sharadar_prices.py", "data.py")},
                               "tickers": sorted(candidate_union - {"QQQ"}),
                               "data_start": args.data_start, "data_end": args.evaluation_end})
        bars_cache = read_cache(cache_root, bars_key)
        if bars_cache is None:
            bars, issues, bridge_issues = build_real_bars(
                data_dir, candidate_union - {"QQQ"}, args.data_start, args.evaluation_end, args.max_workers)
            write_cache(cache_root, bars_key, {"bars": bars, "issues": issues, "bridge_issues": bridge_issues})
        else:
            bars, issues, bridge_issues = (bars_cache[k] for k in ("bars", "issues", "bridge_issues"))
        del bars_cache
        manifest["derived_cache_keys"] = {"hot_universe": hot_key, "bars": bars_key}
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
            raise ValueError("Internal price gaps require explicit halt handling; cannot exclude using future data")

        raw_symbols_by_review_month = {
            result["month_end"][:7]: {t: (ticker_info[t]["sector"] or "Unknown") for t in result["selected"]}
            for result in universe_diagnostics
        }

        print(f"Computing real point-in-time quality scores and excluding the bottom "
             f"{args.quality_exclude_fraction:.0%} per month (docs/review/03 section 2, "
             "P006 exclusion registration)...", flush=True)
        quality_details = {}
        build_quality_by_review_month(
            data_dir, candidate_union - {"QQQ"}, master, months, trading_days_sorted,
            raw_symbols_by_review_month, details_output=quality_details)
        excluded_by_month = {
            month: excluded_by_quality_threshold(scores, args.quality_exclude_fraction)
            for month, scores in quality_details.items()
        }
        symbols_by_review_month = {
            month: {t: sector for t, sector in roster.items() if t not in excluded_by_month.get(month, set())}
            for month, roster in raw_symbols_by_review_month.items()
        }
        quality_excluded_counts = {month: len(names) for month, names in excluded_by_month.items()}
        (run / "quality_exclusion_by_month.json").write_text(json.dumps(
            {month: sorted(names) for month, names in excluded_by_month.items()}, indent=2))
        quality_by_review_month = shift_month_end_inputs(quality_details)
        symbols_by_review_month = shift_month_end_inputs(symbols_by_review_month)
        (run / "quality_details.json").write_text(json.dumps(quality_by_review_month, indent=2))

        print("Fetching cash-yield reference (FRED)...", flush=True)
        cash_yield_envelope = download_series("DGS3MO", args.data_start, args.benchmark_data_end,
                                             args.fred_cache_dir, offline=True)
        cash_annual_rate = daily_rate_by_trading_day(normalize_series(cash_yield_envelope), dates)

        print("Simulating (parallel across variants)...", flush=True)
        static_symbols = {t: sector for month in symbols_by_review_month.values() for t, sector in month.items()}
        sim_config = {
            "evaluation_start": args.evaluation_start, "evaluation_end": args.evaluation_end,
            "symbols": static_symbols, "minimum_adv_usd": 0,  # liquidity already screened upstream
            "sector_weight_cap": args.sector_weight_cap, "volatility_target": 0.15,
            "annual_system_cash_cost_usd": args.annual_system_cash_cost_usd,
            "drawdown_research_limit": args.drawdown_research_limit,
        }
        reference, ref_nav = total_return_reference(
            bars["QQQ"], dates, args.evaluation_start, args.evaluation_end, args.capital_usd, args.cost_bps)
        benchmark_returns = daily_returns(ref_nav, args.capital_usd)

        variants = ("QQQ", "H3", "H5")
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
                {t: i["sector"] or "Unknown" for t, i in ticker_info.items()}, quality_by_review_month)
            if variant.startswith("H"):
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

        print(f"Running the {args.secondary_cost_bps:.0f}bps diagnostic-only cost sensitivity "
             "(not the acceptance cost)...", flush=True)
        secondary_cases = [(args.capital_usd, args.secondary_cost_bps,
                           args.annual_system_cash_cost_usd, variant) for variant in ("H3", "H5")]
        with ProcessPoolExecutor(
            max_workers=min(2, args.max_workers or os.cpu_count() or 1),
            initializer=_init_simulate_worker,
            initargs=(bars, dates, sim_config, args.capital_usd, args.cost_bps, cash_annual_rate,
                     symbols_by_review_month, quality_by_review_month),
        ) as pool:
            secondary_summaries = []
            for task, result in pool.map(_simulate_cost_scenario, secondary_cases):
                secondary_summaries.append(result[0])
        (run / "secondary_cost_scenario.json").write_text(json.dumps(secondary_summaries, indent=2, allow_nan=False))

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
                "quality_excluded_counts_by_month": quality_excluded_counts,
                "limitations": ["Action proximity does not certify economic settlement.",
                                "Current exchange/category/sector snapshots remain a PIT limitation.",
                                "SIC reconstructed chains have unresolved discrepancies.",
                                "Options volume was the original hot-pool proxy; ordinary dollar "
                                "volume spike ratio is an unverified substitute.",
                                "No cost-scenario grid across capital levels was run (single "
                                "primary + one diagnostic-only cost point, per registration).",
                                "No corporate-action (spin-off/acquisition) equity accounting layer "
                                "applied here -- last-price forced-exit proxy only, as in P004."]}
        (run / "data_audit.json").write_text(json.dumps(audit, indent=2))
        (run / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
        decision = {
            "experiment_id": "P006-hot-volume-short-momentum", "run_id": run_id,
            "pre_registered": "Volume-spike pool (5d/60d, top 100), 1-month formation, bottom-25% "
                             "quality exclusion, H3/H5 concentrated equal-weight, primary cost 25bps, "
                             "drawdown research limit 0.50 -- all fixed before this ran; see "
                             "docs/review/08-decisions-and-coverage.md's P006 entry.",
            "investment_decision": "insufficient_evidence",
            "engineering_decision": "completed_with_explicit_data_gaps",
            "data_gate_pass": audit["data_gate_pass"],
            "joint_sample_pass_variants": [r["variant"] for r in results if r.get("sample_joint_pass")],
            "acceptance_blockers": ["Unresolved corporate-action/exit and historical metadata gates",
                                   "No multiple-comparison correction applied across the P001-P006 "
                                   "candidate sequence"],
            "action_bridge_discrepancies": len(bridge_issues),
        }
        (run / "decision.json").write_text(json.dumps(decision, indent=2))
        for artifact in manifest["source_artifacts"]:
            if sha256_file(artifact["path"]) != artifact["sha256"]:
                raise ValueError("Pinned source changed during research run")
        manifest.update(status="completed", output_artifacts=[
            {"path": str(p.relative_to(run)), "sha256": sha256_file(p)}
            for p in sorted(run.rglob("*")) if p.is_file() and p.name != "manifest.json"])
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
        register_run(args.registry_path, {"experiment_id": "P006-hot-volume-short-momentum",
                     "run_id": run_id, "status": "failed", "config_sha256": config_hash,
                     "error": manifest["error"]})
        traceback.print_exc()
        print(manifest["error"], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
