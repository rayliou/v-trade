"""Build the P004 Chinese audit receipt from checked local run artifacts.

python3 -m scripts.build_p004_report --source-run runs/<pit-run> --cash-run runs/<cash0-run>
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from vitalis.research_audit import sha256_file


def load_checked(run, name):
    manifest = json.loads((run / 'manifest.json').read_text())
    if manifest['status'] != 'completed':
        raise ValueError('Run not complete')
    expected = next(r['sha256'] for r in manifest['output_artifacts'] if r['path'] == name)
    if sha256_file(run / name) != expected:
        raise ValueError(f'Report input checksum mismatch: {name}')
    return json.loads((run / name).read_text())


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', required=True)
    parser.add_argument('--cash-run', required=True)
    args = parser.parse_args()
    run, cash_run = Path(args.source_run), Path(args.cash_run)
    config = load_checked(run, 'config.json')
    expected = {'evaluation_start':'2005-01-03', 'evaluation_end':'2025-12-31',
                'capital_usd':300000, 'cost_bps':10, 'annual_system_cash_cost_usd':600,
                'cost_scenario_annual_fee_usd':828}
    if any(config[k] != v for k,v in expected.items()):
        raise ValueError('This report template requires the registered P004 default protocol')
    summary = load_checked(run, 'summary.json')
    costs = load_checked(run, 'cost_scenarios.json')
    zero = load_checked(cash_run, 'summary.json')
    audit = load_checked(run, 'data_audit.json')
    diag = load_checked(run, 'diagnostics.json')
    bootstrap = load_checked(run, 'bootstrap_by_variant.json')
    quality = load_checked(run, 'quality_details.json')
    decision = load_checked(run, 'decision.json')
    cash_config = load_checked(cash_run, 'config.json')
    if cash_config['parent_run_id'] != run.name:
        raise ValueError('Cash sensitivity is not from this exact parent')
    base = {r['variant']: r for r in costs if r['capital_usd'] == 300000 and r['cost_bps'] == 10}
    zeros = {r['variant']: r for r in zero if r['capital_usd'] == 300000 and r['cost_bps'] == 10}
    total = sum(len(rows) for rows in quality.values())
    na = sum(r['na'] for rows in quality.values() for r in rows.values())
    peers = [r['peer_count'] for rows in quality.values() for r in rows.values() if not r['na']]
    categories = Counter(r['category'] for r in audit['action_bridge'])
    held = [r for r in audit['action_bridge'] if r['in_evaluation'] and r['held_variants']]
    ref = next(r for r in summary if r['variant'] == 'QQQ-total-return-proxy')
    folder = Path('docs/prototype')
    metadata = {'run_id': run.name, 'cash_run_id': cash_run.name,
        'run_manifest_sha256': sha256_file(run/'manifest.json'),
        'cash_manifest_sha256': sha256_file(cash_run/'manifest.json'),
        'report_generator_sha256': sha256_file(__file__),
        'engineering_decision': decision['engineering_decision'], 'investment_decision':'insufficient_evidence',
        'data_gate_pass':audit['data_gate_pass'], 'summary':summary, 'actual_fee_scenarios':costs,
        'zero_yield_scenarios':zero, 'audit_counts':{
            'bridge_total':audit['bridge_total'], 'bridge_in_evaluation':audit['bridge_in_evaluation'],
            'bridge_held_events':audit['bridge_held_events'], 'bridge_categories':dict(categories),
            'exit_proxy_rows':len(audit['exit_proxies']),
            'exit_proxy_distinct_securities':len({r['symbol'] for r in audit['exit_proxies']}),
            'unfilled_orders':len(audit['unfilled_orders'])},
        'quality_coverage': {'ticker_months':total, 'na_ticker_months':na,
                             'na_share':na/total, 'minimum_computed_peer_count':min(peers)},
        'limitations':['Unresolved noncash distributions and exit settlements.',
                       'Current metadata and imperfect reconstructed SIC.',
                       'Historical window already inspected; multiple comparisons uncorrected.',
                       'Cash yields and tax drag remain scenarios.']}
    (folder/'p004-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    text = ['# P004：先修复证据，再判断股票主线是否值得继续', '',
        '2026-09-13。仅复用现有Sharadar/Yahoo/FRED缓存，未增加订阅、未连接IBKR、未执行交易。', '',
        '## 当前决定', '',
        '**工程核验已完成并暴露未通过的数据门槛；投资决定仍为证据不足。暂停新信号、风险阈值和LEAPS实验，先补齐分拆资产与并购/退市经济结算。** 当前不完整账本下所有已测股票候选均未同时达到净收益超过QQQ、回撤约30%的目标。低收益不是完整会计验收后的最终策略判决。', '',
        'P003/P003b此前引用的收益优势已撤回：月初使用同月月末候选与质量信息；另有成交额单位混合。旧文件保留，修正后的数字不能被解释成单个修正的因果贡献。', '',
        '## 数据、规则与成本', '',
        f'- 历史：2005-01-03至2025-12-31，共{ref["sessions"]}个交易日；月末输入仅供下月开盘执行。',
        '- 冻结规则：12-1/6-1动量、10/20只、等权、月度滞回、行业上限30%；质量50/50，风险覆盖目标15%。无报价目标未成交留现金，不选择替补。',
        '- 主工程对照维持30万美元、买卖各10bps、固定费600美元；以下投资成本摘要用828美元真实月付年化数据费。828美元尚不含未确认税费，全年总预算仍为1,000美元。',
        '- 现金利息：FRED DGS3MO参考情景与零利息各自完整重算；两者都不是已核实的IBKR计息条款。税前结果，未加入未知账户税制。', '',
        '## 扣真实数据费后的历史诊断', '',
        '30万美元、买卖各10bps、每年固定费828美元；QQQ调整收盘总收益代理为主机会成本，已扣初始买入成本，不扣本系统增量固定费。', '',
        table(['方案','净年化','相对QQQ(pp)','最大回撤','零现金利息年化'],
              [[v,f'{r["cagr"]:.2%}',f'{r["excess_cagr_pp"]:+.2f}',f'{r["max_drawdown"]:.2%}',
                f'{zeros[v]["cagr"]:.2%}'] for v,r in base.items()]), '',
        f'QQQ总收益代理：年化{ref["cagr"]:.2%}、最大回撤{ref["max_drawdown"]:.2%}。整数股QQQ、股息留现金的账本口径约14.15%，不能与主基准合并。', '',
        '## 解释性发现', '',
        table(['方案','2005–2014相对年化(pp)','2015–2025相对年化(pp)','平均现金','36月窗口胜出比例','最长水下交易日'],
          [[v,f'{diag[v]["periods"][0]["excess_cagr_pp"]:+.2f}',
            f'{diag[v]["periods"][1]["excess_cagr_pp"]:+.2f}', f'{diag[v]["average_cash_weight"]:.1%}',
            f'{sum(r["excess_cagr_pp"]>0 for r in diag[v]["rolling_36m"])/len(diag[v]["rolling_36m"]):.1%}',
            next(r['longest_underwater_trading_days'] for r in summary if r['variant']==v)] for v in base]), '',
        '以上时期与水下指标使用600美元工程对照，与828美元费用表分开；分期年化是按交易日年化，36月指756交易日并在月末采样。重叠窗口不是独立样本。', '',
        '- 纯动量在两个已登记长时期均落后主基准；风险覆盖在后期损失更多上涨参与度。现金收益归因必须参考独立零利息重算，不能直接从累计收益中减利息。',
        '- 相同15%风险覆盖的QQQ现金对照年化约11.91%、最大回撤约29.44%，说明现有风险覆盖本身可降低市场风险，但没有达到跑赢原QQQ的目标。它不承担股票研究系统增量固定费；完整账本中的股票选择/行动处理仍待经济核验。',
        '- 正贡献前五占比、正/负贡献HHI、当前行业美元归因已保存。美元贡献受财富路径影响，行业标签不是历史时点认证，不能把这些描述当因果或新alpha。', '',
        table(['方案','正贡献前五占比','平均质量N/A占NAV'],
              [[v,f'{diag[v]["top5_positive_share"]:.1%}',f'{diag[v]["average_quality_na_nav_weight"]:.1%}'] for v in base]), '',
        '## 统计与验收边界', '',
        '固定600美元工程对照的配对21/63交易日区块重采样，2,000次、固定种子20260913。以下CAGR差90%区间没有多重比较修正，也不能解除数据门槛。', '',
        table(['方案','21日区块区间(pp)','63日区块区间(pp)'],
          [[v, f'[{bootstrap[v]["21"]["cagr_diff_pp"]["p05"]:+.2f}, {bootstrap[v]["21"]["cagr_diff_pp"]["p95"]:+.2f}]',
               f'[{bootstrap[v]["63"]["cagr_diff_pp"]["p05"]:+.2f}, {bootstrap[v]["63"]["cagr_diff_pp"]["p95"]:+.2f}]'] for v in base]), '',
        '## 资本与成本压力', '',
        '20万/40万美元，828美元固定费，买卖各10/25bps。表中为净年化/最大回撤，所有失败场景保留；零利息完整情景见元数据。', '',
        table(['方案','20万/10bps','40万/10bps','20万/25bps','40万/25bps'],
          [[v]+[next(f'{r["cagr"]:.2%} / {r["max_drawdown"]:.2%}' for r in costs
             if r['variant']==v and r['capital_usd']==capital and r['cost_bps']==cost)
             for capital,cost in [(200000,10),(400000,10),(200000,25),(400000,25)]] for v in base]), '',
        '## 下一步，保持闭环', '',
        '1. **P005公司行动账本验收**：用已有actions、stocks和tickers，扩展分拆/收购对手证券覆盖。分拆接收子公司权益；现金、换股、选择权对价分开处理。支付日、现金替代零碎股及缺少条款明确列情景或阻断，不能默认最后价变成现金。先对本轮直接持仓分拆与退出事件逐笔验收，再重新冻结基线。',
        '2. **PIT主档范围核验**：统计当前行业/类别/交易所及不完整SIC链实际影响，无法证明历史状态的范围明确降级。新投资建议继续受门槛约束。',
        '3. 完成前两项后重新判断：若净收益/风险仍不达标，停止当前股票候选的alpha扩展；若有稳健候选才进入有限前向影子验证。质量排除阈值或新风险机制需根据有效归因重新预登记。',
        '4. 数据更新、人工建议确认、持仓/交易/现金、QQQ与风险复盘保持同一日志链。影子运行只能先证明操作一致性；IBKR只读接入后置，LEAPS继续独立后置。', '',
        '无需增加数据订阅。下一阶段的投入价值先通过上述逐笔会计验收判断，不以更多因子、UI或回测胜者代替。', '',
        '## 可检查产物', '',
        '- [工程审计与异常分类](p004-engineering-audit.md)',
        '- [聚合元数据，包含全部费用/本金/零利息场景](p004-metadata.json)',
        '- [本地核验Notebook](p004-audit.ipynb)',
        '- [旧时点影响计数](p004-legacy-timing-audit.json)',
        f'- 主run：`{run.name}`；零利息run：`{cash_run.name}`。完整源/代码/输出哈希、账本和异常保存在忽略Git的`runs/`，实验登记追加到`experiments.jsonl`。', '']
    (folder/'p004-audit-and-diagnostics.md').write_text('\n'.join(text))
    technical = ['# P004工程审计：已修复与未验收分开', '',
        '## 已修复', '',
        table(['问题','证据/影响','修复/验证'],[
          ['同月月末输入用于月初交易','旧252个评估月全部存在候选差异，平均约6只未来新增候选','映射到下月，未来输入改变不能改变本月执行；缺月失败'],
          ['名义价格×拆股调整成交量','本地SEP数据字典明确close/volume均拆股调整','成交额用源close×volume；4:1拆股单位回归'],
          ['无开盘报价目标直接索引','第一次修正run在2014-07-01失败','记录未成交、留现金、不替补，保留失败run'],
          ['质量扩大同业组只比较回退成员','旧41,957个计算证券月中2,849个实际同业少于10只','完整上级组成员与按组分位；同行回归及peer_count'],
          ['P003缺代码/源哈希与实验登记','旧manifest只有配置哈希','实际SHA-256核验、代码复制、输出哈希、SQLite快照/文件目录、成功失败登记'],
          ['研究入口可在线补缺','P003曾自动初始化QQQ/FRED','P004精确缓存只读；缺缓存不打开网络；运行remote_requests=0'],
          ['通用输入被误认自身侧录','非zip JSON数组/压缩/脚本无法通用登记','仅zip匹配provenance，补三类回归']]), '',
        '## 当前数据门槛', '', table(['门槛','通过'], [[k,str(v)] for k,v in audit['gates'].items()]), '',
        '价格完整与账本恒等式通过不等于经济行动处理通过；当前门槛总结果为False。内部桥接只是现金持有模型与调整价格的一致性检查，不是独立源认证。', '',
        f'- 总桥接差异{audit["bridge_total"]}条，评估期内{audit["bridge_in_evaluation"]}条，直接持仓日期{audit["bridge_held_events"]}条。',
        f'- 未验证最后价退出{len(audit["exit_proxies"])}条方案事件，涉及{len({r["symbol"] for r in audit["exit_proxies"]})}只证券；无报价目标未成交{len(audit["unfilled_orders"])}条。方案事件不是独立公司事件。',
        '- 全历史566,335个拆股/分红键无重复，重复记录不能解释本轮差异。', '',
        table(['分类','条数'], list(categories.items())), '',
        '附近±3日行动仅作分类；未持仓异常也可能影响复权信号，不能自动忽略。source中仍有IPO/发行人ID、当前主档、已更正AR历史交付时点及行业链覆盖等边界。', '',
        '## 直接持仓分拆异常', '',
        table(['证券','日期','现金模型-调整收益差(pp)','方案'],
              [[r['ticker'],r['date'],f'{r["difference_pp"]:+.2f}',', '.join(r['held_variants'])] for r in held]), '',
        '现有ACTIONTYPES字典将spinoff定义为每股母公司分配的子公司股数，将spinoffdividend定义为分配股票的美元价值。后者不是现金支付，不能直接假设立即变现。此前引擎只接收split/dividend，遗漏分拆权益；必须接入子公司持股与后续交易/处置账本。', '',
        '## 质量与缓存', '',
        f'质量覆盖{total:,}证券月，N/A {na:,}（{na/total:.1%}）。N/A包含有意排除的金融/REIT、无申报和缺指标；中性0.5不是质量合格。修复后实际计算同业最小{min(peers)}只。', '',
        '缓存raw zip不变，派生日历/市值/价格gzip JSON按源哈希、规范化代码及范围命中并校验，禁止pickle。SQLite仅snapshot/artifact目录；共享采集限流、分页重试、并发发布租约、coverage目录及Parquet/DuckDB查询层尚未实现。本轮没有远程采集，不消耗源并发/时间额度。', '',
        '## 重跑与验证', '',
        '```sh', 'python3 -m vitalis.run_pit --offline --max-workers 4',
        f'python3 -m scripts.cash_yield_sensitivity --source-run runs/{run.name}',
        f'python3 -m scripts.build_p004_report --source-run runs/{run.name} --cash-run runs/{cash_run.name}',
        'python3 -m unittest discover -s tests -v', 'git diff --check', '```', '',
        '执行前后源文件哈希核对，每个run唯一且保留代码/配置。报告生成检查其输入产物哈希；Notebook核对源和输出哈希。最终完整103项测试通过（177.880秒）；质量/通用登记修正也通过35项相关回归。Notebook的5个代码单元已执行，源/输出哈希与时点断言通过。', '',
        '完整异常：主run的data_audit.json；解释序列：diagnostics.json；质量peer_count：quality_details.json；真实费用场景：cost_scenarios.json。', '']
    (folder/'p004-engineering-audit.md').write_text('\n'.join(technical))
    print('Wrote P004 narrative, technical audit and aggregate metadata')


if __name__ == '__main__':
    main()
