"""Run a cached, reproducible fixed-rule sample and persist the full research loop."""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .data import check_action_bridge, download, fingerprint, normalize
from .engine import metrics, simulate


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def total_return_reference(bars, dates, config, capital, cost_bps):
    sessions = [d for d in dates if config["evaluation_start"] <= d <= config["evaluation_end"]]
    first = bars[sessions[0]]
    adjusted_open = first["open"] * first["adjclose"] / first["close"]
    units = capital / (1 + cost_bps / 10000) / adjusted_open
    rows = [{"date": d, "nav_usd": units * bars[d]["adjclose"]} for d in sessions]
    summary = metrics(rows, capital)
    summary.update({"variant": "QQQ-total-return-proxy", "capital_usd": capital,
                    "cost_bps": cost_bps,
                    "execution_cost_usd": capital * (cost_bps / 10000) / (1 + cost_bps / 10000)})
    return summary, rows


def report(summary, config, run_id, quality):
    base_rows = [r for r in summary if r["capital_usd"] == 200000 and r["cost_bps"] == 10]
    lines = [
        "# VITALIS 第一轮研究原型结果", "",
        f"实验：`{config['experiment_id']}`；运行：`{run_id}`。", "",
        "**决策：正式投资有效性证据不足。工程原型已完成历史样本闭环；不能据此认定策略能持续跑赢QQQ。**", "",
        f"用户目标：总投资本金20万–40万美元，优先扣成本后超过QQQ，最大回撤约30%作为研究上限；数据年费≤1,000美元。",
        f"本次区间：{quality['evaluation_first']}至{quality['evaluation_last']}，{quality['evaluation_sessions']}个交易日；股票样本{len(config['symbols'])}只。", "",
        "## 同期结果", "",
        "下表为20万美元资金、单次买/卖10bps成本场景；股票策略已扣每年600美元假设系统现金费。费用按252交易日年化；未计税、现金利息及机会成本。", "",
        "| 方案 | 净CAGR | 相对QQQ总收益差 | 最大回撤 | Ulcer | 最长水下交易日 | 平均股票数 | 执行费用USD | 系统费用USD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in base_rows:
        lines.append(
            f"| {row['variant']} | {row['cagr']:.2%} | {row.get('excess_cagr_pp', 0):+.2f}pp | "
            f"{row['max_drawdown']:.2%} | {row['ulcer_index_percentage_points']:.2f} | "
            f"{row['longest_underwater_trading_days']} | {row.get('average_holdings', 1):.1f} | "
            f"{row.get('execution_cost_usd', 0):,.0f} | {row.get('fixed_cost_usd', 0):,.0f} |"
        )
    lines += ["", "QQQ-total-return-proxy使用调整后收盘比例代表分红再投，仅起始开盘为调整价代理；QQQ整数股账本的分红留在现金中，两者分别展示。QQQ-cash15与M10-risk15采用同一15%波动预算、月度滞后估计，但不是两个组合波动恰好相同的保证。", "",
              "## 样本目标检查", "",
              "| 股票方案 | 超过QQQ总收益代理？ | 最大回撤≤30%？ | 两项同时满足？ | 12%单名风险复核天数 |",
              "|---|---|---|---|---:|"]
    for row in base_rows:
        if not row["variant"].startswith("M"):
            continue
        lines.append(f"| {row['variant']} | {'是' if row['sample_return_pass'] else '否'} | "
                     f"{'是' if row['sample_drawdown_pass'] else '否'} | "
                     f"{'是' if row['sample_joint_pass'] else '否'} | {row['hard_review_days']} |")
    lines += ["", "通过仅表示本样本的数值条件，并非满足完整04验证协议、全经济成本门槛或已取得统计证据。降低仓位若让年化落后QQQ，仍未满足当前收益目标。单名12%风险复核只留日志，本版未假设一个人工投资者自动及时处理它。", "",
              "## 资金与成本敏感性", "",
              "| 资金USD | 买/卖成本bps | 方案 | 净CAGR | 相对QQQ差 | 回撤 |",
              "|---:|---:|---|---:|---:|---:|"]
    for row in summary:
        if row["variant"].startswith("M"):
            lines.append(f"| {row['capital_usd']:,} | {row['cost_bps']} | {row['variant']} | "
                         f"{row['cagr']:.2%} | {row['excess_cagr_pp']:+.2f}pp | {row['max_drawdown']:.2%} |")
    lines += ["", "## 证据边界", ""] + ["- " + x for x in config["known_limitations"]]
    lines += ["", "## 贡献与规则诊断", "",
              "| 股票方案 | 最大正贡献证券 | 占正贡献总额比例 |",
              "|---|---|---:|"]
    for row in base_rows:
        if row["variant"].startswith("M"):
            share = row["top_positive_contribution_share"]
            lines.append(f"| {row['variant']} | {row['top_positive_contributor']} | {share:.1%} |")
    lines += ["", "比例以正贡献总额为分母，负贡献另保留，不能把赢家占比等同于独立押注数。每个方案`contributions.csv`的价格损益+分红−执行费，再减固定费，独立核对到期末财富。",
              "20只版保留门槛为排名≤40，但样本只有30只；只要仍符合资格和行业约束，原有20只很少因排名退出。因此M20更接近初始选中的存续股票篮子，不代表200只历史股票池中的动态20只策略。",
              f"内部公司行动桥接检查：{quality['action_bridge_discrepancies']}项超过0.2pp的价格/分红/拆股与调整收益差异。这仅检查同源内部一致性，不替代独立来源核对。"]
    lines += ["", "本次实际购买数据费用为0。600美元是运行费用情景；它不是实际账单，也不包含开发维护时间。30%的研究上限不能保证未来损失不会超限。", "",
              "## 闭环与下一轮", "",
              "数据源、查询时间范围与响应哈希在`manifest.json`；规则在`config.json`；日净值、持仓、交易与风险旗标分别写CSV，选股分数与信号/成交日期在各方案`decisions.json`。所有30个资金/成本/方案组合均保留，不只展示胜者。", "",
              "1. 先检查PIT证券母表和公司行动样本的数据可得性与预算，再替换当前存续股票样本；不能继续在本样本上挑参数证明alpha。",
              "2. 可靠PIT基本面合格后，增加质量对照；当前动量结果不为质量或LEAPS背书。",
              "3. 账户税制与真正策略资金比例确认后重算净价值；IBKR仍后置。",
              "4. 新实验先冻结变更与验证区间，再运行并登记继续/修改/停止/证据不足。",
              "", "`decision.json`登记本轮结论，项目实验日志在`docs/prototype/experiments.jsonl`。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/prototype-v1.json")
    parser.add_argument("--cache-dir", default="data/public-yahoo")
    parser.add_argument("--output-dir", default="runs")
    parser.add_argument("--offline", action="store_true", help="Require existing checksummed raw cache")
    parser.add_argument("--experiment-log", default="docs/prototype/experiments.jsonl")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    config_hash = fingerprint(config)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + config_hash[:8]
    run = Path(args.output_dir) / run_id
    run.mkdir(parents=True, exist_ok=False)
    (run / "config.json").write_text(json.dumps(config, indent=2))
    manifest = {"run_id": run_id, "config_sha256": config_hash,
                "config_saved_before_download": True, "sources": [], "status": "starting"}
    source_dir = run / "source" / "vitalis"
    source_dir.mkdir(parents=True)
    manifest["source_checksums"] = {}
    for source in Path(__file__).parent.glob("*.py"):
        raw = source.read_bytes()
        (source_dir / source.name).write_bytes(raw)
        manifest["source_checksums"][source.name] = hashlib.sha256(raw).hexdigest()
    # Write the frozen run configuration BEFORE downloading or examining results.
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
    bars, issues, bridge_issues = {}, [], []
    all_symbols = list(config["symbols"]) + [config["benchmark"]]
    try:
        for i, symbol in enumerate(all_symbols):
            cache_path = Path(args.cache_dir) / f"{symbol}-{config['data_start']}-{config['data_end_exclusive']}.json"
            if args.offline and not cache_path.exists():
                raise ValueError(f"Offline cache missing: {symbol}")
            envelope = download(symbol, config["data_start"], config["data_end_exclusive"], args.cache_dir)
            bars[symbol], found = normalize(envelope)
            issues.extend(found)
            bridge_issues.extend({"symbol": symbol, **issue} for issue in check_action_bridge(bars[symbol]))
            manifest["sources"].append({k: v for k, v in envelope.items() if k != "payload"})
            print(f"Data {i+1}/{len(all_symbols)}: {symbol}, {len(bars[symbol])} valid sessions", flush=True)
        dates = sorted(bars[config["benchmark"]])
        evaluation = [d for d in dates if config["evaluation_start"] <= d <= config["evaluation_end"]]
        needed = [d for d in dates if d <= config["evaluation_end"]]
        for symbol in all_symbols:
            missing = [d for d in needed if d not in bars[symbol]]
            if missing:
                raise ValueError(f"Missing QQQ-aligned sessions: {symbol}, first {missing[:3]}; no silent dropping")
        if bridge_issues:
            raise ValueError(f"Corporate action/adjustment bridge mismatches: {bridge_issues[:3]}")
        quality = {"sample_universe_pit": False, "independent_action_reconciliation": False,
                   "action_bridge_discrepancies": len(bridge_issues),
                   "missing_required_bar_count": 0, "excluded_invalid_bars": issues,
                   "evaluation_first": evaluation[0], "evaluation_last": evaluation[-1],
                   "evaluation_sessions": len(evaluation), "formal_validation_ready": False}
        (run / "data-quality.json").write_text(json.dumps(quality, indent=2))
        results = []
        for capital in config["capital_scenarios_usd"]:
            for cost in config["execution_cost_bps"]:
                reference, ref_nav = total_return_reference(bars["QQQ"], dates, config, capital, cost)
                results.append(reference)
                ref_dir = run / f"QQQ-total-return-proxy-{capital}-{cost}bps"
                ref_dir.mkdir()
                write_csv(ref_dir / "nav.csv", ref_nav)
                for variant in ("QQQ", "QQQ-cash15", "M10", "M20", "M10-risk15"):
                    summary, nav, trades, positions, decisions, warnings, contributions = simulate(
                        bars, dates, config, capital, cost, variant)
                    summary["excess_cagr_pp"] = (summary["cagr"] - reference["cagr"]) * 100
                    summary["sample_return_pass"] = summary["cagr"] > reference["cagr"]
                    summary["sample_drawdown_pass"] = -summary["max_drawdown"] <= config["drawdown_research_limit"]
                    summary["sample_joint_pass"] = summary["sample_return_pass"] and summary["sample_drawdown_pass"]
                    results.append(summary)
                    folder = run / f"{variant}-{capital}-{cost}bps"
                    folder.mkdir()
                    for name, rows in (("nav", nav), ("trades", trades), ("holdings", positions), ("risk-flags", warnings), ("contributions", contributions)):
                        write_csv(folder / f"{name}.csv", rows)
                    (folder / "decisions.json").write_text(json.dumps(decisions, indent=2))
                    print(f"Simulated {variant}, ${capital}, {cost}bps", flush=True)
        (run / "summary.json").write_text(json.dumps(results, indent=2, allow_nan=False))
        decision = {
            "experiment_id": config["experiment_id"], "run_id": run_id,
            "engineering_loop": "completed", "investment_decision": "insufficient_evidence",
            "reasons": config["known_limitations"], "actual_data_purchase_usd": 0,
            "next_experiment": "P002: point-in-time universe and action reconciliation before quality",
            "sample_joint_passes": [{"variant": r["variant"], "capital_usd": r["capital_usd"],
                                     "cost_bps": r["cost_bps"]} for r in results
                                    if r["variant"].startswith("M") and r["sample_joint_pass"]],
        }
        (run / "decision.json").write_text(json.dumps(decision, indent=2))
        (run / "report.md").write_text(report(results, config, run_id, quality))
        manifest["status"] = "engineering_loop_completed"
        manifest["normalized_data_sha256"] = fingerprint(bars)
        manifest["output_checksums"] = {
            str(p.relative_to(run)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(run.rglob("*")) if p.is_file() and p.name != "manifest.json"
        }
        log = Path(args.experiment_log)
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a") as stream:
            stream.write(json.dumps({"run_id": run_id, "experiment_id": config["experiment_id"],
                                     "config_sha256": config_hash, "investment_decision": "insufficient_evidence",
                                     "report": str(run / "report.md")}) + "\n")
        print(f"Report: {run / 'report.md'}", flush=True)
    except Exception as error:
        manifest.update(status="blocked_by_data_or_accounting", error=f"{type(error).__name__}: {error}")
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(manifest["error"], file=sys.stderr)
        return 2
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
