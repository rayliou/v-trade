"""P002 public AAPL cross-source audit, never a full-market alpha experiment."""

import argparse
import hashlib
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .data import download, fingerprint, normalize
from .pit import fundamentals_asof, normalize_fundamentals


def fetch_sample(table, config, cache, offline=False):
    query = dict(ticker="AAPL", format="json", limit=10000, sort="date.asc",
                 **{"from": config["start"], "to": config["end"]})
    if table == "fundamentals":
        query["dimension"] = "ART"
    path = Path(cache) / f"{table}-AAPL-{config['start']}-{config['end']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        envelope = json.loads(path.read_text())
    else:
        if offline:
            raise FileNotFoundError(path)
        url = "https://api.sharadar.com/v1.0/data/" + table + "?" + urllib.parse.urlencode(
            dict(query, api_key="test-api-key")
        )
        request = urllib.request.Request(url, headers={"User-Agent": "VITALIS-research-prototype/0.2"})
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        envelope = dict(url=url, retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                        payload_sha256=fingerprint(payload), payload=payload)
        with path.open("x") as stream:
            json.dump(envelope, stream)
    if envelope["payload_sha256"] != fingerprint(envelope["payload"]):
        raise ValueError("Public sample cache checksum failed")
    expected_url = "https://api.sharadar.com/v1.0/data/" + table + "?" + urllib.parse.urlencode(
        dict(query, api_key="test-api-key")
    )
    if envelope["url"] != expected_url:
        raise ValueError("Cached request differs from frozen audit query")
    rows = envelope["payload"].get("data")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Missing public sample data array")
    if len(rows) >= query["limit"]:
        raise ValueError("Possible pagination: sample is incomplete")
    for row in rows:
        if row["ticker"] != "AAPL" or not config["start"] <= row["date"] <= config["end"]:
            raise ValueError("Unexpected ticker/date in public sample")
    return rows, envelope


def compare_sample(prices, actions, bars, config):
    if len({r["date"] for r in prices}) != len(prices):
        raise ValueError("Duplicate price date")
    days = sorted(d for d in bars if config["start"] <= d <= config["end"])
    source_days = {r["date"] for r in prices}
    overlap = sorted(set(days) & source_days)
    price_bad, price_errors = [], []
    for row in prices:
        day = row["date"]
        if day not in bars:
            price_bad.append(dict(date=day, issue="no_yahoo_bar"))
            continue
        closing = float(row["closeunadj"])
        if not math.isfinite(closing) or closing <= 0:
            raise ValueError("Nonpositive/nonfinite source closing price")
        error = abs(closing / bars[day]["close"] - 1)
        price_errors.append(error)
        if error > config["price_relative_tolerance"]:
            price_bad.append(dict(date=day, issue="nominal_close_mismatch", relative_error=error))
    action_days, action_bad = set(), []
    for row in actions:
        day, kind = row["date"], row["action"]
        if kind not in ("dividend", "split"):
            action_bad.append(dict(date=day, issue="unsupported_action", action=kind))
            continue
        key = (day, kind)
        if key in action_days:
            raise ValueError("Duplicate action")
        action_days.add(key)
        expected = bars.get(day, {}).get(kind)
        value = float(row["value"])
        if not math.isfinite(value) or value < 0 or (kind == "split" and value == 0):
            raise ValueError("Invalid source action value")
        if expected is None or abs(value - expected) > config["action_absolute_tolerance"]:
            action_bad.append(dict(date=day, issue="action_mismatch", action=kind))
    # Compare both directions only inside the observed price window. Earlier
    # absent events remain uncovered, rather than being called discrepancies.
    if overlap:
        for day in overlap:
            for kind, nondefault in (("dividend", bars[day]["dividend"] != 0),
                                     ("split", bars[day]["split"] != 1)):
                if nondefault and (day, kind) not in action_days:
                    action_bad.append(dict(date=day, issue="vendor_action_missing", action=kind))
    return dict(expected_price_sessions=len(days), compared_price_sessions=len(overlap),
                missing_price_sessions=len(set(days) - source_days),
                returned_first_date=min(source_days), returned_last_date=max(source_days),
                nominal_close_max_relative_error=max(price_errors, default=None),
                price_discrepancies=price_bad, compared_actions=len(actions),
                action_discrepancies=action_bad,
                full_requested_price_history=not (set(days) - source_days) and not price_bad)


