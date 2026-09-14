"""Independent P005 artifact, output-ledger and frozen-code verification."""
import argparse
import csv
import json
import math
from pathlib import Path

from vitalis.research_audit import sha256_file


def verify_run(path):
    path = Path(path)
    manifest = json.loads((path / 'manifest.json').read_text())
    if manifest['status'] != 'completed' or manifest['remote_requests'] != 0:
        raise ValueError('Incomplete or non-offline closeout')
    for row in manifest['source_artifacts']:
        if sha256_file(row['path']) != row['sha256']:
            raise ValueError('Pinned source changed')
    for row in manifest['output_artifacts']:
        if sha256_file(path / row['path']) != row['sha256']:
            raise ValueError('Output artifact changed')
    for row in manifest['code_artifacts']:
        if sha256_file(Path('vitalis') / row['name']) != row['sha256']:
            raise ValueError('Live/frozen code differs')
    summaries = json.loads((path / 'summary.json').read_text())
    dates_checked = 0
    for summary in summaries:
        folder = path / summary['cash_yield_assumption'] / f"{summary['capital_usd']}-{summary['cost_bps']}bps" / summary['variant']
        nav = list(csv.DictReader((folder / 'nav.csv').open()))
        prior = summary['capital_usd']; fixed = interest = 0.0
        for row in nav:
            expected = (float(row['price_pnl_usd']) + float(row['corporate_action_pnl_usd'])
                + float(row['dividend_cash_usd']) + float(row['cash_interest_usd'])
                - float(row['execution_cost_usd']) - float(row['fixed_fee_usd']))
            observed = float(row['nav_usd']) - prior
            if not math.isclose(expected, observed, rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError('Published daily PNL fails independent reconciliation')
            if not math.isclose(float(row['cash_usd']) + float(row['stock_value_usd']),
                                float(row['nav_usd']), rel_tol=1e-9, abs_tol=1e-6):
                raise ValueError('Published cash/stock balance fails')
            if float(row['cash_usd']) < -1e-6:
                raise ValueError('Published negative cash')
            fixed += float(row['fixed_fee_usd']); interest += float(row['cash_interest_usd'])
            prior = float(row['nav_usd']); dates_checked += 1
        contributions = list(csv.DictReader((folder / 'contributions.csv').open()))
        total = 0.0
        for row in contributions:
            derived = float(row['price_pnl_usd']) + float(row['dividends_usd']) - float(row['execution_cost_usd']) + float(row.get('corporate_action_pnl_usd') or 0)
            if not math.isclose(derived, float(row['net_contribution_usd']), rel_tol=1e-9, abs_tol=1e-5):
                raise ValueError('Published contributor components fail')
            total += derived
        if not math.isclose(total - fixed + interest, prior - summary['capital_usd'], rel_tol=1e-9, abs_tol=1e-5):
            raise ValueError('Published contributor wealth fails')
        if not math.isclose(prior, summary['ending_nav_usd'], rel_tol=1e-9, abs_tol=1e-6):
            raise ValueError('Summary does not match ending ledger')
    return {'run_id': path.name, 'manifest_sha256': sha256_file(path / 'manifest.json'),
            'scenario_count': len(summaries), 'daily_rows_checked': dates_checked,
            'source_checksums': True, 'output_checksums': True, 'code_identity': True,
            'independent_pnl_and_wealth_reconciliation': True, 'remote_requests': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spinoff-run', required=True)
    parser.add_argument('--acquisition-run', required=True)
    args = parser.parse_args()
    results = {'verification_script_sha256': sha256_file(__file__),
               'runs': [verify_run(args.spinoff_run), verify_run(args.acquisition_run)],
               'scope': 'Artifact and accounting identities only; economic/PIT gates remain unverified.'}
    Path('docs/prototype/p005-verification.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
