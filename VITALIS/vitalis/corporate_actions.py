"""Bounded local economic-action scenarios; vendor terms are not broker settlements."""

import bisect
import math
from collections import defaultdict


TRANSFER_TYPES = {'spinoff', 'acquisitioncash', 'acquisitionstock'}


def build_events(actions, dates, start, end, include_acquisitions=False):
    """Keep elections separate and flag them; never add mutually exclusive terms.

    Acquisition dates are last-trade dates in cached ACTIONTYPES, so apply on
    the following equity session. Ratios are interpreted as nominal event-date
    ratios per that dictionary. Actual delivery, rounding and tax are unknown.
    """
    groups = defaultdict(list)
    for ticker, rows in actions.items():
        for row in rows:
            if row['action'] in TRANSFER_TYPES or row['action'].startswith('acquisitionelect'):
                if start <= row['date'] <= end:
                    groups[(ticker, row['date'])].append(row)
    events, unresolved = defaultdict(list), []
    for (ticker, day), rows in sorted(groups.items()):
        spins = [r for r in rows if r['action'] == 'spinoff']
        for row in spins:
            ratio = float(row['value'])
            if not math.isfinite(ratio) or ratio <= 0 or row['contraticker'] in ('', 'N/A', ticker):
                unresolved.append({'symbol': ticker, 'source_date': day,
                                   'reason': 'invalid_or_nonproportional_spinoff_terms', 'terms': [row]})
                events[day].append({'kind': 'unresolved', 'symbol': ticker,
                                    'reason': 'invalid_or_nonproportional_spinoff_terms', 'source_date': day})
                continue
            events[day].append({'kind': 'spinoff', 'symbol': ticker,
                                'stock_terms': [{'symbol': row['contraticker'], 'ratio': ratio}],
                                'cash_per_share_usd': 0.0, 'source_date': day})
        if not include_acquisitions:
            continue
        merger_rows = [r for r in rows if r['action'].startswith('acquisition')]
        if not merger_rows:
            continue
        if any(r['action'].startswith('acquisitionelect') for r in merger_rows):
            unresolved.append({'symbol': ticker, 'source_date': day,
                               'reason': 'election_proration_or_alternative_unknown', 'terms': merger_rows})
            continue
        cash_rows = [r for r in merger_rows if r['action'] == 'acquisitioncash']
        stock_rows = [r for r in merger_rows if r['action'] == 'acquisitionstock']
        if len(cash_rows) > 1 or len(stock_rows) > 1:
            unresolved.append({'symbol': ticker, 'source_date': day,
                               'reason': 'multiple_terms_require_identity_resolution', 'terms': merger_rows})
            continue
        terms = [{'symbol': r['contraticker'], 'ratio': float(r['value'])} for r in stock_rows]
        cash = float(cash_rows[0]['value']) if cash_rows else 0.0
        if not math.isfinite(cash) or cash < 0 or any(
                not math.isfinite(r['ratio']) or r['ratio'] <= 0 or r['symbol'] in ('', 'N/A', ticker)
                for r in terms):
            raise ValueError(f'Invalid acquisition terms: {ticker} {day}')
        next_index = bisect.bisect_right(dates, day)
        if next_index < len(dates) and dates[next_index] <= end:
            events[dates[next_index]].append({'kind': 'acquisition', 'symbol': ticker,
                'stock_terms': terms, 'cash_per_share_usd': cash, 'source_date': day})
    return dict(events), unresolved


def entitlement(event, quantity, bars, day):
    """Resolve stocks, not dividend-value cash; unavailable quotes block this action."""
    shares = []
    for row in event['stock_terms']:
        symbol = row['symbol']
        if symbol not in bars or day not in bars[symbol]:
            raise ValueError(f'No recipient quote for {event["symbol"]}->{symbol} on {day}')
        shares.append((symbol, quantity * row['ratio']))
    cash = quantity * event['cash_per_share_usd']
    stock_value = sum(q * bars[s][day]['open'] for s, q in shares)
    return cash, shares, stock_value
