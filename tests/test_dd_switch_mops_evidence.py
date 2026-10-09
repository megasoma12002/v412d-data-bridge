import csv
import gzip
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import dd_switch_mops_evidence as evidence
import dd_switch_announcement_evidence as announcements


class MopsEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        with zipfile.ZipFile(evidence.OUT / 'mops_evidence_sources.zip') as archive:
            archive.extractall(cls.root)
        cls.out = cls.root / 'repro/dd-switch-full-history-audit'
        with evidence.LEDGER.open() as handle:
            cls.ledger = list(csv.DictReader(handle))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def reports(self):
        with patch.object(evidence, 'ROOT', self.root), patch.object(evidence, 'SOURCES', self.out / 'sources/mops_annual'):
            return evidence.load_reports()

    def test_archived_sources_authenticate_and_header_drift_parses(self):
        rows = self.reports()
        self.assertTrue(any(r['reported_at'].startswith('2010') for r in rows))
        self.assertTrue(any(r['reported_at'].startswith('2025') for r in rows))
        for folder in ('mops_annual', 'mops_actions'):
            for entry in json.loads((self.out / 'sources' / folder / 'manifest.json').read_text()):
                packed = (self.root / entry['path']).read_bytes()
                self.assertEqual(hashlib.sha256(packed).hexdigest(), entry['compressed_sha256'])
                self.assertEqual(hashlib.sha256(gzip.decompress(packed)).hexdigest(), entry['response_sha256'])

    def test_security_error_and_wrong_year_fail_closed(self):
        with self.assertRaises(ValueError):
            evidence.parse_report(b'<html>FOR SECURITY</html>', {'year': 2010})
        entry = json.loads((self.out / 'sources/mops_annual/manifest.json').read_text())[0]
        with self.assertRaisesRegex(ValueError, 'year differs'):
            evidence.parse_report(gzip.decompress((self.root / entry['path']).read_bytes()), dict(entry, year=2025))

    def test_389_fields_and_clock_conflict_remain_explicit(self):
        checks = evidence.reconcile(self.ledger, self.reports())
        self.assertEqual(len(checks), 389)
        failed = [r for r in checks if not r['primary_reported_time_supported']]
        self.assertEqual([(r['code'], r['ex_date'], r['mismatch_fields']) for r in failed], [('3045', '2025-07-09', 'REPORTED_CLOCK')])
        self.assertTrue(all(not r['publication_vintage_certified'] for r in checks))

    def test_24_paid_rights_classify_without_free_share_or_settlement(self):
        actions = evidence.reconcile_actions(self.ledger, self.reports())
        with patch.object(evidence, 'ROOT', self.root), patch.object(evidence, 'OUT', self.out):
            actions = evidence.action_class_evidence(actions)
        self.assertEqual(len(actions), 24)
        self.assertEqual(sum(r['issued_security_class'] == 'ORDINARY' for r in actions), 18)
        self.assertEqual(sum(r['issued_security_class'].startswith('PREFERRED_') for r in actions), 6)
        for r in actions:
            self.assertTrue(r['primary_verified'])
            self.assertFalse(r['free_stock_dividend'])
            self.assertFalse(r['settlement_certified'])
            self.assertEqual(evidence.number(r['shares_per_1000']), evidence.number(r['share_ratio']) * 1000)

    def test_stock_leg_and_close_cutoff_survive_issuer_declaration(self):
        row = dict(code='2884', leg='stock', event_id='2884:stock:test', stage='ISSUER_DECLARATION', reported_at='2025-06-01T16:00:00+08:00', amount=.5, ex_date='2025-07-01')
        self.assertEqual(announcements.research_snapshot([row], '2025-06-01T13:30:00+08:00'), [])
        result = announcements.research_snapshot([row], '2025-06-01T16:00:00+08:00')[0]
        self.assertEqual(result['leg'], 'stock')
        self.assertEqual(result['amount'], .5)
        self.assertFalse(result['publication_vintage_certified'])


if __name__ == '__main__':
    unittest.main()
