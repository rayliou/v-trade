"""Read-only re-audit of P005/P006 results and forward project economics.

No simulation, parameter search, remote request, or change to prior run artifacts.
"""
import csv
import json
import math
from pathlib import Path

from vitalis.research_audit import sha256_file


PARENT = Path('runs/20260913T230115679698Z-pit-170d681b')
FINAL = Path('runs/20260913T232207552486Z-p005-acquisition-b01d22c4')
P006 = Path('docs/prototype/p006-metadata.json')
P007 = Path('docs/prototype/p007-strategy-design.md')


def checked_json(run, name, manifest):
    row = next(r for r in manifest['output_artifacts'] if r['path'] == name)
    if sha256_file(run / name) != row['sha256']:
        raise ValueError(f'Output changed: {run.name}/{name}')
    return json.loads((run / name).read_text())


def audit():
    manifest = json.loads((FINAL / 'manifest.json').read_text())
    pm = json.loads((PARENT / 'manifest.json').read_text())
    assert manifest['status'] == pm['status'] == 'completed'
    summaries = checked_json(FINAL, 'summary.json', manifest)
    config = checked_json(FINAL, 'config.json', manifest)
    original = checked_json(PARENT, 'summary.json', pm)
    p006 = json.loads(P006.read_text())
    reference = next(r for r in original if r['variant'] == 'QQQ-total-return-proxy')
    expected = {(a, b, y, v) for a, b in config['capital_cost_cases']
                for y in config['cash_yield_scenarios'] for v in config['variants']}
    assert len(summaries) == len(expected) == 50
    assert {(r['capital_usd'], r['cost_bps'], r['cash_yield_assumption'], r['variant'])
            for r in summaries} == expected
    hashes = {r['path']: r['sha256'] for r in manifest['output_artifacts']}
    results = []
    for r in summaries:
        rel = f"{r['cash_yield_assumption']}/{r['capital_usd']}-{r['cost_bps']}bps/{r['variant']}/nav.csv"
        assert sha256_file(FINAL / rel) == hashes[rel]
        nav = list(csv.DictReader((FINAL / rel).open()))
        initial = r['capital_usd']; high = initial; worst = 0
        assert len(nav) == r['sessions'] == 5283
        assert (nav[0]['date'], nav[-1]['date']) == ('2005-01-03', '2025-12-31')
        for row in nav:
            value = float(row['nav_usd']); high = max(high, value)
            worst = min(worst, value / high - 1)
        cagr = (float(nav[-1]['nav_usd']) / initial) ** (252 / len(nav)) - 1
        assert math.isclose(cagr, r['cagr'], abs_tol=1e-12)
        assert math.isclose(worst, r['max_drawdown'], abs_tol=1e-12)
        # Same TR path: adjust only initial execution fee to the case's 10/25 bps.
        benchmark_cagr = (1 + reference['cagr']) * (
            (1 + reference['cost_bps'] / 10000) / (1 + r['cost_bps'] / 10000)
        ) ** (252 / len(nav)) - 1
        results.append({'variant': r['variant'], 'capital_usd': initial,
                        'cost_bps': r['cost_bps'], 'cash_yield': r['cash_yield_assumption'],
                        'cagr': cagr, 'max_drawdown': worst,
                        'qqq_cagr_matched_cost': benchmark_cagr,
                        'excess_cagr_pp': (cagr - benchmark_cagr) * 100,
                        'return_pass': cagr > benchmark_cagr, 'risk_pass': worst >= -.30})
    economics = []
    # Prospective illustrative costs only: do not amortize sunk work into this decision.
    for capital in [200000, 400000]:
        for label, build_hours, maintenance_hours in [('data_only', 0, 0),
                ('data_plus_maintenance', 0, 20), ('additional_build_first_year', 80, 20)]:
            cost = 828 + (build_hours + maintenance_hours) * 50
            economics.append({'capital_usd': capital, 'scenario': label,
                'data_fee_usd': 828, 'illustrative_additional_build_hours': build_hours,
                'illustrative_maintenance_hours': maintenance_hours, 'illustrative_hourly_value_usd': 50,
                'prospective_cost_usd': cost, 'break_even_pre_fixed_fee_excess_pp': cost / capital * 100,
                'hypothetical_1pp_net_value_usd': capital * .01 - cost,
                'hypothetical_2pp_net_value_usd': capital * .02 - cost})
    primary = [r for r in results if r['capital_usd'] == 300000 and r['cash_yield'] == 'FRED']
    p006_variants = {r['variant']: r for r in p006['summary'] if r['variant'] in ('H3', 'H5')}
    assert set(p006_variants) == {'H3', 'H5'}
    assert not p006['decision']['data_gate_pass']
    assert not p006['decision']['joint_sample_pass_variants']
    assert p006_variants['H3']['ending_nav_usd'] == 0.0
    assert p006_variants['H5']['max_drawdown'] < -0.99
    return {'review_id': 'R010-project-viability', 'asof_date': '2026-09-17',
        'reviewed_git_checkpoint': 'c15d5e77c1ffe018c78579b0e8aead8411c09e4d',
        'decision_basis': ('Fresh P005 ledger calculations plus direct checks of P006 metadata and '
                           'P007 implementation status; prior project_action text is not used as evidence.'),
        'source_manifest_sha256': {'P004': sha256_file(PARENT / 'manifest.json'),
                                   'P005': sha256_file(FINAL / 'manifest.json'),
                                   'P006_metadata': sha256_file(P006),
                                   'P007_design': sha256_file(P007)},
        'audit_script_sha256': sha256_file(__file__), 'scenario_count': len(results),
        'strategy_variants': config['variants'], 'independent_trials_claimed': False,
        'return_pass_count': sum(r['return_pass'] for r in results),
        'risk_pass_count': sum(r['risk_pass'] for r in results),
        'joint_pass_count': sum(r['return_pass'] and r['risk_pass'] for r in results),
        'best_case_cagr': max(r['cagr'] for r in results),
        'best_case_drawdown': max(r['max_drawdown'] for r in results),
        'primary_results': primary, 'all_cases': results, 'forward_cost_scenarios': economics,
        'risk_matched_qqq_control_p004': next(r for r in original if r['variant'] == 'QQQ-cash15'),
        'p006': {
            'hypothesis_verdict': 'rejected',
            'formal_investment_validity': p006['decision']['investment_decision'],
            'data_gate_pass': p006['decision']['data_gate_pass'],
            'acceptance_blockers': p006['decision']['acceptance_blockers'],
            'variants': [p006_variants['H3'], p006_variants['H5']],
        },
        'p007': {
            'status': 'frozen_unexecuted',
            'implemented_only': ['21-session zero-risk-free-rate Sharpe ranking', 'H3S/H5S variants'],
            'not_implemented': ['ORATS adapter', 'options-volume filter',
                                'options-sentiment diagnostics', 'P007 full backtest'],
            'investment_result_available': False,
            'orats_subscription_authorized': False,
            'reason': ('Proposed data cost exceeds the USD 1,000 annual cap; inherited 50% drawdown '
                       'criterion conflicts with the standing approximately 30% research limit.'),
        },
        'standing_constraints': {'annual_data_fee_cap_usd': 1000,
                                 'target_max_drawdown_approx': -0.30,
                                 'priority': 'net_return_above_QQQ'},
        'limitations': ['Existing ledger values recomputed, not independent market-source authentication.',
            'Remaining actions, historical metadata, taxes and actual broker execution unverified.',
            '50 cases are related variants and sensitivities, not 50 independent validations.',
            'Cost hours and future +1/+2pp are illustrations, not forecasts or actual time records.',
            '200k/400k assumes full capital allocation; actual strategy allocation unknown.'],
        'recommendation': 'freeze_entire_current_project_including_p007_and_stop_incremental_development',
        'investment_validity': 'insufficient_evidence', 'scientific_claim_all_factors_invalid': False,
        'new_strategy_runs_during_r010_review': 0, 'remote_market_data_requests': 0}


def main():
    result = audit()
    path = Path('docs/review/10-project-viability-evidence.json')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['scenario_count', 'return_pass_count', 'risk_pass_count',
          'joint_pass_count', 'best_case_cagr', 'best_case_drawdown', 'primary_results',
          'forward_cost_scenarios']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
