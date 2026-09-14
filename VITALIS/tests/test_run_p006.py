"""build_hot_universe(): real-data proof only (tightly coupled to the real
bulk stocks/daily/tickers files; the underlying primitives -- universe.py's
monthly_hot_universe()/load_dollar_volume() -- already have their own
synthetic unit tests in tests/test_universe.py)."""

import unittest
from pathlib import Path

from vitalis.run_p006 import build_hot_universe
from vitalis.universe import distinct_trading_days, month_end_dates, security_master


class BuildHotUniverseTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = Path("data/authorized/sharadar")
        required = ["tickers-bulk-full.csv.zip", "daily-bulk-full.csv.zip", "stocks-bulk-full.csv.zip"]
        if not all((self.data_dir / name).exists() for name in required):
            self.skipTest("no local authorized Sharadar bulk cache present")

    def test_real_hot_pool_is_sane_and_distinct_from_a_market_cap_pool(self):
        master = security_master(self.data_dir / "tickers-bulk-full.csv.zip")
        all_days = distinct_trading_days(self.data_dir / "daily-bulk-full.csv.zip")
        trading_days_sorted = sorted(d for d in all_days if d <= "2020-06-30")
        months = [d for d in month_end_dates(all_days) if d[:7] == "2020-03"]

        results = build_hot_universe(self.data_dir, master, months, trading_days_sorted,
                                     max_issuers=50, minimum_trading_days=252,
                                     minimum_adv_usd=20_000_000, adv_window=63,
                                     short_window=5, long_window=60)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result["month_end"], months[0])
        self.assertGreater(len(result["selected"]), 0)
        self.assertLessEqual(len(result["selected"]), 50)
        # No padding: never claim more names than the real screen produced.
        self.assertEqual(result["waterfall"]["selected"], len(result["selected"]))
        for ticker in result["selected"]:
            self.assertGreater(result["spike_ratio"][ticker], 0)
        # 2020-03-31 is the depth of the COVID selloff -- real volume spiked
        # broadly, so this month's pool should not be dominated by the
        # largest-ever mega caps the stopped market-cap line always picked.
        self.assertNotIn("AAPL", result["selected"][:5])


