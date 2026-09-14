"""Replay P004 with zero cash yield, using pinned local inputs and frozen rules.

Run: python3 -m scripts.cash_yield_sensitivity --source-run runs/<P004-run>
This is an accounting sensitivity, not a new signal or broker-rate assertion.
"""

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from vitalis.data import download, normalize
from vitalis.local_cache import read_cache
from vitalis.research_audit import (
    finish_catalog, pin_inputs, register_run, sha256_file, shift_month_end_inputs,
)
from vitalis.run import write_csv
from vitalis.run_pit import _init_simulate_worker, _simulate_cost_scenario
from vitalis.universe import security_master


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', required=True)
    parser.add_argument('--max-workers', type=int, default=4)
    parser.add_argument('--output-dir', default='runs')
    args = parser.parse_args()
    parent = Path(args.source_run)
    config = json.loads((parent / 'config.json').read_text())
    parent_manifest = json.loads((parent / 'manifest.json').read_text())
    if parent_manifest['status'] != 'completed':
        raise ValueError('Parent research run is not complete')
    inputs = {'parent_run_id': parent.name, 'parent_manifest_sha256': sha256_file(parent / 'manifest.json'),
              'cash_yield_assumption': 'zero', 'annual_fee_usd': 828,
              'capital_cost_cases': [[300000, 10], [200000, 10], [400000, 10], [200000, 25], [400000, 25]],
              'variants': ['M10', 'M20', 'M10-risk15', 'Q10', 'Q20']}
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-cash0-' + digest[:8]
    run = Path(args.output_dir) / run_id; run.mkdir(parents=True)
    (run / 'config.json').write_text(json.dumps(inputs, indent=2))
    manifest = {'run_id': run_id, 'status': 'starting', 'config_sha256': digest, 'remote_requests': 0}
    catalog = config['catalog_path']
    registry = config['registry_path']
    try:
        for row in parent_manifest['code_artifacts']:
            if sha256_file(Path('vitalis') / row['name']) != row['sha256']:
                raise ValueError('Parent code changed; do not silently replay different rules')
        source_paths = [Path(row['path']) for row in parent_manifest['source_artifacts']]
        source_paths += [parent / 'manifest.json']
        manifest['parent_inputs'] = []
        for name in ('universe_diagnostics.json', 'quality_details.json'):
            expected = next(r['sha256'] for r in parent_manifest['output_artifacts'] if r['path'] == name)
            if sha256_file(parent / name) != expected:
                raise ValueError('Parent derived input checksum mismatch')
            manifest['parent_inputs'].append({'path': str((parent / name).resolve()), 'sha256': expected})
        manifest.update(pin_inputs(run, source_paths, catalog))
        script = Path(__file__)
        (run / script.name).write_bytes(script.read_bytes())
        manifest['runner_sha256'] = sha256_file(script)
        (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        data_dir = Path(config['data_dir'])
        cache_key = parent_manifest['derived_cache_keys']['bars']
        cache_path = data_dir / 'derived-cache' / f'{cache_key}.json.gz'
        cached = read_cache(cache_path.parent, cache_key)
        if cached is None:
            raise FileNotFoundError('Pinned normalized cache is absent')
        manifest['derived_input'] = {'key': cache_key, 'sha256': sha256_file(cache_path)}
        bars = cached['bars']; del cached
        bars['QQQ'], _ = normalize(download('QQQ', config['data_start'], config['benchmark_data_end'],
                                            config['cache_dir'], offline=True))
        dates = sorted(bars['QQQ'])
        master = security_master(data_dir / 'tickers-bulk-full.csv.zip')
        ticker_info = {i['ticker']: i for i in master.values()}
        universe = json.loads((parent / 'universe_diagnostics.json').read_text())
        by_month = shift_month_end_inputs({r['month_end'][:7]:
            {t: ticker_info[t]['sector'] or 'Unknown' for t in r['selected']} for r in universe})
        quality_details = json.loads((parent / 'quality_details.json').read_text())
        quality = {m: {t: d['quality'] for t, d in rows.items()} for m, rows in quality_details.items()}
        sim_config = {'evaluation_start': config['evaluation_start'], 'evaluation_end': config['evaluation_end'],
                      'symbols': {}, 'minimum_adv_usd': 0, 'sector_weight_cap': config['sector_weight_cap'],
                      'volatility_target': .15, 'annual_system_cash_cost_usd': 828}
        tasks = [(capital, cost, 828, variant) for capital, cost in inputs['capital_cost_cases']
                 for variant in inputs['variants']]
        summaries = []
        with ProcessPoolExecutor(max_workers=args.max_workers, initializer=_init_simulate_worker,
                                 initargs=(bars, dates, sim_config, 300000, 10, {}, by_month, quality)) as pool:
            for task, result in pool.map(_simulate_cost_scenario, tasks):
                capital, cost, fee, variant = task
                summary, nav, trades, positions, decisions, warnings, contributions = result
                folder = run / f'{capital}-{cost}bps' / variant; folder.mkdir(parents=True)
                summary['cash_yield_assumption'] = 'zero'
                summaries.append(summary)
                for name, rows in [('nav', nav), ('trades', trades), ('holdings', positions),
                                   ('risk-flags', warnings), ('contributions', contributions)]:
                    write_csv(folder / f'{name}.csv', rows)
                (folder / 'decisions.json').write_text(json.dumps(decisions, indent=2))
        (run / 'summary.json').write_text(json.dumps(summaries, indent=2, allow_nan=False))
        (run / 'decision.json').write_text(json.dumps({'experiment_id': 'P004-cash-zero-sensitivity',
            'investment_decision': 'insufficient_evidence', 'inherits_parent_data_gaps': True,
            'limitations': ['Zero/FRED yields are scenarios, not verified broker terms.',
                            'All parent action/exit and metadata limitations apply.']}, indent=2))
        manifest['status'] = 'completed'
        manifest['output_artifacts'] = [{'path': str(p.relative_to(run)), 'sha256': sha256_file(p)}
            for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'manifest.json']
        for row in manifest['source_artifacts'] + manifest['parent_inputs']:
            if sha256_file(row['path']) != row['sha256']:
                raise ValueError('Pinned source changed during sensitivity replay')
        (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        finish_catalog(catalog, run_id, 'completed')
        register_run(registry, {'experiment_id': 'P004-cash-zero-sensitivity', 'run_id': run_id,
            'status': 'completed', 'config_sha256': digest, 'manifest_sha256': sha256_file(run / 'manifest.json'),
            'investment_decision': 'insufficient_evidence'})
        print(f'Wrote cash-yield sensitivity to {run}')
    except Exception as error:
        manifest.update(status='failed', error=f'{type(error).__name__}: {error}')
        (run / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        finish_catalog(catalog, run_id, 'failed')
        register_run(registry, {'experiment_id': 'P004-cash-zero-sensitivity', 'run_id': run_id,
                               'status': 'failed', 'error': manifest['error']})
        raise
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
