import sys,unittest,tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from live_dd_funding import DDFunding,FundingPaperPort,reject_unfunded_legacy_exit
from live_ledger import assert_no_uncommitted_ledger

class FundingTests(unittest.TestCase):
 def order(self,code,side,q,oid):
  return dict(order_id=oid,signal_date='2026-10-01',code=code,side=side,quantity=q,execution_clock='NEXT_SESSION_OPEN')
 def fill(self,f,orders,pos,cash,prices):
  with tempfile.TemporaryDirectory() as td:
   pd.DataFrame(orders).to_csv(Path(td)/'orders.csv',index=False)
   return FundingPaperPort(f).fill_pending(state_dir=Path(td),latest=pd.Timestamp('2026-10-02'),open_prices=prices,pos=pos,cash=cash)
 def test_actual_sale_reserved_and_private_cannot_spend(self):
  f=DDFunding(); sell=self.order('2880','SELL',1000,'exit-P3T0'); f.register([sell],dict(ok=True,path3_active=False))
  private=self.order('2881','BUY',1000,'private')
  pos,cash,fills,_,ok=self.fill(f,[sell,private],{'2880':1000},0,{'2880':100,'2881':50})
  self.assertTrue(ok);self.assertEqual(len(fills),1);self.assertEqual(f.total,cash);self.assertEqual(pos['2880'],0)
 def test_reentry_only_uses_own_sleeve(self):
  f=DDFunding();f.state['owned']=['FIN','TEL'];f.post('seed','2026-10-01','FIN',100000,'SELL');f.post('tel','2026-10-01','TEL',200000,'SELL')
  buy=self.order('2880','BUY',1000,'entry-P3T0'); f.register([buy],dict(ok=True,path3_active=True))
  _,cash,fills,_,_=self.fill(f,[buy],{},300000,{'2880':101})
  self.assertEqual(fills,[]);self.assertEqual(cash,300000)
 def test_affordable_reentry_spends_reserve_once(self):
  f=DDFunding();f.state['owned']=['FIN'];f.post('sale','2026-10-01','FIN',100000,'SELL')
  buy=self.order('2880','BUY',1000,'entry-P3T0');f.register([buy],dict(ok=True,path3_active=True))
  _,cash,fills,_,_=self.fill(f,[buy],{},100000,{'2880':90})
  self.assertEqual(len(fills),1);self.assertAlmostEqual(f.total,cash)
  before=f.total
  with self.assertRaises(RuntimeError):f.post('FILL:entry-P3T0','2026-10-02','FIN',-1,'BUY')
  self.assertEqual(f.total,before)
 def test_funded_plan_restores_flat_sleeve(self):
  f=DDFunding();f.state['owned']=['FIN'];f.post('sale','d','FIN',1000000,'SELL')
  delta,meta=f.funded_plan({},dict(fin_mix={'2880':1.}),{}, {'2880':100,'2886':100,'2892':100,'5880':100})
  self.assertEqual(delta['2880'],9000)
 def test_paid_dividends_only_and_snapshot_isolation(self):
  f=DDFunding();f.state['owned']=['FIN'];saved=f.state;g=DDFunding(saved)
  g.dividends([dict(key='ex',date='d',code='2880',cash_credit=0,receivable_credit=100),dict(key='pay',date='d',code='2880',cash_credit=100)])
  self.assertEqual(g.total,100);self.assertEqual(f.total,0)
 def test_overdraft_and_global_claim_fail_closed(self):
  f=DDFunding()
  with self.assertRaises(RuntimeError):f.post('bad','d','FIN',-1,'BUY')
  f.post('cash','d','FIN',100,'SELL')
  with self.assertRaises(RuntimeError):f.check(99)
 def test_signal_does_not_create_cash_or_reset_repeat_exit(self):
  f=DDFunding();order=self.order('2880','SELL',1000,'exit-P3T0')
  f.register([order],dict(ok=True,path3_active=False));self.assertEqual(f.total,0)
  f.post('sale','d','FIN',50000,'SELL');f.register([order],dict(ok=True,path3_active=False));self.assertEqual(f.total,50000)
 def test_funded_odd_lots_are_retained(self):
  f=DDFunding();f.state['owned']=['FIN'];f.post('sale','d','FIN',1000000,'SELL')
  delta,_=f.funded_plan({},dict(fin_mix={'2880':1.}),{'2880':123}, {'2880':100,'2886':100,'2892':100,'5880':100})
  self.assertEqual(delta['2880']%1000,0)
  self.assertEqual((123+delta['2880'])%1000,123)
 def test_legacy_off_requires_actual_fill_reconstruction(self):
  with tempfile.TemporaryDirectory() as td:
   pd.DataFrame([dict(tipsoft_dd_path3_active=False)]).to_csv(Path(td)/'signals.csv',index=False)
   with self.assertRaises(RuntimeError):reject_unfunded_legacy_exit(Path(td),None)
   reject_unfunded_legacy_exit(Path(td),DDFunding().state)
 def test_orphan_event_blocks_retry(self):
  with tempfile.TemporaryDirectory() as td:
   pd.DataFrame([dict(event_id='fill',date='2026-10-02')]).to_csv(Path(td)/'dd_funding_events.csv',index=False)
   with self.assertRaises(SystemExit):assert_no_uncommitted_ledger(td,'2026-10-01')
if __name__=='__main__':unittest.main()
