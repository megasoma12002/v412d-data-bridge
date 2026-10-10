import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import dd_switch_full_history_audit as audit


class AnnualCacheIntegrityTests(unittest.TestCase):
    def fixture(self, root, raw):
        out = root / 'audit'
        (out / 'sources').mkdir(parents=True)
        path = out / 'sources/TAIEX_2023.json'
        (out / 'source_manifest.json').write_text(json.dumps([
            dict(status='FETCHED', path=str(path.relative_to(root)),
                 sha256=hashlib.sha256(raw).hexdigest())]))
        return out, path

    def test_missing_fetched_snapshot_does_not_shrink_benchmark(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out, _ = self.fixture(root, b'expected')
            with patch.object(audit, 'ROOT', root):
                with self.assertRaisesRegex(FileNotFoundError, 'Restore fetched'):
                    audit.archive_prices(out)

    def test_modified_snapshot_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out, path = self.fixture(root, b'expected')
            path.write_bytes(b'changed')
            with patch.object(audit, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    audit.archive_prices(out)

    def test_intact_snapshot_included(self):
        raw = json.dumps(dict(status=200, data=[dict(date='2023-01-03', stock_id='TAIEX',
            open=100, max=101, min=99, close=100, Trading_Volume=1)])).encode()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out, path = self.fixture(root, raw)
            path.write_bytes(raw)
            with patch.object(audit, 'ROOT', root):
                frame = audit.archive_prices(out)
            self.assertEqual(list(frame.date), ['2023-01-03'])


if __name__ == '__main__':
    unittest.main()
