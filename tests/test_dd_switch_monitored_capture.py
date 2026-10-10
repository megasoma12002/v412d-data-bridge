import unittest
from dd_switch_monitored_capture import blocked, advance

class MonitoredCaptureTests(unittest.TestCase):
    def state(self):return dict(processed=0,success=0,failed=0,consecutive_failures=0,attempted_ids=[],status='FETCHING')
    def test_http_200_overrun_stops_on_first_response(self):
        s=advance(self.state(),dict(id='x',status='UNAVAILABLE'),b'Overrun - Too many query requests')
        self.assertEqual(s['status'],'STOPPED_SOURCE_BLOCK');self.assertEqual(s['failed'],1)
    def test_three_failed_requests_stop_batch(self):
        s=self.state()
        for i in range(3):advance(s,dict(id=str(i),status='UNAVAILABLE'),b'')
        self.assertEqual(s['status'],'STOPPED_FAILURE_LIMIT')
    def test_success_resets_failure_streak_and_records_timestamp(self):
        s=self.state();advance(s,dict(id='a',status='UNAVAILABLE'),b'');advance(s,dict(id='b',status='CAPTURED'),b'valid')
        self.assertEqual(s['consecutive_failures'],0);self.assertEqual(s['success'],1);self.assertTrue(s['last_completed_at'])
    def test_normal_primary_body_is_not_blocked(self):
        self.assertFalse(blocked('公開資訊觀測站正常公告'.encode()))
    def test_success_does_not_report_stale_error_from_previous_attempt(self):
        s=advance(self.state(),dict(id='x',status='CAPTURED',error='Unrelated/security response'),b'valid')
        self.assertEqual(s['recent_results'][0]['error'],'')

if __name__=='__main__':unittest.main()
