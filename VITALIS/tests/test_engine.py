"""Meaningful accounting and causality checks; all fixtures are synthetic."""

import copy
import unittest
from datetime import date, timedelta

from vitalis.data import normalize
from vitalis.engine import choose, downside_capture_ratio, metrics, percentile, rank_signals, simulate


class EngineTests(unittest.TestCase):
    def config(self):
        return {"evaluation_start": "2025-01-02", "evaluation_end": "2025-01-06",
                "symbols": {"A": "x"}, "minimum_adv_usd": 0,
                "sector_weight_cap": 0.3, "volatility_target": 0.15,
                "annual_system_cash_cost_usd": 0}

    def test_split_and_dividend_preserve_real_wealth(self):
        dates = ["2024-12-31", "2025-01-02", "2025-01-03", "2025-01-06"]
        series = {d: {"open": 100, "close": 100, "split": 1,
                      "dividend": 0, "adjclose": 100, "dollar_volume": 1e8} for d in dates}
        series["2025-01-03"].update(open=50, close=50, split=2)
        series["2025-01-06"].update(open=49, close=49, dividend=1)
        summary, nav, trades, holdings, *_ = simulate({"QQQ": series}, dates, self.config(), 1000, 0, "QQQ")
        self.assertEqual([r["nav_usd"] for r in nav], [1000, 1000, 1000])
        self.assertEqual(summary["dividends_usd"], 20)
        self.assertEqual(holdings[-1]["quantity"], 20)
        self.assertEqual(trades[0]["signal_date"], "2024-12-31")

    def test_next_open_and_cost_are_not_same_close(self):
        dates = ["2024-12-31", "2025-01-02"]
        series = {d: {"open": 100, "close": 110, "split": 1, "dividend": 0,
                      "adjclose": 110, "dollar_volume": 1e8} for d in dates}
        config = self.config()
        config["evaluation_end"] = "2025-01-02"
        summary, nav, trades, *_ = simulate({"QQQ": series}, dates, config, 1000, 10, "QQQ")
        self.assertEqual(trades[0]["price_usd"], 100)
        self.assertEqual(trades[0]["quantity"], 9)
        self.assertAlmostEqual(summary["execution_cost_usd"], 0.9)
        self.assertAlmostEqual(nav[0]["cash_usd"], 99.1)
        self.assertAlmostEqual(nav[0]["nav_usd"], 1089.1)

    def test_ranking_ignores_future_prices(self):
        dates = [f"session-{i:03}" for i in range(270)]
        bars = {s: {d: {"adjclose": 100 + i * slope, "dollar_volume": 1e8}
                    for i, d in enumerate(dates)} for s, slope in (("A", 1), ("B", 0.5))}
        before = rank_signals(bars, dates, 252, bars, 0)
        changed = copy.deepcopy(bars)
        for d in dates[253:]:
            changed["B"][d]["adjclose"] = 1e9
        self.assertEqual(before, rank_signals(changed, dates, 252, changed, 0))
        self.assertEqual(before[0]["symbol"], "A")

    def test_quality_blend_can_reorder_ranking_per_03_section_2_formula(self):
        dates = [f"session-{i:03}" for i in range(270)]
        # A best momentum, B middle, C worst (momentum-only order: A, B, C).
        bars = {s: {d: {"adjclose": 100 + i * slope, "dollar_volume": 1e8}
                    for i, d in enumerate(dates)} for s, slope in (("A", 3), ("B", 2), ("C", 1))}
        momentum_only = rank_signals(bars, dates, 252, bars, 0)
        self.assertEqual([r["symbol"] for r in momentum_only], ["A", "B", "C"])
        # Total Score = 0.5*momentum + 0.5*quality (docs/review/03 section 2):
        # A=0.5*1.0+0.5*0.0=0.5, B=0.5*0.5+0.5*1.0=0.75, C=0.5*0.0+0.5*0.3=0.15
        # -> order flips to B, A, C.
        quality = {"A": 0.0, "B": 1.0, "C": 0.3}
        blended = rank_signals(bars, dates, 252, bars, 0, quality_by_symbol=quality)
        self.assertEqual([r["symbol"] for r in blended], ["B", "A", "C"])
        scores = {r["symbol"]: r["score"] for r in blended}
        self.assertAlmostEqual(scores["A"], 0.5)
        self.assertAlmostEqual(scores["B"], 0.75)
        self.assertAlmostEqual(scores["C"], 0.15)
        momentum_scores = {r["symbol"]: r["momentum_score"] for r in blended}
        self.assertAlmostEqual(momentum_scores["A"], 1.0)

    def test_quality_missing_for_a_symbol_defaults_to_neutral_not_exclusion(self):
        dates = [f"session-{i:03}" for i in range(270)]
        bars = {s: {d: {"adjclose": 100 + i * slope, "dollar_volume": 1e8}
                    for i, d in enumerate(dates)} for s, slope in (("A", 2), ("B", 1))}
        quality = {"A": 0.0}  # B is momentum-eligible but missing from the quality dict
        result = rank_signals(bars, dates, 252, bars, 0, quality_by_symbol=quality)
        self.assertEqual({r["symbol"] for r in result}, {"A", "B"})  # neither excluded
        scores = {r["symbol"]: r["score"] for r in result}
        self.assertAlmostEqual(scores["B"], 0.5 * 0.0 + 0.5 * 0.5)  # neutral 0.5, matching quality.py's own fallback

    def test_variant_q10_uses_quality_blend_q_variants_get_top_10_slots(self):
        from datetime import date, timedelta
        start = date(2019, 1, 1)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(280)]
        # Momentum-only order is A, B, C (slopes 3, 2, 1); with a big enough
        # quality gap for B, the blended order should become B, A, C -- with
        # exactly 2 candidates a full [0,1] momentum swing can never be
        # overcome by an equally-capped [0,1] quality score at 50/50 weight,
        # so this needs 3 to actually flip anything (see the equivalent
        # rank_signals()-level test above for the arithmetic).
        bars = {s: {d: {"open": p, "close": p, "adjclose": p, "dollar_volume": 1e8,
                        "split": 1, "dividend": 0}
                    for d, p in zip(dates, prices)}
                for s, prices in (("A", [100 + 3 * i for i in range(280)]),
                                  ("B", [100 + 2 * i for i in range(280)]),
                                  ("C", [100 + 1 * i for i in range(280)]))}
        config = {"evaluation_start": dates[260], "evaluation_end": dates[260],
                 "symbols": {"A": "x", "B": "x", "C": "x"}, "minimum_adv_usd": 0,
                 "sector_weight_cap": 1.0, "volatility_target": 0.15,
                 "annual_system_cash_cost_usd": 0}
        quality_by_month = {dates[260][:7]: {"A": 0.0, "B": 1.0, "C": 0.3}}
        _, _, _, _, decisions_q, *_ = simulate(
            bars, dates, config, 100_000, 0, "Q10", quality_by_review_month=quality_by_month)
        # All three get bought (3 candidates for 10 slots either way), but the
        # ranking inside Q10's decisions.json should show B outranking A once
        # quality is blended in, unlike a momentum-only ranking.
        ranks_q = {r["symbol"]: r["rank"] for r in decisions_q[0]["ranking"]}
        self.assertLess(ranks_q["B"], ranks_q["A"])

    def test_hysteresis_and_sector_cap_leave_cash(self):
        ranking = [{"symbol": s, "rank": i + 1} for i, s in enumerate("ABCDEF")]
        sectors = {s: "x" for s in "ABCDEF"}
        self.assertEqual(choose(ranking, ["D"], 2, sectors, 0.5), ["D"])

    def test_a_sector_cap_below_one_over_count_makes_every_slot_unfillable(self):
        """Regression: P006's H3 (count=3) ran real 21-year data 100% in cash
        for every one of 251 review months -- 1/3=33.3% alone already exceeds
        the 30% sector cap inherited from P001-P005's 10/20-name books, so
        the very first entrant in choose()'s loop is rejected regardless of
        which sector it's in, every single time. Found before any real H3
        result existed (see docs/review/08, 2026-09-14): a single position's
        weight alone breaching the cap is a config/count mismatch, not a
        diversification finding, and count-based concentration already IS
        the diversification control for a 3-5 name book -- stacking an
        incompatible sector cap on top doesn't add real risk control, it
        just makes the variant unable to ever hold anything.
        """
        ranking = [{"symbol": s, "rank": i + 1} for i, s in enumerate("ABC")]
        sectors = {s: "distinct-sector-" + s for s in "ABC"}  # not a sector-concentration issue
        self.assertEqual(choose(ranking, [], 3, sectors, 0.30), [])
        self.assertEqual(choose(ranking, [], 3, sectors, 1.0), ["A", "B", "C"])

    def test_percentile_ties_use_average_rank(self):
        self.assertEqual(percentile({"A": 1, "B": 1, "C": 2}), {"A": 0.25, "B": 0.25, "C": 1.0})

    def test_cash_interest_accrues_on_beginning_of_day_balance(self):
        dates = ["2024-12-31", "2025-01-02", "2025-01-03"]
        series = {d: {"open": 100, "close": 100, "split": 1, "dividend": 0,
                      "adjclose": 100, "dollar_volume": 1e8} for d in dates}
        config = self.config()
        config["evaluation_end"] = "2025-01-03"
        # index-1 stays below the 63-session risk_fraction warmup, so the risk overlay
        # holds 100% cash throughout: interest is isolated from any price/trading effect.
        rates = {"2025-01-02": 0.0, "2025-01-03": 0.05}
        summary, nav, trades, *_ = simulate(
            {"QQQ": series}, dates, config, 1000, 0, "QQQ-cash15", cash_annual_rate=rates)
        expected_day2_interest = 1000 * 0.05 / 252
        self.assertEqual(trades, [])
        self.assertEqual(nav[0]["cash_interest_usd"], 0.0)
        self.assertAlmostEqual(nav[1]["cash_interest_usd"], expected_day2_interest)
        self.assertAlmostEqual(nav[1]["nav_usd"], 1000 + expected_day2_interest)
        self.assertAlmostEqual(summary["cash_interest_usd"], expected_day2_interest)

    def test_missing_cash_rate_defaults_to_zero_interest(self):
        dates = ["2024-12-31", "2025-01-02"]
        series = {d: {"open": 100, "close": 100, "split": 1, "dividend": 0,
                      "adjclose": 100, "dollar_volume": 1e8} for d in dates}
        config = self.config()
        config["evaluation_end"] = "2025-01-02"
        summary, nav, *_ = simulate({"QQQ": series}, dates, config, 1000, 0, "QQQ")
        self.assertEqual(nav[0]["cash_interest_usd"], 0.0)
        self.assertEqual(summary["cash_interest_usd"], 0.0)

    def test_sortino_and_calmar_are_undefined_without_downside_or_drawdown(self):
        nav = [{"date": f"2025-01-{i:02}", "nav_usd": 1000 * (1.01 ** i)} for i in range(1, 6)]
        result = metrics(nav, 1000)
        self.assertIsNone(result["sortino_zero_target"])  # no session below the zero target
        self.assertIsNone(result["calmar_ratio"])  # max_drawdown is exactly 0

    def test_calmar_and_worst_quarter_with_a_single_drawdown_day(self):
        returns = [-0.10] + [0.0] * 251
        day, nav_value, rows = date(2021, 1, 4), 1000.0, []
        for r in returns:
            nav_value *= (1 + r)
            rows.append({"date": day.isoformat(), "nav_usd": nav_value})
            day += timedelta(days=1)
        result = metrics(rows, 1000.0)
        self.assertAlmostEqual(result["max_drawdown"], -0.10)
        self.assertAlmostEqual(result["cagr"], -0.10)
        self.assertAlmostEqual(result["calmar_ratio"], -1.0)
        self.assertAlmostEqual(result["worst_quarter"], -0.10)
        self.assertEqual(result["hit_rate_positive_sessions"], 0.0)

    def test_downside_capture_ratio_uses_compounded_benchmark_down_days(self):
        strategy = [0.02, -0.01, -0.03, 0.01]
        benchmark = [0.01, -0.02, -0.01, 0.03]
        expected = ((1 - 0.01) * (1 - 0.03) - 1) / ((1 - 0.02) * (1 - 0.01) - 1)
        self.assertAlmostEqual(downside_capture_ratio(strategy, benchmark), expected)

    def test_downside_capture_ratio_is_none_without_benchmark_down_days(self):
        self.assertIsNone(downside_capture_ratio([0.01, 0.02], [0.01, 0.02]))

    def test_symbols_by_review_month_drops_a_name_that_leaves_the_real_universe(self):
        from datetime import date, timedelta
        start = date(2019, 1, 1)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(400)]
        # Two symbols, both trending up so both always qualify; A always
        # ranks above B on momentum, so a fixed-universe run would keep A.
        bars = {
            "A": {d: {"open": 100 + i, "close": 100 + i, "adjclose": 100 + i,
                      "dollar_volume": 1e8, "split": 1, "dividend": 0} for i, d in enumerate(dates)},
            "B": {d: {"open": 50 + 0.1 * i, "close": 50 + 0.1 * i, "adjclose": 50 + 0.1 * i,
                      "dollar_volume": 1e8, "split": 1, "dividend": 0} for i, d in enumerate(dates)},
        }
        eval_start, eval_end = dates[280], dates[300]
        config = {"evaluation_start": eval_start, "evaluation_end": eval_end,
                 "symbols": {"A": "x", "B": "x"}, "minimum_adv_usd": 0,
                 "sector_weight_cap": 1.0, "volatility_target": 0.15,
                 "annual_system_cash_cost_usd": 0}
        review_month = eval_start[:7]
        # Real point-in-time universe for that month excludes A entirely,
        # even though it would win on momentum in a fixed-universe run.
        symbols_by_review_month = {review_month: {"B": "x"}}
        summary, nav, trades, holdings, *_ = simulate(
            bars, dates, config, 1000, 0, "M10", symbols_by_review_month=symbols_by_review_month)
        held_symbols = {h["symbol"] for h in holdings}
        self.assertEqual(held_symbols, {"B"})
        self.assertNotIn("A", {t["symbol"] for t in trades})

        with self.assertRaisesRegex(ValueError, 'Missing point-in-time universe'):
            simulate(bars, dates, config, 1000, 0, "M10", symbols_by_review_month={})

        # Regression: modifying the current month's future roster cannot
        # change its initial execution based on the preceding month-end.
        from vitalis.research_audit import execution_month, shift_month_end_inputs
        prior_month = dates[250][:7]
        self.assertEqual(execution_month(prior_month + '-01'), review_month)
        raw = {prior_month: {"B": "x"}, review_month: {"A": "x"}}
        result = simulate(bars, dates, config, 1000, 0, "M10",
                          symbols_by_review_month=shift_month_end_inputs(raw))
        self.assertEqual({h['symbol'] for h in result[3]}, {'B'})
        raw[review_month] = {"FUTURE": "x"}
        changed = simulate(bars, dates, config, 1000, 0, "M10",
                           symbols_by_review_month=shift_month_end_inputs(raw))
        self.assertEqual(result, changed)

    def test_symbols_by_review_month_omitted_matches_prior_static_behavior(self):
        from datetime import date, timedelta
        start = date(2019, 1, 1)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(400)]
        bars = {
            "A": {d: {"open": 100 + i, "close": 100 + i, "adjclose": 100 + i,
                      "dollar_volume": 1e8, "split": 1, "dividend": 0} for i, d in enumerate(dates)},
            "B": {d: {"open": 50 + 0.1 * i, "close": 50 + 0.1 * i, "adjclose": 50 + 0.1 * i,
                      "dollar_volume": 1e8, "split": 1, "dividend": 0} for i, d in enumerate(dates)},
        }
        eval_start, eval_end = dates[280], dates[300]
        config = {"evaluation_start": eval_start, "evaluation_end": eval_end,
                 "symbols": {"A": "x", "B": "x"}, "minimum_adv_usd": 0,
                 "sector_weight_cap": 1.0, "volatility_target": 0.15,
                 "annual_system_cash_cost_usd": 0}
        with_none, without_param = (
            simulate(bars, dates, config, 1000, 0, "M10", symbols_by_review_month=None),
            simulate(bars, dates, config, 1000, 0, "M10"),
        )
        self.assertEqual(with_none[0], without_param[0])

    def test_missing_next_open_leaves_cash_and_does_not_replace_selected_name(self):
        from datetime import date, timedelta
        dates = [(date(2019, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)]
        series = {d: {"open": 100+i, "close": 100+i, "adjclose": 100+i,
                      "dollar_volume": 1e8, "split": 1, "dividend": 0} for i,d in enumerate(dates)}
        execution = dates[280]
        bars = {"A": {d:b for d,b in series.items() if d < execution}, "B": series}
        config = {"evaluation_start": execution, "evaluation_end": execution,
                  "symbols": {"A":"x", "B":"x"}, "minimum_adv_usd":0,
                  "sector_weight_cap":1, "volatility_target":.15, "annual_system_cash_cost_usd":0}
        result = simulate(bars, dates, config, 100000, 0, "M10")
        self.assertIn('A', result[4][0]['selected'])
        self.assertEqual(result[4][0]['unfilled_target_symbols'], ['A'])
        self.assertNotIn('A', {r['symbol'] for r in result[2]})
        self.assertGreater(result[1][0]['cash_usd'] / result[1][0]['nav_usd'], .89)
        self.assertTrue(any(r['flag']=='unfilled_order_no_execution_bar' for r in result[5]))

    def test_delisted_holding_is_settled_at_last_known_price_not_a_crash(self):
        from datetime import date, timedelta
        start = date(2019, 1, 1)
        all_dates = [(start + timedelta(days=i)).isoformat() for i in range(400)]
        # A and B both trend up so both qualify and both get selected (only
        # 2 candidates, M10's count=10 has no reason to exclude either).
        full_series = lambda base, slope: {d: {"open": base + slope * i, "close": base + slope * i,
                                                "adjclose": base + slope * i, "dollar_volume": 1e8,
                                                "split": 1, "dividend": 0} for i, d in enumerate(all_dates)}
        bars = {"A": full_series(100, 1), "B": full_series(50, 0.5)}
        eval_start = all_dates[280]
        delist_index = 290  # inside the evaluation window
        last_trading_day = all_dates[delist_index - 1]
        # A's data simply ends -- as if delisted/acquired -- from delist_index on.
        dates_for_sim = all_dates  # engine's own `dates` calendar keeps going
        del_bars_a = {d: b for d, b in bars["A"].items() if d < all_dates[delist_index]}
        bars_with_delisting = {"A": del_bars_a, "B": bars["B"]}
        config = {"evaluation_start": eval_start, "evaluation_end": all_dates[300],
                 "symbols": {"A": "x", "B": "x"}, "minimum_adv_usd": 0,
                 "sector_weight_cap": 1.0, "volatility_target": 0.15,
                 "annual_system_cash_cost_usd": 0}
        summary, nav, trades, holdings, decisions, warnings, contributions = simulate(
            bars_with_delisting, dates_for_sim, config, 100_000, 0, "M10")
        forced = [w for w in warnings if w["flag"] == "forced_exit_data_discontinued"]
        self.assertEqual(len(forced), 1)
        self.assertEqual(forced[0]["symbol"], "A")
        self.assertEqual(forced[0]["last_known_date"], last_trading_day)
        self.assertAlmostEqual(forced[0]["last_price_usd"], del_bars_a[last_trading_day]["close"])
        # B keeps trading normally through the end of the window.
        held_at_end = {h["symbol"] for h in holdings if h["date"] == all_dates[300]}
        self.assertEqual(held_at_end, {"B"})
        # No PNL distortion: the day of forced exit has zero net gain/loss
        # attributable to A beyond what was already marked the prior day.
        exit_day_ledger = next(r for r in nav if r["date"] == all_dates[delist_index])
        self.assertAlmostEqual(exit_day_ledger["pnl_usd"],
                               exit_day_ledger["price_pnl_usd"] + exit_day_ledger["dividend_cash_usd"]
                               + exit_day_ledger["cash_interest_usd"] - exit_day_ledger["execution_cost_usd"]
                               - exit_day_ledger["fixed_fee_usd"])

    def test_provider_split_units_reconstruct_nominal_prices(self):
        payload = {"chart": {"result": [{"meta": {"currency": "USD"},
                    "timestamp": [1735830000, 1735916400],
                    "events": {"splits": {"x": {"date": 1735916400, "numerator": 2, "denominator": 1}}},
                    "indicators": {"quote": [{"open": [50, 50], "close": [50, 50], "volume": [200, 200]}],
                                   "adjclose": [{"adjclose": [50, 50]}]}}]}}
        bars, _ = normalize({"symbol": "A", "payload": payload})
        first, second = sorted(bars)
        self.assertEqual(bars[first]["open"], 100)
        self.assertEqual(bars[second]["split"], 2)
        self.assertEqual(bars[second]["open"], 50)


class ShortHorizonFormationTests(unittest.TestCase):
    """P006's 1-month formation window (docs/review/08, P006 entry)."""

    def _bars(self):
        from datetime import date, timedelta
        dates = [(date(2019, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)]
        # STEADY climbs all year then goes flat for the last month; LATE is flat
        # all year then jumps in the last month. 12-1/6-1 (which skips the most
        # recent month) must prefer STEADY; a plain trailing-21-session window
        # must prefer LATE. That makes the window choice, not noise, decide.
        def bar(price):
            return {"open": price, "close": price, "adjclose": price,
                    "dollar_volume": 1e9, "split": 1, "dividend": 0}
        steady, late = {}, {}
        for i, day in enumerate(dates):
            steady[day] = bar(100 + i if i < len(dates) - 21 else 100 + (len(dates) - 22))
            late[day] = bar(100 if i < len(dates) - 21 else 100 + 5 * (i - (len(dates) - 22)))
        return {"STEADY": steady, "LATE": late}, dates

    def test_one_month_window_reorders_against_the_twelve_month_default(self):
        bars, dates = self._bars()
        index = len(dates) - 1
        symbols = {"STEADY": "x", "LATE": "x"}
        default = rank_signals(bars, dates, index, symbols, 0)
        short = rank_signals(bars, dates, index, symbols, 0, formation="1m")
        self.assertEqual(default[0]["symbol"], "STEADY")
        self.assertEqual(short[0]["symbol"], "LATE")
        # The 1m rows carry the single registered window, not the blend.
        self.assertIn("m1", short[0])
        self.assertNotIn("m12_1", short[0])

    def test_one_month_window_keeps_the_252_session_history_requirement(self):
        bars, dates = self._bars()
        # A shorter formation must not silently admit names with under a year
        # of history -- the eligible pool is meant to be unchanged.
        self.assertEqual(rank_signals(bars, dates, 251, {"STEADY": "x"}, 0, formation="1m"), [])

    def test_h3_and_h5_take_three_and_five_slots_on_the_short_window(self):
        from datetime import date, timedelta
        dates = [(date(2019, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)]
        bars = {}
        for n in range(8):
            series = {}
            for i, day in enumerate(dates):
                price = 100 + (n * i / 100)
                series[day] = {"open": price, "close": price, "adjclose": price,
                               "dollar_volume": 1e9, "split": 1, "dividend": 0}
            bars[f"S{n}"] = series
        config = {"evaluation_start": dates[260], "evaluation_end": dates[299],
                  "symbols": {f"S{n}": "x" for n in range(8)}, "minimum_adv_usd": 0,
                  "sector_weight_cap": 1, "volatility_target": .15,
                  "annual_system_cash_cost_usd": 0}
        for variant, expected in (("H3", 3), ("H5", 5)):
            result = simulate(bars, dates, config, 500000, 0, variant)
            self.assertEqual(len(result[4][0]["selected"]), expected, variant)

    def test_h3s_and_h5s_take_three_and_five_slots_on_the_sharpe_ranking(self):
        from datetime import date, timedelta
        dates = [(date(2019, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)]
        bars = {}
        for n in range(8):
            series = {}
            for i, day in enumerate(dates):
                price = 100 + (n * i / 100)
                series[day] = {"open": price, "close": price, "adjclose": price,
                               "dollar_volume": 1e9, "split": 1, "dividend": 0}
            bars[f"S{n}"] = series
        config = {"evaluation_start": dates[260], "evaluation_end": dates[299],
                  "symbols": {f"S{n}": "x" for n in range(8)}, "minimum_adv_usd": 0,
                  "sector_weight_cap": 1, "volatility_target": .15,
                  "annual_system_cash_cost_usd": 0}
        for variant, expected in (("H3S", 3), ("H5S", 5)):
            result = simulate(bars, dates, config, 500000, 0, variant)
            self.assertEqual(len(result[4][0]["selected"]), expected, variant)


class NearRuinFixedFeeTests(unittest.TestCase):
    """Regression: P006's H3 (unconstrained, 3-name, no risk control) fell
    from real $300,000 to real $2.13 over 18 real years -- genuine
    catastrophic capital destruction, not a bug. Once NAV is that close to
    zero, the flat per-session dollar fee can exceed the cash actually left
    in the account, and there is nothing left to collect it from; a fund
    that reaches exactly zero (no cash, no holdings) must then stay there
    rather than crash on the next session's turnover/return arithmetic.
    """

    def test_fixed_fee_never_exceeds_cash_and_a_ruined_fund_stays_at_zero(self):
        from datetime import date, timedelta
        start = date(2019, 1, 1)
        all_dates = [(start + timedelta(days=i)).isoformat() for i in range(700)]
        # Three names (matching H3's count=3, so the book is fully invested,
        # not cushioned by unused cash) crash at staggered offsets so the
        # last one keeps falling well past when the first two hit near-zero.
        def crash_series(offset):
            prices = ([100.0] * (300 + offset) +
                     [max(0.01, 100.0 * 0.9 ** i) for i in range(400 - offset)])
            return {d: {"open": p, "close": p, "adjclose": p, "dollar_volume": 1e9,
                       "split": 1, "dividend": 0} for d, p in zip(all_dates, prices)}
        bars = {f"S{i}": crash_series(i * 5) for i in range(3)}
        config = {"evaluation_start": all_dates[280], "evaluation_end": all_dates[-1],
                 "symbols": {f"S{i}": "x" for i in range(3)}, "minimum_adv_usd": 0,
                 "sector_weight_cap": 1.0, "volatility_target": 0.15,
                 "annual_system_cash_cost_usd": 828}
        summary, nav, *_ = simulate(bars, all_dates, config, 1_000, 0, "H3")
        self.assertTrue(all(row["cash_usd"] >= -1e-6 for row in nav))
        self.assertEqual(nav[-1]["nav_usd"], 0.0)
        # The fee actually collected once cash ran thin must be less than
        # the nominal daily fee, not silently waived to zero or paid from
        # nowhere -- and cash must land at exactly zero, not go negative.
        thin_days = [r for r in nav if 0 < r["fixed_fee_usd"] < 828 / 252 - 1e-9]
        self.assertTrue(thin_days)
        for row in thin_days:
            self.assertEqual(row["cash_usd"], 0.0)
        self.assertEqual(summary["cagr"], -1.0)


class SharpeFormationTests(unittest.TestCase):
    """P007's Sharpe-ranked 1-month window (docs/review/08, 2026-09-16 P007 entry)."""

    def _bars(self):
        from datetime import date, timedelta
        dates = [(date(2019, 1, 1) + timedelta(days=i)).isoformat() for i in range(300)]

        def bar(price):
            return {"open": price, "close": price, "adjclose": price,
                    "dollar_volume": 1e9, "split": 1, "dividend": 0}
        # STEADY and JUMPY both end the 21-session window up ~10% in total,
        # but STEADY gets there in small, even daily steps while JUMPY sits
        # flat then makes the whole move in one giant single-day spike (P006's
        # real failure mode: names that "look hot" on raw return but got
        # there via one violent day). Raw 1-month return ranks them equally;
        # only Sharpe should separate them.
        steady, jumpy = {}, {}
        for i, day in enumerate(dates):
            if i < len(dates) - 21:
                steady[day] = bar(100.0)
                jumpy[day] = bar(100.0)
            else:
                k = i - (len(dates) - 22)
                steady[day] = bar(100.0 * (1 + 0.10) ** (k / 21))
                jumpy[day] = bar(100.0 if k < 20 else 110.0)
        return {"STEADY": steady, "JUMPY": jumpy}, dates

    def test_sharpe_prefers_the_steady_path_over_a_single_day_spike_to_the_same_total_return(self):
        bars, dates = self._bars()
        index = len(dates) - 1
        symbols = {"STEADY": "x", "JUMPY": "x"}
        raw = rank_signals(bars, dates, index, symbols, 0, formation="1m")
        sharpe = rank_signals(bars, dates, index, symbols, 0, formation="1m-sharpe")
        raw_m1 = {r["symbol"]: r["m1"] for r in raw}
        self.assertAlmostEqual(raw_m1["STEADY"], raw_m1["JUMPY"], places=3)
        self.assertEqual(sharpe[0]["symbol"], "STEADY")
        self.assertIn("sharpe_1m", sharpe[0])
        self.assertNotIn("m1", sharpe[0])

    def test_zero_variance_symbol_is_dropped_not_scored(self):
        bars, dates = self._bars()
        index = len(dates) - 1
        flat = {d: {"open": 50.0, "close": 50.0, "adjclose": 50.0, "dollar_volume": 1e9,
                    "split": 1, "dividend": 0} for d in dates}
        bars = dict(bars, FLAT=flat)
        result = rank_signals(bars, dates, index, {"STEADY": "x", "JUMPY": "x", "FLAT": "x"},
                              0, formation="1m-sharpe")
        self.assertNotIn("FLAT", {r["symbol"] for r in result})
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()
