import hashlib
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from dd_switch_live_replay import verify_runtime_generation
from dd_switch_original_live_audit import clock_audit

class OriginalLiveReplayTest(unittest.TestCase):
    def test_source_hash_checked_before_day_cut_can_launder_corruption(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);g=root/'generations/test';g.mkdir(parents=True)
            source=g/'signal.csv';source.write_text('date\n2026-10-01\n')
            meta={'generation':'generations/test','files':{'signal':'signal.csv'},
                  'hashes':{'signal':hashlib.sha256(source.read_bytes()).hexdigest()}}
            self.assertEqual(verify_runtime_generation(root,meta),g)
            source.write_text('date\n2026-10-02\n')
            with self.assertRaisesRegex(RuntimeError,'checksum mismatch'):
                verify_runtime_generation(root,meta)
            meta['generation']='../outside'
            with self.assertRaisesRegex(RuntimeError,'outside source'):
                verify_runtime_generation(root,meta)

    def test_next_session_clock_respects_weekend_and_refuses_same_day(self):
        fills=pd.DataFrame({'signal_date':['2026-10-02'],'fill_date':['2026-10-05'],'quantity':[1000.]})
        orders=pd.DataFrame({'signal_date':['2026-10-02'],'carve_out_id':['T0_CARVE_FIN_SAT_SWITCH'],
                             'execution_clock':['NEXT_SESSION_OPEN']})
        calendar=['2026-10-01','2026-10-02','2026-10-05']
        self.assertEqual(clock_audit(fills,orders,calendar,'2026-09-29')['next_session_fills'],1)
        fills.loc[0,'fill_date']='2026-10-02'
        with self.assertRaisesRegex(ValueError,'Non-T'):
            clock_audit(fills,orders,calendar,'2026-09-29')
        fills.loc[0,'fill_date']='2026-10-05';orders.loc[0,'execution_clock']='SAME_BAR'
        with self.assertRaisesRegex(ValueError,'qualification'):
            clock_audit(fills,orders,calendar,'2026-09-29')
if __name__=='__main__':unittest.main()
