import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import dd_switch_targeted_capture as capture
from dd_switch_targeted_capture import source_blocked

class TargetedGuardTests(unittest.TestCase):
    def test_webpack_library_overrun_is_not_source_block(self):
        self.assertFalse(source_blocked(b'(window.webpackJsonp=window.webpackJsonp||[]).push(["DecoderBuffer overrun"]);','https://example.org/_nuxt/app.js'))
    def test_html_security_page_at_js_url_still_blocks(self):
        self.assertTrue(source_blocked(b'<html><h1>FOR SECURITY</h1></html>','https://example.org/_nuxt/app.js'))
    def test_plain_overrun_at_js_url_still_blocks(self):
        self.assertTrue(source_blocked(b'Overrun - Too many query requests','https://example.org/_nuxt/app.js'))
    def test_announcement_overrun_still_blocks(self):
        self.assertTrue(source_blocked(b'Overrun - Too many query requests','https://example.org/announcement'))

    def test_forbidden_response_is_a_source_block(self):
        self.assertTrue(source_blocked(b'<html><title>403 Forbidden</title></html>', 'https://example.org/archive', b'403'))
        self.assertFalse(source_blocked(b'<html><title>404 Not Found</title></html>', 'https://example.org/archive', b'404'))

    def test_forbidden_response_stops_same_host(self):
        result, calls = self.run_capture(SimpleNamespace(returncode=0, stdout=b'<html><title>403 Forbidden</title></html>\n403', stderr=b''), 2)
        self.assertEqual(result['status'], 'STOPPED_SOURCE_BLOCK')
        self.assertEqual((result['processed'], result['skipped'], calls), (1, 1, 1))

    def run_capture(self, response, count):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue = root / 'queue.json'
            queue.write_text(json.dumps([dict(id='notice_' + str(i), url='https://example.org/notice/' + str(i)) for i in range(count)]))
            with patch.object(capture, 'ROOT', root), patch.object(capture, 'OUT', root), patch.object(capture, 'DEST', root / 'sources'), patch('sys.argv', ['capture', str(queue)]), patch.object(capture.time, 'sleep'), patch.object(capture.subprocess, 'run', return_value=response) as request, patch('builtins.print'):
                capture.main()
            return json.loads((root / 'issuer_capture_progress.json').read_text()), request.call_count

    def test_source_block_stops_same_host_and_records_skipped_work(self):
        result, calls = self.run_capture(SimpleNamespace(returncode=0, stdout=b'<html>FOR SECURITY</html>\n200', stderr=b''), 2)
        self.assertEqual(result['status'], 'STOPPED_SOURCE_BLOCK')
        self.assertEqual((result['processed'], result['skipped'], calls), (1, 1, 1))
        self.assertEqual(result['current_id'], '')

    def test_three_failed_transfers_stop_before_fourth_request(self):
        result, calls = self.run_capture(SimpleNamespace(returncode=28, stdout=b'partial body\n200', stderr=b'timed out'), 4)
        self.assertEqual(result['status'], 'STOPPED_FAILURE_LIMIT')
        self.assertEqual((result['processed'], result['skipped'], calls), (3, 1, 3))
        self.assertEqual(result['current_id'], '')


class CaptureWriterLockTests(unittest.TestCase):
    def test_overlapping_writer_rejected(self):
        import tempfile
        from pathlib import Path
        from dd_switch_targeted_capture import exclusive_capture_lock
        with tempfile.TemporaryDirectory() as name:
            with exclusive_capture_lock(Path(name)):
                with self.assertRaises(BlockingIOError):
                    with exclusive_capture_lock(Path(name)): pass
            with exclusive_capture_lock(Path(name)): pass

if __name__=='__main__':unittest.main()
