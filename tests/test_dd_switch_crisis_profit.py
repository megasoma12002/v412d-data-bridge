import unittest
import pandas as pd
from dd_switch_funded_sleeve import FundingJournal
from dd_switch_crisis_policies import RiskOverlay
from dd_switch_crisis_profit_research import forward_labels,market_features
BAD=dict(dd63=-.09,ret20=-.04,ret5=-.04,above_ma20=False)
GOOD=dict(dd63=-.02,ret20=.02,ret5=.01,above_ma20=True)
class CrisisProfitTests(unittest.TestCase):
    def test_sales_refill_buy_once(self):
        f=FundingJournal(10.)
        f.fill(dict(fill_id='exit',gross=100.,fees_tax=1.,side='SELL'))
        f.fill(dict(fill_id='reentry',gross=90.,fees_tax=1.,side='BUY'))
        self.assertEqual(f.cash,18.)
        with self.assertRaises(ValueError):f.fill(dict(fill_id='exit',gross=100.,fees_tax=1.,side='SELL'))
        self.assertEqual(f.cash,18.)
    def test_overdraft_cannot_borrow_another_wallet_and_is_atomic(self):
        fin=FundingJournal(100.);tel=FundingJournal(1000.)
        with self.assertRaises(ValueError):fin.fill(dict(fill_id='buy',gross=101.,fees_tax=1.,side='BUY'))
        self.assertEqual(fin.cash,100.);self.assertEqual(tel.cash,1000.)
        self.assertNotIn('buy',fin.applied)
    def test_dividend_not_double_counted(self):
        f=FundingJournal(10.);f.credit_dividend('2026-01-02',5.)
        with self.assertRaises(ValueError):f.credit_dividend('2026-01-02',5.)
        self.assertEqual(f.cash,15.);self.assertEqual(f.reconcile(15.),0.)
    def test_confirm_half_needs_two_bad_three_good(self):
        c=RiskOverlay('MARKET_HALF_CONFIRM')
        self.assertEqual(c.observe(BAD,True)['scale'],1.)
        self.assertEqual(c.observe(BAD,True)['scale'],.5)
        self.assertEqual(c.observe(GOOD,True)['scale'],.5)
        self.assertEqual(c.observe(GOOD,True)['scale'],.5)
        self.assertEqual(c.observe(GOOD,True)['scale'],1.)
    def test_fast_recovery_one_day(self):
        c=RiskOverlay('MARKET_HALF_FAST');c.observe(BAD,True);c.observe(BAD,True)
        self.assertEqual(c.observe(GOOD,True)['scale'],1.)
    def test_existing_dd_overrides_half(self):
        c=RiskOverlay('DD_PLUS_HALF');self.assertEqual(c.observe(GOOD,False)['scale'],0.)
        self.assertEqual(c.observe(GOOD,True)['scale'],1.)
    def test_baseline_never_cut_by_dd(self):
        c=RiskOverlay('CORE_ON');c.observe(BAD,False);self.assertEqual(c.observe(BAD,False)['scale'],1.)
    def test_future_labels_exclude_incomplete_or_missing_horizon(self):
        s=pd.Series([100.,100.,80.,90.,100.,100.]);r=forward_labels(s,2)
        self.assertEqual(r.iloc[0],1.);self.assertTrue(pd.isna(r.iloc[-1]))
        s.iloc[1]=float('nan');self.assertTrue(pd.isna(forward_labels(s,2).iloc[0]))
    def test_future_price_cannot_change_previous_market_features(self):
        s=pd.Series([100.+i for i in range(100)])
        old=market_features(s.iloc[:80]);s.iloc[80:]=1.
        pd.testing.assert_frame_equal(old,market_features(s).iloc[:80])
if __name__=='__main__':unittest.main()
