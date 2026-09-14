"""Economic entitlement checks; synthetic fixtures do not establish source validity."""
import unittest
from unittest.mock import patch

from vitalis.corporate_actions import build_events, entitlement
from vitalis.engine import simulate


class CorporateActionTests(unittest.TestCase):
    dates = ['2024-12-31', '2025-01-02', '2025-01-03', '2025-01-06', '2025-01-07']

    def bars(self):
        return {s: {d: {'open': p, 'close': p, 'adjclose': p,
                        'split': 1, 'dividend': 0, 'dollar_volume': 1e8}
                    for d in self.dates} for s, p in [('A', 100), ('CHILD', 20)]}

    def run_case(self, bars, events, cost=0, end='2025-01-07'):
        config = {'evaluation_start': '2025-01-02', 'evaluation_end': end,
                  'symbols': {'A': 'x'}, 'minimum_adv_usd': 0, 'sector_weight_cap': 1,
                  'volatility_target': .15, 'annual_system_cash_cost_usd': 0}
        ranking = [{'symbol': 'A', 'rank': 1, 'score': 1}]
        with patch('vitalis.engine.rank_signals', return_value=ranking):
            return simulate(bars, self.dates, config, 10000, cost, 'M10',
                            corporate_actions_by_date=events)

    def test_spinoff_is_stock_and_next_open_sale_not_cash_dividend(self):
        bars = self.bars()
        for day in self.dates[2:]:
            bars['A'][day].update(open=90, close=90)
        bars['CHILD']['2025-01-06'].update(open=30, close=30)
        bars['CHILD']['2025-01-07'].update(open=30, close=30)
        event = {'kind': 'spinoff', 'symbol': 'A', 'cash_per_share_usd': 0,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': .5}], 'source_date': '2025-01-03'}
        summary, nav, trades, holdings, _, flags, contributions = self.run_case(
            bars, {'2025-01-03': [event]})
        self.assertEqual(nav[1]['nav_usd'], 10000)  # A loses 100; shares receive 100.
        self.assertEqual(nav[1]['cash_usd'], 9000)
        self.assertEqual(nav[1]['dividend_cash_usd'], 0)
        self.assertIn({'date': '2025-01-03', 'symbol': 'CHILD', 'quantity': 5, 'weight': .01}, holdings)
        disposal = next(t for t in trades if t.get('reason'))
        self.assertEqual((disposal['date'], disposal['quantity'], disposal['price_usd']),
                         ('2025-01-06', -5, 30))
        self.assertEqual(summary['ending_nav_usd'], 10050)
        self.assertEqual(sum(c['net_contribution_usd'] for c in contributions), 50)
        self.assertEqual(flags[0]['cash_consideration_usd'], 0)

    def test_cash_and_stock_merger_are_additive_replace_parent(self):
        bars = self.bars(); del bars['A']['2025-01-06']; del bars['A']['2025-01-07']
        event = {'kind': 'acquisition', 'symbol': 'A', 'cash_per_share_usd': 90,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': .5}], 'source_date': '2025-01-03'}
        summary, nav, trades, positions, _, flags, _ = self.run_case(bars, {'2025-01-06': [event]}, 10)
        self.assertFalse(any(f.get('flag') == 'forced_exit_data_discontinued' for f in flags))
        self.assertFalse(any(r['date'] == '2025-01-06' and r['symbol'] == 'A' for r in positions))
        self.assertTrue(any(t.get('reason') and t['date'] == '2025-01-07' for t in trades))
        self.assertGreater(summary['execution_cost_usd'], 0)
        self.assertEqual(nav[2]['corporate_action_pnl_usd'], 0)

    def test_election_terms_not_summed_or_used_as_plain_merger(self):
        rows = [{'action': 'acquisitionelectcash', 'date': '2025-01-03', 'value': '100', 'contraticker': 'CHILD'},
                {'action': 'acquisitionelectstock', 'date': '2025-01-03', 'value': '4', 'contraticker': 'CHILD'}]
        events, unresolved = build_events({'A': rows}, self.dates, '2025-01-02', '2025-01-07', True)
        self.assertEqual(events, {})
        self.assertEqual(len(unresolved), 1)
        rows[0]['action'] = 'acquisitioncash'; rows[1]['action'] = 'acquisitionstock'
        events, unresolved = build_events({'A': rows}, self.dates, '2025-01-02', '2025-01-07', True)
        e = events['2025-01-06'][0]
        cash, shares, value = entitlement(e, 10, self.bars(), '2025-01-06')
        self.assertEqual((cash, shares, value), (1000, [('CHILD', 40)], 800))

    def test_missing_recipient_quote_blocks_instead_of_cash_credit(self):
        e = {'symbol': 'A', 'stock_terms': [{'symbol': 'UNKNOWN', 'ratio': 1}], 'cash_per_share_usd': 0}
        with self.assertRaisesRegex(ValueError, 'No recipient quote'):
            entitlement(e, 10, self.bars(), '2025-01-03')

    def test_future_action_does_not_change_earlier_ledger(self):
        bars = self.bars()
        baseline = self.run_case(bars, {}, end='2025-01-03')
        event = {'kind': 'spinoff', 'symbol': 'A', 'cash_per_share_usd': 0,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': 999}], 'source_date': '2025-01-07'}
        later = self.run_case(bars, {'2025-01-07': [event]}, end='2025-01-03')
        self.assertEqual(baseline, later)

    def test_inherited_stock_split_preserves_value_and_disposal_quantity(self):
        bars = self.bars()
        bars['CHILD']['2025-01-06'].update(open=10, close=10, split=2)
        event = {'kind': 'spinoff', 'symbol': 'A', 'cash_per_share_usd': 0,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': .55}], 'source_date': '2025-01-03'}
        summary, _, trades, *_ = self.run_case(bars, {'2025-01-03': [event]})
        sale = next(t for t in trades if t.get('reason'))
        self.assertEqual((sale['quantity'], sale['price_usd']), (-11, 10))
        self.assertEqual(summary['ending_nav_usd'], 10110)

    def test_second_entitlement_does_not_sell_new_shares_with_old_batch(self):
        event = {'kind': 'spinoff', 'symbol': 'A', 'cash_per_share_usd': 0,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': .5}], 'source_date': '2025-01-03'}
        second = dict(event, source_date='2025-01-06')
        _, _, trades, holdings, *_ = self.run_case(self.bars(),
            {'2025-01-03': [event], '2025-01-06': [second]})
        sales = [t for t in trades if t.get('reason')]
        self.assertEqual([(t['date'], t['quantity']) for t in sales],
                         [('2025-01-06', -5), ('2025-01-07', -5)])
        self.assertEqual(next(r['quantity'] for r in holdings
                              if r['date'] == '2025-01-06' and r['symbol'] == 'CHILD'), 5)

    def test_invalid_spinoff_terms_remain_flagged_not_silently_dropped(self):
        row = {'action': 'spinoff', 'date': '2025-01-03', 'value': '0', 'contraticker': 'CHILD'}
        events, unresolved = build_events({'A': [row]}, self.dates, '2025-01-02', '2025-01-07')
        self.assertEqual(unresolved[0]['reason'], 'invalid_or_nonproportional_spinoff_terms')
        result = self.run_case(self.bars(), events)
        self.assertEqual(result[5][0]['flag'], 'corporate_action_unresolved')

    def test_disposal_preserves_existing_ordinary_child_position(self):
        bars = self.bars()
        config = {'evaluation_start': '2025-01-02', 'evaluation_end': '2025-01-07',
                  'symbols': {'A': 'x', 'CHILD': 'x'}, 'minimum_adv_usd': 0,
                  'sector_weight_cap': 1, 'volatility_target': .15, 'annual_system_cash_cost_usd': 0}
        event = {'kind': 'spinoff', 'symbol': 'A', 'cash_per_share_usd': 0,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': .5}], 'source_date': '2025-01-03'}
        ranking = [{'symbol': 'A', 'rank': 1}, {'symbol': 'CHILD', 'rank': 2}]
        with patch('vitalis.engine.rank_signals', return_value=ranking):
            result = simulate(bars, self.dates, config, 10000, 0, 'M10',
                              corporate_actions_by_date={'2025-01-03': [event]})
        self.assertEqual(next(r['quantity'] for r in result[3]
            if r['date'] == '2025-01-07' and r['symbol'] == 'CHILD'), 50)

    def test_spinoff_after_last_parent_quote_is_unresolved_not_double_credited(self):
        bars = self.bars()
        del bars['A']['2025-01-06']; del bars['A']['2025-01-07']
        event = {'kind': 'spinoff', 'symbol': 'A', 'cash_per_share_usd': 0,
                 'stock_terms': [{'symbol': 'CHILD', 'ratio': 1}], 'source_date': '2025-01-06'}
        result = self.run_case(bars, {'2025-01-06': [event]})
        self.assertEqual(result[0]['ending_nav_usd'], 10000)
        self.assertTrue(any(r.get('reason') == 'spinoff_date_has_no_parent_quote_or_conflicts_with_exit'
                            for r in result[5]))
        self.assertFalse(any(r['symbol'] == 'CHILD' for r in result[3]))


if __name__ == '__main__':
    unittest.main()
