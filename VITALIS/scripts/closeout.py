"""P005 fixed-rule economic accounting closeout; pinned local data only.

python3 -m scripts.closeout --stage spinoff
python3 -m scripts.closeout --stage acquisition
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from vitalis.corporate_actions import build_events
from vitalis.data import download, normalize
from vitalis.engine import simulate
from vitalis.local_cache import read_cache
from vitalis.macro import daily_rate_by_trading_day, download_series, normalize_series
from vitalis.research_audit import finish_catalog, pin_inputs, register_run, sha256_file, shift_month_end_inputs
from vitalis.run import write_csv
from vitalis.run_pit import _load_ticker_rows
from vitalis.sharadar_prices import normalize_ticker
from vitalis.universe import security_master

_SHARED = None


def init_worker(bars, dates, config, rates, universe, quality, events):
    global _SHARED
    _SHARED = bars, dates, config, rates, universe, quality, events


def worker(task):
    capital, cost, yield_name, variant = task
    bars, dates, config, rates, universe, quality, events = _SHARED
    result = simulate(bars, dates, config, capital, cost, variant,
                      cash_annual_rate=rates if yield_name == 'FRED' else {},
                      symbols_by_review_month=universe, quality_by_review_month=quality,
                      corporate_actions_by_date=events)
    return task, result


def verified_json(parent, manifest, name):
    expected = next(r['sha256'] for r in manifest['output_artifacts'] if r['path'] == name)
    if sha256_file(parent / name) != expected:
        raise ValueError(f'Parent output checksum mismatch: {name}')
    return json.loads((parent / name).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['spinoff', 'acquisition'], required=True)
    parser.add_argument('--source-run', default='runs/20260913T230115679698Z-pit-170d681b')
    parser.add_argument('--max-workers', type=int, default=4)
    args = parser.parse_args()
    parent = Path(args.source_run)
    protocol_path = Path('docs/prototype/p005-closeout-protocol.json')
    protocol = json.loads(protocol_path.read_text())
    if parent.name != protocol['parent_run_id']:
        raise ValueError('P005 parent must match preregistration')
    parent_manifest = json.loads((parent / 'manifest.json').read_text())
    if parent_manifest['status'] != 'completed':
        raise ValueError('Parent is incomplete')
    source_config = json.loads((parent / 'config.json').read_text())
    run_config = {'experiment_id': f'P005-{args.stage}', 'protocol_sha256': sha256_file(protocol_path),
                  'parent_manifest_sha256': sha256_file(parent / 'manifest.json'),
                  'stage': args.stage, 'max_workers': args.max_workers,
                  'variants': protocol['variants'], 'capital_cost_cases': protocol['capital_cost_cases'],
                  'cash_yield_scenarios': protocol['cash_yield_scenarios'], 'annual_fee_usd': protocol['annual_fee_usd']}
    digest = hashlib.sha256(json.dumps(run_config, sort_keys=True).encode()).hexdigest()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-p005-' + args.stage + '-' + digest[:8]
    run = Path('runs') / run_id; run.mkdir()
    (run / 'config.json').write_text(json.dumps(run_config, indent=2))
    manifest = {'run_id': run_id, 'status': 'starting', 'config_sha256': digest, 'remote_requests': 0}
    catalog = source_config['catalog_path']; registry = source_config['registry_path']
    try:
        data_dir = Path(source_config['data_dir'])
        cache_key = parent_manifest['derived_cache_keys']['bars']
        cache_path = data_dir / 'derived-cache' / f'{cache_key}.json.gz'
        addon_path = data_dir / 'p005-recipient-source-rows.json'
        addon_metadata = addon_path.with_suffix('.metadata.json')
        sources = [Path(r['path']) for r in parent_manifest['source_artifacts']]
        sources += [parent / 'manifest.json', parent / 'universe_diagnostics.json', parent / 'quality_details.json',
                    cache_path, cache_path.with_suffix('.metadata.json'), protocol_path, addon_path, addon_metadata,
                    data_dir / 'p005-recipient-cache-builder.py', Path(__file__)]
        manifest.update(pin_inputs(run, sources, catalog))
        # Every inherited source must still be the parent's actual pinned file.
        for row in parent_manifest['source_artifacts']:
            if sha256_file(row['path']) != row['sha256']:
                raise ValueError('Parent source changed')
        (run / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
        manifest['runner_sha256'] = sha256_file(__file__)
        (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        bars = read_cache(cache_path.parent, cache_key)['bars']
        candidate_set = set(bars)
        addon = json.loads(addon_path.read_text()); meta = json.loads(addon_metadata.read_text())
        checks = {'source_sha256': data_dir / 'stocks-bulk-full.csv.zip',
                  'actions_sha256': data_dir / 'actions-bulk-full.csv.zip',
                  'payload_sha256': addon_path, 'builder_sha256': data_dir / 'p005-recipient-cache-builder.py',
                  'parent_manifest_sha256': parent / 'manifest.json'}
        if any(sha256_file(path) != meta[key] for key, path in checks.items()):
            raise ValueError('Recipient cache lineage mismatch')
        actions = _load_ticker_rows(data_dir / 'actions-bulk-full.csv.zip', candidate_set | set(addon['rows']))
        addon_issues = []
        for symbol, rows in addon['rows'].items():
            bars[symbol], issues = normalize_ticker(rows, actions[symbol])
            addon_issues.extend({'symbol': symbol, **r} for r in issues)
        bars['QQQ'], _ = normalize(download('QQQ', source_config['data_start'], source_config['benchmark_data_end'],
                                           source_config['cache_dir'], offline=True))
        dates = sorted(bars['QQQ'])
        events, unresolved = build_events({t: actions[t] for t in candidate_set}, dates,
            source_config['evaluation_start'], source_config['evaluation_end'], args.stage == 'acquisition')
        master = security_master(data_dir / 'tickers-bulk-full.csv.zip')
        ticker_info = {r['ticker']: r for r in master.values()}
        diagnostics = verified_json(parent, parent_manifest, 'universe_diagnostics.json')
        universe = shift_month_end_inputs({r['month_end'][:7]:
            {t: ticker_info[t]['sector'] or 'Unknown' for t in r['selected']} for r in diagnostics})
        details = verified_json(parent, parent_manifest, 'quality_details.json')
        quality = {m: {t: d['quality'] for t, d in rows.items()} for m, rows in details.items()}
        sim_config = {'evaluation_start': source_config['evaluation_start'], 'evaluation_end': source_config['evaluation_end'],
                      'symbols': {}, 'minimum_adv_usd': 0, 'sector_weight_cap': source_config['sector_weight_cap'],
                      'volatility_target': .15, 'annual_system_cash_cost_usd': protocol['annual_fee_usd']}
        rates = daily_rate_by_trading_day(normalize_series(download_series('DGS3MO', source_config['data_start'],
             source_config['benchmark_data_end'], source_config['fred_cache_dir'], offline=True)), dates)
        (run / 'action-plan.json').write_text(json.dumps({'events': events, 'unresolved': unresolved,
             'recipient_bar_issues': addon_issues, 'recipient_bar_rows': sum(len(x) for x in addon['rows'].values()),
             'recipient_symbols_for_entitlement_only': sorted(addon['rows'])}, indent=2))
        # Check unchanged accounting path against all five parent real-fee cases.
        if args.stage == 'spinoff':
            identity = {}
            for variant in protocol['variants']:
                result = simulate(bars, dates, sim_config, 300000, 10, variant, rates, universe, quality)
                old_folder = parent / 'cost-scenarios' / '300000-10bps-828fee' / variant
                for name, rows in [('nav', result[1]), ('trades', result[2]), ('holdings', result[3])]:
                    target = run / f'identity-{variant}-{name}.csv'; write_csv(target, rows)
                    identity[f'{variant}/{name}'] = sha256_file(target) == sha256_file(old_folder / f'{name}.csv')
                # Ranking is re-evaluated as before; all frozen input rules are identical.
            (run / 'baseline-identity.json').write_text(json.dumps(identity, indent=2))
            if not all(identity.values()):
                raise ValueError('Non-action engine behavior changed')
        tasks = [(capital, cost, yield_name, variant) for capital, cost in protocol['capital_cost_cases']
                 for yield_name in protocol['cash_yield_scenarios'] for variant in protocol['variants']]
        summaries = []; counts = []
        with ProcessPoolExecutor(max_workers=args.max_workers, initializer=init_worker,
                                 initargs=(bars, dates, sim_config, rates, universe, quality, events)) as pool:
            for task, result in pool.map(worker, tasks):
                capital, cost, yield_name, variant = task
                summary, nav, trades, positions, decisions, warnings, contributions = result
                summary.update(cash_yield_assumption=yield_name, stage=args.stage)
                folder = run / yield_name / f'{capital}-{cost}bps' / variant; folder.mkdir(parents=True)
                summaries.append(summary)
                for name, rows in [('nav', nav), ('trades', trades), ('holdings', positions),
                                   ('risk-flags', warnings), ('contributions', contributions)]:
                    write_csv(folder / f'{name}.csv', rows)
                (folder / 'decisions.json').write_text(json.dumps(decisions, indent=2))
                counter = Counter(w['flag'] for w in warnings)
                counts.append({'capital_usd': capital, 'cost_bps': cost, 'yield': yield_name,
                               'variant': variant, 'events': dict(counter),
                               'corporate_actions': [w for w in warnings if w['flag'].startswith('corporate_')],
                               'unresolved_exits': [w for w in warnings if w['flag'] == 'forced_exit_data_discontinued']})
                print(f'{args.stage}: {capital}/{cost}/{yield_name}/{variant} complete', flush=True)
        (run / 'summary.json').write_text(json.dumps(summaries, indent=2, allow_nan=False))
        (run / 'accounting-audit.json').write_text(json.dumps(counts, indent=2))
        ref = next(r for r in verified_json(parent, parent_manifest, 'summary.json') if r['variant'] == 'QQQ-total-return-proxy')
        passed = [r for r in summaries if r['cagr'] > ref['cagr'] and r['max_drawdown'] >= -.30]
        decision = {'experiment_id': run_config['experiment_id'], 'engineering_status': 'completed',
            'joint_point_pass_cases': len(passed), 'investment_decision': 'insufficient_evidence',
            'project_action': 'stop_current_equity_alpha_development' if args.stage == 'acquisition' else 'complete_registered_acquisition_stage',
            'data_gate_pass': False, 'limitations': ['Action ratios are interpreted per cached vendor dictionary, not verified broker entitlements.',
                'Settlement/delivery dates, fractional cash-in-lieu and taxes are scenarios; disposal assumes next-session execution.',
                'Election-only exits retain flagged last-price proxy; no proration/alternative invented.',
                'Parent adjusted-signal bridges and historical metadata limits remain; inspected history is not untouched validation.']}
        (run / 'decision.json').write_text(json.dumps(decision, indent=2))
        for row in manifest['source_artifacts']:
            if sha256_file(row['path']) != row['sha256']:
                raise ValueError('Pinned input changed during closeout')
        for row in manifest['code_artifacts']:
            if sha256_file(Path('vitalis') / row['name']) != row['sha256']:
                raise ValueError('Live code changed during closeout')
        manifest['status'] = 'completed'
        manifest['output_artifacts'] = [{'path': str(p.relative_to(run)), 'sha256': sha256_file(p)}
            for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'manifest.json']
        (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        finish_catalog(catalog, run_id, 'completed')
        register_run(registry, {'experiment_id': run_config['experiment_id'], 'run_id': run_id,
            'status': 'completed', 'config_sha256': digest, 'manifest_sha256': sha256_file(run / 'manifest.json'),
            'investment_decision': 'insufficient_evidence', 'project_action': decision['project_action']})
        print(f'Wrote {run}', flush=True)
    except Exception as error:
        manifest.update(status='failed', error=f'{type(error).__name__}: {error}')
        (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        finish_catalog(catalog, run_id, 'failed')
        register_run(registry, {'experiment_id': run_config['experiment_id'], 'run_id': run_id,
                               'status': 'failed', 'error': manifest['error']})
        raise
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