class FixedFeeCashMarginRealDataTests(unittest.TestCase):
    """Real-data regression for a genuine P006 crash: H5 (25bps, 5 names)
    ran cash to -$2.05 on 2009-06-09, a non-rebalance day, after roughly
    4.5 years of compounding drawdown left its turnover-cost margin with no
    slack for the fixed system fee accruing between rebalances. Fixed in
    engine.simulate() by reserving a worst-case month of that fee at every
    rebalance (see its comment for why a 12-months-average reserve is not
    enough on its own). A small synthetic reproduction was not pursued: the
    failure took years of real compounding drift to surface, so the real
    21-year run is the actual regression proof, not an approximation of it.
    """

    def setUp(self):
        self.data_dir = Path("data/authorized/sharadar")
        required = ["tickers-bulk-full.csv.zip", "daily-bulk-full.csv.zip", "stocks-bulk-full.csv.zip",
                   "actions-bulk-full.csv.zip", "fundamentals-bulk-full.csv.zip"]
        if not all((self.data_dir / name).exists() for name in required):
            self.skipTest("no local authorized Sharadar bulk cache present")
        cache_root = self.data_dir / "derived-cache"
        if not any(cache_root.glob("*.json.gz")) if cache_root.exists() else True:
            self.skipTest("no warmed derived-cache present; run vitalis.run_p006 once first "
                          "(this test only re-derives state from that cache, it does not build it)")

    def test_h5_runs_the_full_real_evaluation_window_without_negative_cash(self):
        import tempfile
        from vitalis.data import download, fingerprint, normalize
        from vitalis.local_cache import read_cache
        from vitalis.engine import simulate
        from vitalis.macro import daily_rate_by_trading_day, download_series, normalize_series
        from vitalis.quality import excluded_by_quality_threshold
        from vitalis.run_pit import build_quality_by_review_month
        from vitalis.research_audit import pin_inputs, shift_month_end_inputs
        from vitalis.sharadar_prices import find_gap_free_tickers
        from vitalis.universe import distinct_trading_days, month_end_dates, security_master

        data_dir, cache_dir, fred_cache_dir = self.data_dir, "data/public-yahoo", "data/public-fred"
        benchmark_data_end, data_start = "2026-09-13", "2004-01-01"
        universe_start_month, evaluation_start, evaluation_end = "2004-06", "2005-01-03", "2025-12-31"

        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            input_paths = [data_dir / f"{name}-bulk-full.csv.zip" for name in
                          ("tickers", "daily", "stocks", "actions", "fundamentals", "descriptions")]
            input_paths += [Path(cache_dir) / f"QQQ-{data_start}-{benchmark_data_end}.json",
                            Path(fred_cache_dir) / f"DGS3MO-{data_start}-{benchmark_data_end}.json"]
            if not all(p.exists() for p in input_paths[-2:]):
                self.skipTest("QQQ/FRED offline caches not warmed yet")
            manifest = pin_inputs(run, input_paths, "data/catalog.sqlite")
            source_hashes = {Path(a["path"]).name: a["sha256"] for a in manifest["source_artifacts"]}
            code_hashes = {a["name"]: a["sha256"] for a in manifest["code_artifacts"]}

            master = security_master(data_dir / "tickers-bulk-full.csv.zip")
            ticker_info = {info["ticker"]: info for info in master.values()}
            all_days = distinct_trading_days(data_dir / "daily-bulk-full.csv.zip")
            trading_days_sorted = sorted(d for d in all_days if d <= evaluation_end)
            months = [d for d in month_end_dates(all_days)
                     if universe_start_month <= d[:7] <= evaluation_end[:7]]

            cache_root = data_dir / "derived-cache"
            hot_key = fingerprint({"stage": "hot_universe",
                                   "sources": {k: source_hashes[k] for k in
                                              ("daily-bulk-full.csv.zip", "stocks-bulk-full.csv.zip")},
                                   "code": {k: code_hashes[k] for k in ("universe.py",)},
                                   "months": months, "max_issuers": 100, "minimum_trading_days": 252,
                                   "minimum_adv_usd": 20_000_000, "adv_window": 63,
                                   "short_window": 5, "long_window": 60})
            hot_cache = read_cache(cache_root, hot_key)
            if hot_cache is None:
                self.skipTest("hot_universe derived-cache miss; run vitalis.run_p006 once first")
            universe_diagnostics = hot_cache["universe"]
            candidate_union = {t for r in universe_diagnostics for t in r["selected"]}
            candidate_union.add("QQQ")
            bars_key = fingerprint({"stage": "bars", "sources": {k: source_hashes[k] for k in
                                   ("stocks-bulk-full.csv.zip", "actions-bulk-full.csv.zip")},
                                   "code": {k: code_hashes[k] for k in ("sharadar_prices.py", "data.py")},
                                   "tickers": sorted(candidate_union - {"QQQ"}),
                                   "data_start": data_start, "data_end": evaluation_end})
            bars_cache = read_cache(cache_root, bars_key)
            if bars_cache is None:
                self.skipTest("bars derived-cache miss; run vitalis.run_p006 once first")
            bars, issues, bridge_issues = (bars_cache[k] for k in ("bars", "issues", "bridge_issues"))

            qqq_envelope = download("QQQ", data_start, benchmark_data_end, cache_dir, offline=True)
            bars["QQQ"], _ = normalize(qqq_envelope)
            dates = sorted(bars["QQQ"])
            gap_free, gaps = find_gap_free_tickers({t: b for t, b in bars.items() if t != "QQQ"}, dates)
            self.assertFalse(gaps)

            raw_symbols_by_review_month = {
                result["month_end"][:7]: {t: (ticker_info[t]["sector"] or "Unknown") for t in result["selected"]}
                for result in universe_diagnostics
            }
            quality_details = {}
            build_quality_by_review_month(data_dir, candidate_union - {"QQQ"}, master, months,
                                          trading_days_sorted, raw_symbols_by_review_month,
                                          details_output=quality_details)
            excluded_by_month = {m: excluded_by_quality_threshold(s, 0.25) for m, s in quality_details.items()}
            symbols_by_review_month = {
                m: {t: sec for t, sec in roster.items() if t not in excluded_by_month.get(m, set())}
                for m, roster in raw_symbols_by_review_month.items()
            }
            quality_by_review_month = shift_month_end_inputs(quality_details)
            symbols_by_review_month = shift_month_end_inputs(symbols_by_review_month)

            cash_yield_envelope = download_series("DGS3MO", data_start, benchmark_data_end,
                                                  fred_cache_dir, offline=True)
            cash_annual_rate = daily_rate_by_trading_day(normalize_series(cash_yield_envelope), dates)
            static_symbols = {t: s for m in symbols_by_review_month.values() for t, s in m.items()}
            sim_config = {"evaluation_start": evaluation_start, "evaluation_end": evaluation_end,
                         "symbols": static_symbols, "minimum_adv_usd": 0, "sector_weight_cap": 0.30,
                         "volatility_target": 0.15, "annual_system_cash_cost_usd": 828,
                         "drawdown_research_limit": 0.50}
            summary, nav, *_ = simulate(bars, dates, sim_config, 300000, 25, "H5",
                                        cash_annual_rate=cash_annual_rate,
                                        symbols_by_review_month=symbols_by_review_month,
                                        quality_by_review_month=quality_by_review_month)
            self.assertTrue(all(row["cash_usd"] >= -1e-6 for row in nav))


if __name__ == "__main__":
    unittest.main()
