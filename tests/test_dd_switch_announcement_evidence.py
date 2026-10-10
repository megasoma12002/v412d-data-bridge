import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dd_switch_announcement_evidence as evidence


class AnnouncementEvidenceTests(unittest.TestCase):
    def versions(self):
        return [dict(event_id='0050:cash:test', code='0050', stage='ESTIMATE_SCHEDULE',
                     reported_at='2025-07-01T17:08:41+08:00', ex_date='2025-07-21',
                     payment_date='2025-08-08', estimated_amount=.3),
                dict(event_id='0050:cash:test', code='0050', stage='FINAL',
                     reported_at='2025-07-17T16:48:30+08:00', ex_date='2025-07-21',
                     payment_date='2025-08-08', amount=.36)]

    def test_same_day_after_close_publication_is_not_visible_at_close(self):
        self.assertEqual(evidence.research_snapshot(self.versions(), '2025-07-01T13:30:00+08:00'), [])
        row = evidence.research_snapshot(self.versions(), '2025-07-01T18:00:00+08:00')[0]
        self.assertNotIn('amount', row)
        self.assertEqual(row['estimated_amount'], .3)
        self.assertFalse(row['publication_vintage_certified'])

    def test_final_amount_not_backdated_to_estimate(self):
        before = evidence.research_snapshot(self.versions(), '2025-07-17T13:30:00+08:00')[0]
        self.assertNotIn('amount', before)
        after = evidence.research_snapshot(self.versions(), '2025-07-17T16:48:30+08:00')[0]
        self.assertEqual(after['amount'], .36)

    def test_future_amendment_does_not_change_prefix(self):
        rows = self.versions()
        expected = evidence.research_snapshot(rows, '2025-07-17T18:00:00+08:00')
        amendment = copy.deepcopy(rows[-1])
        amendment.update(reported_at='2025-07-18T09:00:00+08:00', amount=99, payment_date='2025-08-09')
        self.assertEqual(evidence.research_snapshot(rows + [amendment], '2025-07-17T18:00:00+08:00'), expected)
        self.assertEqual(evidence.research_snapshot(rows + [amendment], '2025-07-18T09:00:00+08:00')[0]['amount'], 99)

    def test_timezone_aware_order_and_missing_timestamp(self):
        rows = self.versions()
        amendment = copy.deepcopy(rows[-1])
        amendment.update(reported_at='2025-07-17T10:00:00+00:00', amount=.4)
        missing = copy.deepcopy(amendment)
        missing.pop('reported_at')
        missing['amount'] = 100
        self.assertEqual(evidence.research_snapshot(rows + [amendment, missing], '2025-07-17T19:00:00+08:00')[0]['amount'], .4)
        with self.assertRaises(ValueError):
            evidence.research_snapshot(rows, '2025-07-17T19:00:00')

    def test_fact_conflicts_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row = dict(code='0050', stage='FINAL', amount=.36,
                       source_url='https://www.twse.com.tw/zh/ETFortune/announcement?company=A00005&date=20250717&fund=0050&seq=1')
            (root / 'announcement_facts_1.json').write_text(json.dumps([row]))
            (root / 'announcement_facts_2.json').write_text(json.dumps([dict(row, amount=1)]))
            with patch.object(evidence, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Conflicting primary facts'):
                    evidence.load_facts(root)

    def test_checked_in_0050_coverage_is_complete_but_not_certified(self):
        facts, _ = evidence.load_facts(evidence.OUT / 'sources')
        import csv
        with (evidence.ROOT / 'data/dividend_events/e22_dividend_events.csv').open() as handle:
            ledger = list(csv.DictReader(handle))
        checks, _ = evidence.reconcile(ledger, facts)
        etf = [r for r in checks if r['code'] == '0050']
        self.assertEqual(len(etf), 27)
        self.assertTrue(all(r['primary_reported_time_supported'] for r in etf))
        self.assertTrue(all(not r['publication_vintage_certified'] for r in checks))

    def test_primary_split_contracts_match_and_mismatch_blocks(self):
        from dd_switch_session_market import SPLITS
        self.assertEqual(len(evidence.audit_splits()), 2)
        wrong = copy.deepcopy(SPLITS)
        wrong['2025-06-18']['0050'] = 5
        with patch('dd_switch_session_market.SPLITS', wrong):
            with self.assertRaisesRegex(ValueError, 'unit contract'):
                evidence.audit_splits()


if __name__ == '__main__':
    unittest.main()