def render(result):
    c, f = result["cross_source"], result["financial_timing"]
    return "\n".join([
        "# P002：免费样本数据验收", "",
        "**决策：继续准备历史数据，正式投资有效性仍为证据不足。**", "",
        "本轮未改动P001选股参数，不增加收益优胜方案。只核验数据和财务可得性；实际采购0美元。", "",
        "## 实际检查", "",
        f"- 请求2020–2025；AAPL返回价格从{c['returned_first_date']}到{c['returned_last_date']}。",
        f"- 应有{c['expected_price_sessions']}个交易日，交叉比较{c['compared_price_sessions']}日，缺{c['missing_price_sessions']}日。",
        f"- 名义收盘价差异超限{len(c['price_discrepancies'])}日；最大相对差{c['nominal_close_max_relative_error']:.8%}（门槛0.05%）。",
        f"- 比较{c['compared_actions']}条公司行动，差异{len(c['action_discrepancies'])}条；此次供应商样本只包含现金分红，不能覆盖全部行动类型。",
        f"- 苹果官方2020-08-31交易拆股4:1与Yahoo事件匹配：{result['official_split_check']['matched']}。",
        f"- ART财务{f['observations']}条，覆盖{f['first_filing_date']}至{f['last_filing_date']}；仅1只股票，不能做30只质量策略比较。", "",
        "## 时点规则", "",
        "已实现ARQ/ARY/ART输入与截至日过滤；拒绝MR重述输入。财务所属期不作公布时间，下载日不作历史公布日。只有申报日而无时分时，整段延迟至申报日之后第一个交易日收盘才可用于研究，次日开盘成交。缺失不填零，旧季度后续申报不覆盖已知更新季度。", "",
        "这证明时点过滤工程可运行，不证明所有供应商AR值均完整保存历史修订；尚需披露原文抽查和稳定证券ID。", "",
        "## 未通过的研究门槛", "",
        "全请求历史缺口、历史进入/退出股票池与退市结算、ticker变更及稳定ID、历史行业/市值、全池财务、独立并购/分拆/支付日核对均未齐。两个供应商相同也不必然独立于底层数据商。缺口会阻止正式认证，不能被免费访问成功替代。", "",
        "## 下一步与预算", "",
        "先导入已有授权历史文件；若没有，评估预算内完整历史订阅。Sharadar个人完整历史Bundle当前499美元/年，或先69美元月付验收；未假设抵扣，未购买。采购前必须确认退出者、稳定映射、AR时点、历史覆盖和个人许可。[官方订阅](https://sharadar.com/subscribe)。", "",
        "数据齐备后只推进P003：冻结历史股票池，保持P001动量规则，加质量增量对照；保存账本、净QQQ差、回撤、水下期和继续/修改/停止决定。先核验数据，再定义未触碰的验证区间，不把P001反复看过的2021–2025称为封存集。", "",
        "来源：[价格口径](https://sharadar.com/docs/stocks)、[行动字段](https://sharadar.com/docs/actions)、[AR时点](https://sharadar.com/docs/fundamentals)、[苹果拆股公告](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/)。", "",
        f"运行：`{result['run_id']}`；完整审计、冻结配置、数据/代码哈希保存在对应runs目录。", "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/data-audit-v1.json")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-P002"
    output = Path("runs") / run_id
    output.mkdir(parents=True)
    (output / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    source_hashes = {}
    for name in ("sample_audit.py", "pit.py", "data.py"):
        content = Path("vitalis", name).read_bytes()
        source_hashes[name] = hashlib.sha256(content).hexdigest()
        (output / name).write_bytes(content)
    result = dict(run_id=run_id, experiment_id=config["experiment_id"],
                  config_sha256=fingerprint(config), code_sha256=source_hashes,
                  formal_strategy_validation_ready=False, investment_decision="insufficient_evidence",
                  actual_data_purchase_usd=0, status="started")
    result["research_blockers"] = [
        "Full requested history and warmup coverage not established",
        "Point-in-time entry/exit universe including delisted securities absent",
        "Stable security identity and ticker changes not reconciled",
        "Historical sector/market-cap evidence absent",
        "Whole-universe as-reported financial coverage absent",
        "Acquisition, spinoff, delisting settlement and dividend payment timing unverified",
        "Untouched validation period and forward shadow operation absent",
    ]
    try:
        samples, sources = {}, {}
        result["sources"] = sources
        for table in ("stocks", "actions", "fundamentals"):
            samples[table], envelope = fetch_sample(table, config, "data/public-sharadar", args.offline)
            sources[table] = {k: v for k, v in envelope.items() if k != "payload"}
        yahoo_path = Path("data/public-yahoo/AAPL-2020-01-01-2026-09-13.json")
        if args.offline and not yahoo_path.exists():
            raise FileNotFoundError(yahoo_path)
        yahoo = download("AAPL", "2020-01-01", "2026-09-13", "data/public-yahoo")
        bars, issues = normalize(yahoo)
        if issues:
            raise ValueError("Invalid Yahoo bars")
        sources["yahoo"] = {k: v for k, v in yahoo.items() if k != "payload"}
        financials = normalize_fundamentals(samples["fundamentals"], sorted(bars))
        timing = []
        for row in financials:
            before = fundamentals_asof([row], row["filing_date"])
            after = fundamentals_asof([row], row["available_on_close"])
            timing.append(dict(filing_date=row["filing_date"], reportperiod=row["reportperiod"],
                               available_on_close=row["available_on_close"],
                               withheld_on_filing_close=not before, visible_after_delay=bool(after)))
        if not all(r["withheld_on_filing_close"] and r["visible_after_delay"] for r in timing):
            raise ValueError("Financial timing boundary failed")
        result.update(status="completed", sources=sources,
                      cross_source=compare_sample(samples["stocks"], samples["actions"], bars, config),
                      financial_timing=dict(observations=len(financials), security_coverage=1,
                                            first_filing_date=min(r["filing_date"] for r in financials),
                                            last_filing_date=max(r["filing_date"] for r in financials),
                                            boundaries=timing),
                      official_split_check=dict(**config["official_split"],
                                                matched=bars[config["official_split"]["date"]]["split"] == config["official_split"]["ratio"]))
        (output / "report.md").write_text(render(result))
    except Exception as error:
        result.update(status="failed", error=f"{type(error).__name__}: {error}")
    result["artifact_sha256"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output.iterdir()) if path.is_file()
    }
    (output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    with Path("docs/prototype/experiments.jsonl").open("a") as stream:
        stream.write(json.dumps(dict(run_id=run_id, experiment_id=config["experiment_id"],
                                     config_sha256=result["config_sha256"], status=result["status"],
                                     investment_decision=result["investment_decision"],
                                     report=str(output / "report.md"), audit=str(output / "audit.json"))) + "\n")
    print(json.dumps(dict(run_id=run_id, status=result["status"], output=str(output),
                          error=result.get("error")), indent=2))
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
