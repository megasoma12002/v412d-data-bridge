import unittest
import pandas as pd
from dd_switch_position_origin_audit import lifecycle,mix_gap,recorded_regime

class OriginAudit(unittest.TestCase):
    def test_cash_limited_fill_and_future_pending(self):
        orders=pd.DataFrame([dict(order_id='a',signal_date='2026-09-03',code='5880',side='BUY',quantity=3000),
            dict(order_id='b',signal_date='2026-09-04',code='0050',side='BUY',quantity=1000)])
        fills=pd.DataFrame([dict(fill_id='a',signal_date='2026-09-03',fill_date='2026-09-04',code='5880',side='BUY',quantity=2000,fill_price=10.,gross=20000.,fees_tax=20.)])
        report,cash=lifecycle(orders,fills,['2026-09-03','2026-09-04'],25000.,'2026-09-04')
        self.assertTrue(report.iloc[0].status.startswith('CASH_LIMITED'))
        self.assertEqual(report.iloc[1].status,'PENDING_AFTER_CUTOFF')
        self.assertEqual(cash,4980.)
    def test_same_mix_different_capital_not_a_gap(self):
        gap,value=mix_gap({'A':2000,'B':4000},{'A':1000,'B':2000},{'A':10,'B':20},['A','B'])
        self.assertEqual(gap,0.)
        self.assertEqual(value,100000.)
    def test_cutover_failure_distinct_from_no_flip(self):
        self.assertEqual(recorded_regime({'path3_t0_weight_reason':'no_flip'}),'FLIP_ONLY_NO_SWITCH')
        self.assertEqual(recorded_regime({'path3_strategy_cutover_applied':'True','path3_t0_weight_reason':'ledger_stale'}),'CUTOVER_STALE_LEDGER_NO_RECON')
