import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import e50_early_stack_combined_nav as core
from dd_switch_session_market import constant_factor,attach_off,SPLITS,HALTS
from cool_t50_lev_short_assist_stagea import _0050_rets
from e16_soft_frozen_base import FIN,TEL

class SessionContractTests(unittest.TestCase):
 def fixture(self):
  dates=pd.bdate_range('2025-06-02','2025-06-30');rows=[]
  for d in dates:
   for c in FIN+TEL+['0050']:
    halted=c=='0050' and d in HALTS['0050'];px=100. if c!='0050' or d<pd.Timestamp('2025-06-18') else 25.
    rows.append(dict(date=d,code=c,open=np.nan if halted else px,high=px,low=px,close=px,adj_close=100.,volume=0 if halted else 1000,tradable=not halted,unit_multiplier=4. if c=='0050' and d>=pd.Timestamp('2025-06-18') else 1.))
  m=pd.DataFrame(rows);t=pd.DataFrame({'Financial':0.,'Telecom':0.,'0050':1.},index=dates);return dates,m,t
 def run_model(self,m,t,**kwargs):
  with patch.object(core,'WARMUP_DAYS',0):return core.simulate_core(m,t,pd.Series('Bull',index=t.index),None,apply_e22=False,capital=1000000.,cost_multiple=0.,share_events=SPLITS,**kwargs)
 def test_halt_no_fills_null_opens_and_split_wealth_continuity(self):
  dates,m,t=self.fixture();sink=[];nav,fills,_=self.run_model(m,t,daily_pos_sink=sink)
  self.assertFalse(pd.to_datetime(fills.fill_date).isin(HALTS['0050']).any())
  values=nav.set_index('date').nav
  self.assertAlmostEqual(values['2025-06-17'],values['2025-06-18'])
  shares=pd.DataFrame(sink).query("code=='0050'").set_index('date').shares
  self.assertEqual(shares['2025-06-18'],4*shares['2025-06-17'])
 def test_suspended_intent_replaces_prior_intent_and_scales_on_resume(self):
  dates,m,t=self.fixture();t.loc[:'2025-06-10','0050']=0.;nav,fills,_=self.run_model(m,t)
  resume=fills[(fills.code.eq('0050'))&fills.fill_date.eq('2025-06-18')]
  self.assertEqual(len(resume),1)
  self.assertEqual(resume.iloc[0].signal_date,'2025-06-17');self.assertEqual(resume.iloc[0].quantity,8000)  # 2,000 old units × four; E18 caps this rebalance.
  self.assertGreaterEqual(nav.cash.min(),0)
 def test_tradable_missing_open_rejected(self):
  dates,m,t=self.fixture();m.loc[(m.date.eq(dates[1]))&m.code.eq('0050'),'open']=np.nan
  with self.assertRaises(ValueError):self.run_model(m,t)
 def test_split_neutral_signal(self):
  dates,m,t=self.fixture();ret1,ret3=_0050_rets(m,dates)
  self.assertEqual(ret1.loc['2025-06-18'],0);self.assertEqual(ret3.loc['2025-06-18'],0)
 def test_shadow_returns_do_not_treat_split_as_loss(self):
  import tipsoft_ip3_fill_lock_stagea as fl
  dates=pd.bdate_range('2025-01-01',periods=140);day=dates[70]
  px=pd.DataFrame(100.,index=dates,columns=fl.SOFT_CORE);px.loc[day:,'0050']=25.
  weights=pd.DataFrame(0.,index=dates,columns=fl.SOFT_CORE);weights['0050']=1.
  signal=pd.DataFrame(dict(date=dates,book=fl.BOOK_COMP))
  nav,_=fl.simulate_fill(fill='ALWAYS_WITHIN',weights_by_book={fl.BOOK_COMP:weights,fl.BOOK_SAT:weights},px=px,signal=signal,i3_on=pd.Series(1.,index=dates),share_events={str(day.date()):{'0050':4}})
  self.assertAlmostEqual(nav.nav.iloc[-1],1.)
 def test_adjustment_factor_ambiguity_blocks_inference(self):
  frame=pd.DataFrame(dict(date=pd.to_datetime(['2025-02-05','2025-02-07']),code=['2880','2880'],close=[10.,10.],adj_close=[9.,8.]))
  with self.assertRaises(ValueError):constant_factor(frame,'2880',pd.Timestamp('2025-02-06'))
 def test_missing_post_list_off_quote_is_not_forward_filled(self):
  eq=pd.DataFrame(dict(date=pd.to_datetime(['2025-02-06','2025-02-07']),code=['0050','0050'],close=[100.,100.]))
  raw=pd.DataFrame(dict(date=pd.to_datetime(['2025-02-06']),code=['00631L'],open=[10.],high=[10.],low=[10.],close=[10.],adj_close=[10.],volume=[100]))
  with self.assertRaises(ValueError):attach_off(eq,raw)
if __name__=='__main__':unittest.main()
