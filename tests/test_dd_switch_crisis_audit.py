import unittest
import pandas as pd
from unittest.mock import patch
from dd_switch_crisis_audit import features,market_episodes,stale_pending_probe
from path3_comp_sat_daily_share_ssot import plan_delta_ledger_scaled
import live_tipsoft_dd_switch as gate
from live_fill_core import _paper_fill_rows
class CrisisAuditTests(unittest.TestCase):
    def test_features_prefix_causal(self):
        dates=pd.date_range('2026-01-01',periods=80)
        frames={k:pd.DataFrame({'date':dates,'nav':[100*(1+r)**i for i in range(80)]}) for k,r in [('base',.001),('l4',-.001),('trail',0)]}
        old=features({k:v.iloc[:45] for k,v in frames.items()});full=features(frames).iloc[:45]
        pd.testing.assert_frame_equal(old,full)
    def test_premium_excludes_current_day_return(self):
        dates=pd.date_range('2026-01-01',periods=20)
        frames={k:pd.DataFrame({'date':dates,'nav':[100.]*20}) for k in ['base','l4','trail']}
        frames['l4'].loc[19,'nav']=50.
        f=features(frames);self.assertEqual(f.iloc[-1].premium42_lag1,0.)
    def test_all_threshold_episodes_including_unrecovered(self):
        series=pd.Series([100.,85.,101.,80.],index=['a','b','c','d'])
        result=market_episodes(series);self.assertEqual(len(result),2)
        self.assertEqual(result[0]['recovery_date'],'c');self.assertIsNone(result[1]['recovery_date'])
    def test_on_with_cash_and_no_core_cannot_refill_current_planner(self):
        delta,meta=plan_delta_ledger_scaled(live_pos={'0050':1000},prices={'2880':45.,'0050':100.},ledger_shares={'2880':100000})
        self.assertEqual(delta,{})
        self.assertEqual(meta['fin_notional'],0.)
    def test_dd_exit_overrides_buy_and_keeps_etf(self):
        state={'2880':2000,'2412':1000,'0050':1000,'2884':1000}
        with patch.object(gate,'is_on',return_value=True),patch.object(gate,'compute_gate_state',return_value={'ok':True,'path3_active':False}):
            delta,meta=gate.apply_to_path3_deltas({'2892':1000},state,'2026-09-30')
        self.assertEqual(delta,{'2880':-2000.,'2412':-1000.})
    def test_no_same_day_flatten_fill(self):
        pending=pd.DataFrame([dict(order_id='exit',signal_date='2026-09-30',code='2880',side='SELL',quantity=1000)])
        _,_,fills=_paper_fill_rows(pending=pending,latest=pd.Timestamp('2026-09-30'),open_prices={'2880':45.},pos={'2880':1000},cash=0.,carve_authorized=False)
        self.assertEqual(fills,[])
    def test_stale_buy_cancelled_before_next_session(self):
        self.assertTrue(stale_pending_probe()['cancelled'])
if __name__=='__main__':unittest.main()
