"""G2 audit of the SF2 insider table (docs/prototype/p009-smallcap-value-protocol.md).

Read-only. Measures disclosure timing against the real trading calendar,
amendment/restatement volume, de-duplicated event counts and transaction
nature. It does NOT reclassify the table's tier and does NOT feed any
ranking rule: `insiders` stays tier C until a separate registered decision.
"""
import bisect
import collections
import csv
import io
import json
import zipfile
from pathlib import Path

SF2 = Path('data/authorized/sharadar/insiders-bulk-full.csv.zip')
QQQ = Path('data/public-yahoo/QQQ-1999-01-01-2026-09-20.json')
PURCHASE_CODE = 'P'
REPORT_LAGS = (0, 1, 2, 3, 5, 10, 45)


def trading_sessions():
    """Real US equity sessions, taken from the QQQ snapshot's own bar dates."""
    from vitalis.data import normalize
    bars, issues = normalize(json.loads(QQQ.read_text()))
    if issues:
        raise ValueError(f'{len(issues)} invalid bars in the QQQ snapshot')
    return sorted(bars)


def sessions_between(sessions, earlier, later):
    """Trading sessions strictly after `earlier`, up to and including `later`."""
    return bisect.bisect_right(sessions, later) - bisect.bisect_right(sessions, earlier)


def main():
    sessions = trading_sessions()
    first_session, last_session = sessions[0], sessions[-1]

    forms = collections.Counter()
    purchase_rows = 0
    amended_purchase_rows = 0
    purchase_groups = set()
    derivative_flags = collections.Counter()
    session_lags = collections.Counter()
    filed_before_transaction = 0
    unpriced = 0
    out_of_calendar = 0

    with zipfile.ZipFile(SF2) as archive:
        with archive.open('insiders.csv') as handle:
            reader = csv.DictReader(io.TextIOWrapper(handle, 'utf-8'))
            for row in reader:
                form = (row.get('formtype') or '').strip()
                forms[form] += 1
                if (row.get('transactioncode') or '').strip() != PURCHASE_CODE:
                    continue
                purchase_rows += 1
                # Sharadar marks restatements as "RESTATED - 4", not the SEC's "4/A".
                if form.upper().startswith('RESTATED'):
                    amended_purchase_rows += 1
                filing, traded = row.get('date') or '', row.get('transactiondate') or ''
                if len(filing) == 10:
                    purchase_groups.add((row.get('ticker'), filing))
                derivative_flags[(row.get('securityadcode') or '').strip()[:1]] += 1
                if not (row.get('transactionpricepershare') or '').strip():
                    unpriced += 1
                if len(filing) == 10 and len(traded) == 10:
                    if filing < traded:
                        filed_before_transaction += 1
                    elif not (first_session <= traded and filing <= last_session):
                        out_of_calendar += 1
                    else:
                        session_lags[sessions_between(sessions, traded, filing)] += 1

    print(f'form types (all rows): {forms.most_common(6)}')
    print(f'\ntransactioncode = {PURCHASE_CODE}')
    print(f'  rows                                 {purchase_rows:>10,}')
    print(f'  distinct (ticker, filing date) groups{len(purchase_groups):>10,}')
    print(f'  rows on a RESTATED form            {amended_purchase_rows:>10,}'
          f'  ({amended_purchase_rows / purchase_rows * 100:.2f}%)')
    print(f'  rows with no transaction price       {unpriced:>10,}'
          f'  ({unpriced / purchase_rows * 100:.2f}%)')
    print(f'  filed BEFORE the transaction         {filed_before_transaction:>10,}'
          f'  ({filed_before_transaction / purchase_rows * 100:.3f}%)')
    print(f'  outside the QQQ session calendar     {out_of_calendar:>10,}')
    print(f'  securityadcode first char            {dict(derivative_flags.most_common(6))}')

    total = sum(session_lags.values())
    print(f'\ndisclosure lag in TRADING SESSIONS (n={total:,}):')
    cumulative = 0
    for lag in sorted(session_lags):
        cumulative += session_lags[lag]
        if lag in REPORT_LAGS:
            print(f'  <= {lag:2d} sessions: {cumulative / total * 100:5.1f}%')
    print('\nForm 4 is due within two BUSINESS days of the transaction; this table '
          'measures sessions, which is the right unit for a point-in-time rule but '
          'is not itself proof of compliance with that deadline.')
    print('Tier unchanged: insiders remains tier C and feeds no ranking rule.')


if __name__ == '__main__':
    main()
