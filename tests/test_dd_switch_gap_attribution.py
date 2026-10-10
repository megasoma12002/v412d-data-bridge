import unittest
import tempfile
from pathlib import Path
import pandas as pd
from dd_switch_gap_attribution import book_flows
from dd_switch_gap_pipeline import force_active_state
from dd_switch_runtime import DEFAULT_DIR,r1_research_destination

class GapAttributionTest(unittest.TestCase):
    def test_non_equivalent_r1_cannot_publish_to_canonical_runtime(self):
        for path in (DEFAULT_DIR,DEFAULT_DIR/'nested'):
            with self.assertRaisesRegex(RuntimeError,'parity failed'):
                r1_research_destination(path)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(r1_research_destination(Path(tmp)),Path(tmp).resolve())

    def test_exact_hold_trade_execution_fee_identity(self):
        nav=pd.DataFrame([dict(date='2026-10-01',nav=2080),dict(date='2026-10-02',nav=2115)])
        positions=pd.DataFrame([dict(date='2026-10-01',code='0050',quantity=10),dict(date='2026-10-02',code='0050',quantity=5)])
        fills=pd.DataFrame([dict(fill_date='2026-10-01',code='0050',side='BUY',quantity=10,fill_price=101,fees_tax=10),
                            dict(fill_date='2026-10-02',code='0050',side='SELL',quantity=5,fill_price=109,fees_tax=10)])
        panel=pd.DataFrame([dict(date='2026-10-01',code='0050',open=100,close=110),
                            dict(date='2026-10-02',code='0050',open=110,close=120)]).set_index(['date','code'])
        flow=book_flows(nav,positions,fills,panel,2000)
        self.assertEqual(flow.total.tolist(),[80,35])
        self.assertEqual(flow.holding_pnl.tolist(),[0,100])
        self.assertEqual(flow.execution_price_pnl.tolist(),[-10,-5])
        nav.loc[1,'nav']=2116
        with self.assertRaisesRegex(ValueError,'residual'):
            book_flows(nav,positions,fills,panel,2000)

    def test_exit_ablation_cannot_bypass_stale_gate(self):
        failed={'ok':False,'reason':'nav_stale','path3_active':None}
        self.assertEqual(force_active_state(failed),failed)
        natural={'ok':True,'path3_active':False,'fill':'FT_TO_CASH','clock':'exact_t1'}
        altered=force_active_state(natural)
        self.assertFalse(natural['path3_active'])
        self.assertTrue(altered['path3_active'])
        self.assertEqual(altered['clock'],'exact_t1')

if __name__=='__main__':unittest.main()
