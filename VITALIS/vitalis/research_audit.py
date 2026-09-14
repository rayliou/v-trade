"""Local research provenance and diagnostic checks; never acquires remote data."""

import hashlib
import json
import sqlite3
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def execution_month(month_end):
    day = date.fromisoformat(month_end)
    return f'{day.year + (day.month == 12):04d}-{day.month % 12 + 1:02d}'


def shift_month_end_inputs(values):
    """As-of month M belongs to execution month M+1, never M."""
    return {execution_month(month + '-01'): value for month, value in values.items()}


def pin_inputs(run, paths, catalog_path):
    """Verify actual files, freeze code, and register safe local metadata only.

    This is a snapshot/artifact catalog, not a claim that shared ingestion or
    rate-limit coordination is implemented. Raw provenance URLs are not copied.
    """
    artifacts = []
    for path in paths:
        path = Path(path)
        digest = sha256_file(path)  # missing input is a hard offline failure
        provenance = path.with_name(path.name.replace('.csv.zip', '.provenance.json'))
        if path.name.endswith('.csv.zip') and provenance.exists():
            declared = json.loads(provenance.read_text()).get('sha256')
            if declared and declared != digest:
                raise ValueError(f'Source hash mismatch: {path.name}')
        artifacts.append({'path': str(path.resolve()), 'bytes': path.stat().st_size,
                          'sha256': digest})
    code_dir = run / 'code'
    code_dir.mkdir()
    code = []
    for path in sorted(Path(__file__).parent.glob('*.py')):
        content = path.read_bytes()
        (code_dir / path.name).write_bytes(content)
        code.append({'name': path.name, 'sha256': hashlib.sha256(content).hexdigest()})
    catalog_path = Path(catalog_path)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(catalog_path)) as db, db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS snapshot (
                run_id TEXT PRIMARY KEY, created_at_utc TEXT NOT NULL,
                status TEXT NOT NULL, manifest_path TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifact (
                run_id TEXT NOT NULL REFERENCES snapshot(run_id),
                path TEXT NOT NULL, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL,
                PRIMARY KEY (run_id, path));
        ''')
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('INSERT INTO snapshot VALUES (?,?,?,?)',
                   (run.name, datetime.now(timezone.utc).isoformat(), 'pinned',
                    str((run / 'manifest.json').resolve())))
        db.executemany('INSERT INTO artifact VALUES (?,?,?,?)',
                       [(run.name, a['path'], a['sha256'], a['bytes']) for a in artifacts])
    return {'source_artifacts': artifacts, 'code_artifacts': code,
            'catalog_path': str(catalog_path.resolve())}


def finish_catalog(catalog_path, run_id, status):
    if Path(catalog_path).exists():
        with closing(sqlite3.connect(catalog_path)) as db, db:
            db.execute('UPDATE snapshot SET status=? WHERE run_id=?', (status, run_id))


def register_run(path, entry):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # CLI coordinator is the sole writer; parallel workers never write registry.
    with path.open('a') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + '\n')


def classify_bridge(issues, actions, evaluation_start, evaluation_end, exposure):
    """Action proximity is diagnostic context, not proof of correct settlement."""
    result = []
    for issue in issues:
        ticker, day = issue['ticker'], issue['date']
        center = date.fromisoformat(day)
        nearby = [r for r in actions.get(ticker, [])
                  if abs((date.fromisoformat(r['date']) - center).days) <= 3
                  and not r['action'].startswith('sicchange')]
        types = sorted({r['action'] for r in nearby})
        in_eval = evaluation_start <= day <= evaluation_end
        if not in_eval:
            category = 'outside_evaluation'
        elif any('spinoff' in a for a in types):
            category = 'spinoff_context_unresolved'
        elif 'split' in types:
            category = 'split_context_unresolved'
        elif 'dividend' in types:
            category = 'dividend_context_unresolved'
        else:
            category = 'no_matching_action_unresolved'
        held = sorted(v for v, ticker_days in exposure.items()
                      if day in ticker_days.get(ticker, set()))
        result.append({**issue, 'difference_pp':
                       (issue['cash_action_return'] - issue['adjusted_return']) * 100,
                       'in_evaluation': in_eval, 'category': category,
                       'nearby_actions': nearby, 'held_variants': held,
                       'resolved': False})
    return result


def held_event_dates(holdings, dates):
    """Include prior-session holdings, which receive overnight corporate actions."""
    following = dict(zip(dates, dates[1:]))
    result = defaultdict(set)
    for row in holdings:
        if row['quantity'] <= 0:
            continue
        result[row['symbol']].add(row['date'])
        if row['date'] in following:
            result[row['symbol']].add(following[row['date']])
    return result


def diagnose_ledger(nav, contributions, capital, reference_nav, holdings, sector_by_ticker,
                    quality_details=None):
    if [r['date'] for r in nav] != [r['date'] for r in reference_nav]:
        raise ValueError('Diagnostic benchmark dates differ')
    annual, periods = [], []
    groups = defaultdict(list)
    for i, row in enumerate(nav):
        groups[row['date'][:4]].append(i)
    for label, indices in groups.items():
        a, b = indices[0], indices[-1]
        start = nav[a - 1]['nav_usd'] if a else capital
        ref_start = reference_nav[a - 1]['nav_usd'] if a else capital
        sr = nav[b]['nav_usd'] / start - 1
        br = reference_nav[b]['nav_usd'] / ref_start - 1
        annual.append({'year': label, 'return': sr, 'qqq_return': br,
                       'relative_return_pp': (sr - br) * 100,
                       'average_cash_weight': sum(nav[i]['cash_usd'] / nav[i]['nav_usd']
                                                  for i in indices) / len(indices)})
    for label, lower, upper in [('2005-2014', '2005', '2014'), ('2015-2025', '2015', '2025')]:
        indices = [i for i, r in enumerate(nav) if lower <= r['date'][:4] <= upper]
        if not indices:
            continue
        a, b = indices[0], indices[-1]
        start = nav[a - 1]['nav_usd'] if a else capital
        ref_start = reference_nav[a - 1]['nav_usd'] if a else capital
        n = len(indices)
        s = (nav[b]['nav_usd'] / start) ** (252 / n) - 1
        q = (reference_nav[b]['nav_usd'] / ref_start) ** (252 / n) - 1
        periods.append({'period': label, 'cagr': s, 'qqq_cagr': q, 'excess_cagr_pp': (s - q) * 100})
    rolling = []
    for i in range(755, len(nav)):
        if i != len(nav) - 1 and nav[i]['date'][:7] == nav[i + 1]['date'][:7]:
            continue
        prior = i - 756
        start = nav[prior]['nav_usd'] if prior >= 0 else capital
        ref_start = reference_nav[prior]['nav_usd'] if prior >= 0 else capital
        rolling.append({'end_date': nav[i]['date'], 'excess_cagr_pp':
                        ((nav[i]['nav_usd'] / start) ** (1 / 3) -
                         (reference_nav[i]['nav_usd'] / ref_start) ** (1 / 3)) * 100})
    pos = sum(max(0, r['net_contribution_usd']) for r in contributions)
    neg = sum(max(0, -r['net_contribution_usd']) for r in contributions)
    top = sorted(contributions, key=lambda r: -r['net_contribution_usd'])[:5]
    sector = defaultdict(float)
    for row in contributions:
        sector[sector_by_ticker.get(row['symbol'], 'Unknown')] += row['net_contribution_usd']
    na_weights = defaultdict(float)
    daily_weights = defaultdict(list)
    for row in holdings:
        daily_weights[row['date']].append(row['weight'])
        if quality_details is not None:
            detail = quality_details.get(row['date'][:7], {}).get(row['symbol'])
            if detail is None or detail['na']:
                na_weights[row['date']] += row['weight']
    n = len(nav)
    return {'annual': annual, 'periods': periods, 'rolling_36m': rolling,
            'average_cash_weight': sum(r['cash_usd'] / r['nav_usd'] for r in nav) / n,
            'average_position_hhi': sum(sum(w*w for w in daily_weights.get(r['date'], []))
                                        for r in nav) / n,
            'top5_positive_contributors': top,
            'top5_positive_share': sum(max(0, r['net_contribution_usd']) for r in top) / pos if pos else None,
            'positive_contribution_hhi': sum((max(0, r['net_contribution_usd']) / pos)**2
                                              for r in contributions) if pos else None,
            'negative_contribution_hhi': sum((max(0, -r['net_contribution_usd']) / neg)**2
                                              for r in contributions) if neg else None,
            'sector_contribution_current_labels_usd': dict(sector),
            'average_quality_na_nav_weight': sum(na_weights.values()) / n if quality_details is not None else None,
            'ledger_reconciled': all(abs(r['pnl_usd'] - (r['price_pnl_usd'] +
                 r['dividend_cash_usd'] + r['cash_interest_usd'] -
                 r['fixed_fee_usd'] - r['execution_cost_usd'])) < 1e-5 for r in nav),
            'limitations': ['Historical diagnostics, not untouched validation.',
                           'Sector attribution uses current labels.',
                           'Dollar contributions depend on portfolio wealth over time.',
                           'Quality N/A is neutral fallback, not a qualified company.']}
