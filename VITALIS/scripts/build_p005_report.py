"""Build the bounded P005 closeout decision from checksummed completed runs."""
import argparse
import json
from pathlib import Path

from vitalis.research_audit import sha256_file


def load_run(path, stage):
    path = Path(path)
    manifest = json.loads((path / 'manifest.json').read_text())
    if manifest['status'] != 'completed':
        raise ValueError('Cannot report an incomplete run')
    hashes = {r['path']: r['sha256'] for r in manifest['output_artifacts']}
    for name, expected in hashes.items():
        if sha256_file(path / name) != expected:
            raise ValueError(f'Run artifact checksum mismatch: {name}')
    outputs = {}
    for name in ['summary.json', 'accounting-audit.json', 'action-plan.json', 'decision.json', 'config.json']:
        if sha256_file(path / name) != hashes[name]:
            raise ValueError(f'Output checksum mismatch: {name}')
        outputs[name] = json.loads((path / name).read_text())
    if outputs['config.json']['stage'] != stage:
        raise ValueError('Stage mismatch')
    expected_cases = {(capital, cost, yield_name, variant)
        for capital, cost in outputs['config.json']['capital_cost_cases']
        for yield_name in outputs['config.json']['cash_yield_scenarios']
        for variant in outputs['config.json']['variants']}
    actual_cases = [(r['capital_usd'], r['cost_bps'], r['cash_yield_assumption'], r['variant'])
                    for r in outputs['summary.json']]
    if set(actual_cases) != expected_cases or len(actual_cases) != len(expected_cases) or len(actual_cases) != 50:
        raise ValueError('Missing, duplicate or unregistered closeout cases')
    return path, manifest, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spinoff-run', required=True)
    parser.add_argument('--acquisition-run', required=True)
    args = parser.parse_args()
    spin, sm, so = load_run(args.spinoff_run, 'spinoff')
    acq, am, ao = load_run(args.acquisition_run, 'acquisition')
    if sm['code_artifacts'] != am['code_artifacts'] or sm['runner_sha256'] != am['runner_sha256']:
        raise ValueError('Stages used different accounting code')
    if so['config.json']['parent_manifest_sha256'] != ao['config.json']['parent_manifest_sha256']:
        raise ValueError('Stages used different parent manifests')
    identity = json.loads((spin / 'baseline-identity.json').read_text())
    if len(identity) != 15 or not all(identity.values()):
        raise ValueError('Baseline identity checks did not pass')
    if so['config.json']['protocol_sha256'] != ao['config.json']['protocol_sha256']:
        raise ValueError('Stages used different preregistration')
    parent = Path('runs/20260913T230115679698Z-pit-170d681b')
    pm = json.loads((parent / 'manifest.json').read_text())
    if so['config.json']['parent_manifest_sha256'] != sha256_file(parent / 'manifest.json'):
        raise ValueError('Parent manifest changed')
    for name in ['summary.json', 'cost_scenarios.json', 'data_audit.json']:
        expected = next(r['sha256'] for r in pm['output_artifacts'] if r['path'] == name)
        if sha256_file(parent / name) != expected:
            raise ValueError('Parent result changed')
    baseline = json.loads((parent / 'cost_scenarios.json').read_text())
    if isinstance(baseline, dict):
        # P004 stores case summaries with their frozen real annual fee.
        baseline = baseline['summaries']
    ref = next(r for r in json.loads((parent / 'summary.json').read_text()) if r['variant'] == 'QQQ-total-return-proxy')
    def primary(rows, variant, yield_name='FRED'):
        return next(r for r in rows if r['variant'] == variant and r['capital_usd'] == 300000
                    and r['cost_bps'] == 10 and r.get('cash_yield_assumption', 'FRED') == yield_name)
    def main_audit(outputs, variant):
        return next(r for r in outputs['accounting-audit.json'] if r['variant'] == variant
                    and r['capital_usd'] == 300000 and r['cost_bps'] == 10 and r['yield'] == 'FRED')
    rows = []
    for variant in so['config.json']['variants']:
        b = primary(baseline, variant); s = primary(so['summary.json'], variant); a = primary(ao['summary.json'], variant)
        z = primary(ao['summary.json'], variant, 'zero'); audit = main_audit(ao, variant)
        rows.append({'variant': variant, 'p004_cagr': b['cagr'], 'spinoff_cagr': s['cagr'],
            'closeout_cagr': a['cagr'], 'excess_qqq_pp': (a['cagr'] - ref['cagr']) * 100,
            'max_drawdown': a['max_drawdown'], 'zero_cash_cagr': z['cagr'],
            'longest_underwater_trading_days': a['longest_underwater_trading_days'],
            'ulcer_index_percentage_points': a['ulcer_index_percentage_points'],
            'one_way_turnover_total': a['one_way_turnover_total'], 'events': audit['events']})
    joint = sum(r['cagr'] > ref['cagr'] and r['max_drawdown'] >= -.30 for r in ao['summary.json'])
    held_spins = {(w['symbol'], w['date']) for v in so['config.json']['variants']
                  for w in main_audit(ao, v)['corporate_actions'] if w['flag'] == 'corporate_spinoff_shares'}
    held_mergers = {(w['symbol'], w['date']) for v in so['config.json']['variants']
                    for w in main_audit(ao, v)['corporate_actions'] if w['flag'] == 'corporate_acquisition_scenario'}
    exits = {(w['symbol'], w['date']) for v in so['config.json']['variants']
             for w in main_audit(ao, v)['unresolved_exits']}
    fail_runs = []
    for p in sorted(Path('runs').glob('*p005-*')):
        m = json.loads((p / 'manifest.json').read_text())
        if m['status'] == 'failed': fail_runs.append({'run_id': p.name, 'error': m['error']})
    metadata = {'experiment_id': 'P005', 'project_action': 'stop_current_equity_alpha_development',
        'investment_decision': 'insufficient_evidence', 'data_gate_pass': False,
        'spinoff_run_id': spin.name, 'acquisition_run_id': acq.name,
        'manifest_sha256': {'spinoff': sha256_file(spin / 'manifest.json'), 'acquisition': sha256_file(acq / 'manifest.json')},
        'protocol_sha256': so['config.json']['protocol_sha256'], 'report_builder_sha256': sha256_file(__file__),
        'benchmark': ref, 'primary_results': rows, 'spinoff_all_cases': so['summary.json'],
        'acquisition_all_cases': ao['summary.json'], 'joint_point_pass_cases': joint,
        'held_spinoff_events_primary': sorted(held_spins), 'held_unambiguous_merger_events_primary': sorted(held_mergers),
        'unresolved_exit_events_primary': sorted(exits), 'failed_attempts': fail_runs,
        'verification': {'baseline_identity': identity,
                         'accounting_reconciliation': 'all simulations enforce daily and contributor PNL identities',
                         'remote_requests': 0},
        'limitations': ao['decision.json']['limitations']}
    checks_path = Path('docs/prototype/p005-checks.json')
    if checks_path.exists():
        checks = json.loads(checks_path.read_text())
        if any(sha256_file(r['path']) != r['sha256'] for r in checks['test_artifacts']):
            raise ValueError('Tests changed since recorded verification')
        metadata['verification']['tests'] = checks
        metadata['verification']['tests_sha256'] = sha256_file(checks_path)
    target = Path('docs/prototype/p005-metadata.json'); target.write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    md = ['# P005：有边界收尾与停止决定', '',
          '2026-09-13。仅使用已有Sharadar/Yahoo/FRED数据，完成预登记的两个记账阶段；未新增策略、订阅或券商连接。', '',
          '## 决定', '',
          '**停止当前股票动量/质量超额收益主线的继续开发。** 本轮是会计修复，不是新的策略搜索。现有候选没有可信证据同时达到扣成本跑赢QQQ、最大回撤约30%；继续叠加因子或产品工程没有得到投资收益证据支持。', '',
          '投资有效性结论为`insufficient_evidence`：仍存在未解决行动与历史时点缺口。项目动作是`stop_current_equity_alpha_development`；证据不足不自动触发下一轮补工程，也不能被表述成证明所有主动策略必然失败。', '',
          '## 冻结范围与经济处理', '',
          '- 沿用P004上月月末→下月执行、候选池、12-1/6-1动量、滞回、行业上限、质量50/50和15%风险目标，不调参。',
          '- 分拆股票进入持仓；`spinoffdividend`不当现金。下一交易日开盘只处置继承股数，并扣相同执行成本；原策略持股数量保留。',
          '- 新继承股票不参与滞回保留判断，月度交易预留其待处置市值后才分配普通目标；不为它增加排名名额。',
          '- 明确现金和股票收购条款相加，母公司持股被换出；收购源日期表示最后交易日，因此下一股票交易日记入对价，继承股票再于下一日处置。',
          '- 普通目标订单为整数股；公司行动允许分数权益作为情景。实际交付日、现金替代零股、税与支付日尚未核实，不能称为真实券商结算。',
          '- 两阶段各完整重算5个本金/成本组合×5个候选×FRED/零利息，共100条场景；每年固定费828美元，税前。数据订阅税费待确认，年度总预算仍≤1,000美元。', '',
          '## 30万美元、10bps、每年828美元费用的结果', '',
          '| 候选 | P004净年化 | 仅补分拆 | 再补明确收购 | 相对QQQ(pp) | 最大回撤 | 零现金利息年化 |',
          '| --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        md.append(f"| {r['variant']} | {r['p004_cagr']:.2%} | {r['spinoff_cagr']:.2%} | {r['closeout_cagr']:.2%} | {r['excess_qqq_pp']:+.2f} | {r['max_drawdown']:.2%} | {r['zero_cash_cagr']:.2%} |")
    md += ['', f"QQQ调整收盘总收益代理年化{ref['cagr']:.2%}、最大回撤{ref['max_drawdown']:.2%}；沿用P004相同起始成本与日期口径。联合收益/回撤点值通过：本轮明确收购阶段{joint}/50场景；即使点值通过也不能越过数据门槛。",
           '', '## 持仓体验', '', '| 候选 | 最长水下交易日 | Ulcer(pp) | 累计单边换手 |', '| --- | --- | --- | --- |']
    for r in rows:
        md.append(f"| {r['variant']} | {r['longest_underwater_trading_days']} | {r['ulcer_index_percentage_points']:.2f} | {r['one_way_turnover_total']:.2f} |")
    md += ['', '累计换手是全期现金与股票交易权重变化；继承股票处置计入。不是年化次数，也没有对未知人工操作或税制建模。', '',
           '## 已修到哪里、还缺什么', '',
           f'- 主本金/成本、FRED情景跨五候选实际记入{len(held_spins)}个独立分拆事件、{len(held_mergers)}个独立明确收购事件；重复候选不算独立公司事件。',
           f'- 主情景剩余最后价代理退出涉及{len(exits)}个独立证券/日期：'+', '.join(f'{s} ({d})' for s,d in sorted(exits))+ '。',
           '- 择付收购不能把现金和股票替代条款叠加；部分源记录只有一个替代选项，分配/比例/实际选择未知。继续保留最后价代理及旗标，不虚构条款。',
           '- TFCF 2019-03-21分拆源日期晚于母公司最后报价，属于行动日期/退出估值冲突；未重复加分拆资产，保留未解决旗标。无比例/非同比例分拆记录也保留。',
           '- P004的五条潜在持仓分拆桥接中，WMB在2012-01-03开盘才买入，没有前日持仓，不应领取该次分拆股票；实际四个既有持仓分拆才记入权益。相邻日期/当日持仓只能作诊断暴露，不能证明领取资格。',
           '- 非持仓复权桥接异常仍可能影响选股信号；历史交易所/类别、行业链、AR数据交付时点、报价覆盖等P004限制没有被本次记账修复认证。',
           '- 因此经济行动、执行与历史主档门槛仍未整体通过；没有追加外部数据源，也没有将这一缺口转成采购要求。', '',
           '## 复现与审计', '',
           f'- 分拆阶段：`{spin.name}`；明确收购阶段：`{acq.name}`。',
           '- 禁用行动模块时，五候选主情景的NAV、交易、持仓与P004真实费用账本15项SHA-256逐字节一致。两阶段会计代码与runner哈希相同。',
           '- [独立核验记录](p005-verification.json)重新读取100份场景账本，共528,300日记录，核对发布后的现金/股票余额、每日损益与证券贡献财富；源/产物哈希及冻结代码一致。它仅认证恒等式，不认证真实经济条款。',
           '- 每日现金/价格/行动/利息/费用损益与净值变化核对，按证券贡献与最终财富核对；源、代码、输出哈希保留，失败尝试见metadata和实验登记。',
           '- 最终完整113项unittest通过（164.497秒）；[检查记录](p005-checks.json)保存命令、日志和测试文件哈希。文档链接、脚本语法、JSON与git diff --check通过。',
           '- 本轮新增两类数据缺陷的失败：无效GE分拆比例；TFCF无母公司当日报价。修复为显式未解决项后重跑；没有修改信号参数来绕开。', '',
           '```sh', 'PYTHONPATH=. python3 scripts/prepare_p005_recipients.py',
           'python3 -m scripts.closeout --stage spinoff', 'python3 -m scripts.closeout --stage acquisition',
           f'python3 -m scripts.build_p005_report --spinoff-run runs/{spin.name} --acquisition-run runs/{acq.name}',
           f'python3 -m scripts.verify_p005 --spinoff-run runs/{spin.name} --acquisition-run runs/{acq.name}',
           'python3 -m unittest discover -s tests -v', 'git diff --check', '```', '',
           '全部原始/派生价格与完整场景账本保存在忽略版本控制的data/、runs/；摘要和冻结协议在docs/prototype/。准备脚本仅扫描已授权本地zip的对价报价，不改变候选池。', '',
           '## 收尾后工程范围', '',
           '保留可复现代码、缓存、报告、失败记录和目标约束。当前不启动新因子、风险调参、LEAPS、IBKR、影子运行、平台化数据库或产品界面。任何重启应单独提出能推翻停止决定的假设、验收标准、投入上限和退出条件，并获得用户明确授权。']
    Path('docs/prototype/p005-closeout-results.md').write_text('\n'.join(md)+'\n')
    print('Wrote P005 closeout metadata and report')


if __name__ == '__main__':
    main()
