"""Synthetic fixtures validate mechanics only, never strategy performance."""
import unittest
import json
import tempfile
import hashlib
import subprocess
import sys
from pathlib import Path
import pandas as pd
from dd_switch_intraday_replay import timestamp as ts, decisions, replay, read_bundle
from dd_switch_capital_policy import POLICIES

def quote(at,code='0050',price=100,size=100000):
    return dict(timestamp=ts(at),available_at=ts(at),code=code,bid=price,ask=price,
                bid_size=size,ask_size=size)

def frames(quotes):
    return dict(quotes=pd.DataFrame(quotes),events=pd.DataFrame(columns=['effective_at','kind','code','factor']))

def plan(at='2026-10-01T10:00:00+08:00',weights=None):
    return dict(signal_at=ts(at),ready_at=ts(at),snapshot_id='s',parent='L4',weights={'0050':1.0} if weights is None else weights)

class ReplayTest(unittest.TestCase):
    def test_future_price_cannot_fill_past_signal(self):
        r=replay(frames([quote('2026-10-01T10:00:00+08:00'),quote('2026-10-01T10:00:02+08:00')]),[plan()],1_000_000)
        self.assertEqual(len(r['fills']),1)
        self.assertGreater(ts(r['fills'][0]['fill_at']),ts(r['fills'][0]['signal_at']))
        self.assertGreaterEqual(r['final_cash'],0)

    def test_depth_and_lots(self):
        r=replay(frames([quote('2026-10-01T10:00:02+08:00',size=15000)]),[plan()],1_000_000)
        self.assertEqual(r['fills'][0]['quantity'],1000)

    def test_optional_capital_reserve_has_one_cash_account(self):
        r=replay(frames([quote('2026-10-01T10:00:02+08:00')]),[plan()],1_000_000,
                 capital_policy=POLICIES[2])
        self.assertGreaterEqual(r['final_cash'],100000)
        self.assertEqual(r['events'][0]['scale'],.9)

    def test_reentry_uses_account_cash(self):
        q=[quote('2026-10-01T10:00:02+08:00'),quote('2026-10-01T11:00:02+08:00'),quote('2026-10-01T12:00:02+08:00')]
        plans=[plan(),plan('2026-10-01T11:00:00+08:00',{}),plan('2026-10-01T12:00:00+08:00')]
        r=replay(frames(q),plans,1_000_000)
        self.assertEqual([f['side'] for f in r['fills']],['BUY','SELL','BUY'])
        self.assertLess(r['final_cash']+r['final_positions']['0050']*100,1_000_000)

    def test_new_target_cancels_unfilled_old_target(self):
        r=replay(frames([quote('2026-10-01T11:00:02+08:00')]),[plan(),plan('2026-10-01T11:00:00+08:00',{})],1_000_000)
        self.assertEqual(r['fills'],[])

    def test_pending_expires_at_session_end(self):
        r=replay(frames([quote('2026-10-02T09:00:02+08:00')]),[plan()],1_000_000)
        self.assertEqual(r['fills'],[])

    def test_stale_quote_cannot_fill(self):
        q=quote('2026-10-01T10:00:00+08:00');q['available_at']=ts('2026-10-01T10:02:00+08:00')
        self.assertEqual(replay(frames([q]),[plan()],1_000_000)['fills'],[])

    def test_delayed_pre_signal_quote_cannot_fill(self):
        q=quote('2026-10-01T09:59:59+08:00');q['available_at']=ts('2026-10-01T10:00:02+08:00')
        self.assertEqual(replay(frames([q]),[plan()],1_000_000)['fills'],[])

    def test_same_arrival_batch_uses_latest_quote_only(self):
        q1=quote('2026-10-01T10:00:02+08:00',size=10000)
        q2=quote('2026-10-01T10:00:03+08:00',size=10000)
        q1['available_at']=q2['available_at']
        r=replay(frames([q1,q2]),[plan()],1_000_000)
        self.assertEqual(len(r['fills']),1)
        self.assertEqual(r['fills'][0]['quantity'],1000)

    def test_sell_before_buy_in_same_quote_batch(self):
        q=[quote('2026-10-01T10:00:02+08:00'),quote('2026-10-01T11:00:02+08:00'),quote('2026-10-01T11:00:02+08:00',code='00631L')]
        r=replay(frames(q),[plan(),plan('2026-10-01T11:00:00+08:00',{'00631L':1})],1_000_000)
        self.assertEqual([f['side'] for f in r['fills']],['BUY','SELL','BUY'])
        self.assertEqual(r['final_positions']['0050'],0)

    def test_t1_waits_for_next_session_quote(self):
        p=plan('2026-10-01T14:00:00+08:00');p['ready_at']=ts('2026-10-02T09:00:00+08:00')
        q=[quote('2026-10-01T14:01:02+08:00'),quote('2026-10-02T09:00:02+08:00')]
        r=replay(frames(q),[p],1_000_000)
        self.assertEqual(len(r['fills']),1)
        self.assertEqual(ts(r['fills'][0]['fill_at']).strftime('%F'),'2026-10-02')

    def test_split_preserves_equity(self):
        f=frames([quote('2026-10-01T10:00:02+08:00'),quote('2026-10-02T09:00:02+08:00',price=50)])
        f['events']=pd.DataFrame([dict(effective_at=ts('2026-10-02T08:00:00+08:00'),kind='split',code='0050',factor=2)])
        r=replay(f,[plan()],1_000_000)
        self.assertEqual(r['nav'][0]['nav'],r['nav'][1]['nav'])

    def test_prefix_fill_invariance(self):
        q=[quote('2026-10-01T10:00:02+08:00'),quote('2026-10-02T10:00:02+08:00',price=200)]
        short=replay(frames(q[:1]),[plan()],1_000_000)
        full=replay(frames(q),[plan()],1_000_000)
        self.assertEqual(short['fills'],full['fills'])

    def test_fixed_target_does_not_churn_with_quotes(self):
        q=[quote('2026-10-01T10:00:02+08:00'),quote('2026-10-01T10:01:02+08:00',price=120)]
        r=replay(frames(q),[plan()],1_000_000)
        self.assertEqual(len(r['fills']),1)

class DecisionTest(unittest.TestCase):
    def fixture(self):
        return dict(sessions=pd.DataFrame({'date':['2026-09-30','2026-10-01','2026-10-02']}),
                    daily_nav=pd.DataFrame([dict(date=d,available_at=ts(d+'T14:00:00+08:00'),l4_nav=100,trail_nav=100) for d in ['2026-09-30','2026-10-01','2026-10-02']]),
                    snapshots=pd.DataFrame([dict(snapshot_id='s'+d,observed_at=ts(d+'T10:00:00+08:00'),available_at=ts(d+'T10:00:00+08:00'),l4_nav=90,trail_nav=95) for d in ['2026-10-01','2026-10-02']]),
                    targets=pd.DataFrame([dict(snapshot_id='s'+d,parent=p,code='0050',weight=0.5,available_at=ts(d+'T09:59:00+08:00')) for d in ['2026-10-01','2026-10-02'] for p in ['L4','TRAIL42']]))

    def test_original_dd_comparison_and_no_future_eod(self):
        f=self.fixture();before=decisions(f,'10:00')
        self.assertEqual(before[0]['parent'],'TRAIL42')
        f['daily_nav'].loc[f['daily_nav'].date=='2026-10-02','trail_nav']=10000
        self.assertEqual(before,decisions(f,'10:00'))

    def test_future_target_rejected(self):
        f=self.fixture();f['targets']['available_at']=ts('2026-10-02T15:00:00+08:00')
        with self.assertRaisesRegex(ValueError,'future parent'):
            decisions(f,'10:00')

    def test_missing_daily_history_rejected(self):
        f=self.fixture();f['daily_nav']=f['daily_nav'].iloc[1:]
        with self.assertRaisesRegex(ValueError,'prior daily'):
            decisions(f,'10:00')

    def test_missing_active_day_snapshot_rejected(self):
        f=self.fixture();f['snapshots']=f['snapshots'].iloc[:1]
        with self.assertRaisesRegex(ValueError,'Missing contemporaneous'):
            decisions(f,'10:00')

    def test_timezone_required(self):
        with self.assertRaisesRegex(ValueError,'timezone'):
            ts('2026-10-01 10:00')

    def test_daily_proxy_bundle_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);(path/'manifest.json').write_text(json.dumps({'evidence_kind':'daily_proxy'}))
            with self.assertRaisesRegex(ValueError,'not research evidence'):
                read_bundle(path)

    def test_bundle_cli_all_ten_arms(self):
        # Temporary synthetic market observations exercise serialization and
        # CLI plumbing only; this result is never retained as research evidence.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);bundle=root/'bundle';bundle.mkdir()
            f=self.fixture();snapshots=[];targets=[];quotes=[]
            for day in ('2026-10-01','2026-10-02'):
                quotes.append(quote(day+'T09:00:02+08:00'))
                for clock in ('10:00','12:00','13:20','13:30'):
                    ident=day+clock
                    snapshots.append(dict(snapshot_id=ident,observed_at=ts(day+'T'+clock+':00+08:00'),
                                          available_at=ts(day+'T'+clock+':00+08:00'),l4_nav=90,trail_nav=95))
                    for parent in ('L4','TRAIL42'):
                        targets.append(dict(snapshot_id=ident,parent=parent,code='0050',weight=.5,
                                            available_at=ts(day+'T09:00:00+08:00')))
                    quotes.append(quote(day+'T'+clock+':02+08:00'))
            f.update(snapshots=pd.DataFrame(snapshots),targets=pd.DataFrame(targets),quotes=pd.DataFrame(quotes),
                     events=pd.DataFrame(columns=['effective_at','kind','code','factor']))
            hashes={}
            for name,frame in f.items():
                path=bundle/(name+'.csv');frame.to_csv(path,index=False)
                hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
            manifest=dict(evidence_kind='timestamped_market_observations',parent_scope='full_account',
                          sha256=hashes,provider='SYNTHETIC_UNITTEST_ONLY')
            (bundle/'manifest.json').write_text(json.dumps(manifest))
            script=Path(__file__).resolve().parents[1]/'scripts/dd_switch_intraday_replay.py'
            out=root/'out'
            process=subprocess.run([sys.executable,str(script),'--bundle',str(bundle),'--out',str(out),
                                    '--initial-cash','1000000'],capture_output=True,text=True)
            self.assertEqual(process.returncode,0,process.stderr)
            summary=json.loads((out/'summary.json').read_text())
            self.assertEqual(len(summary['arms']),10)
            self.assertEqual(summary['status'],'QUOTE_FILL_MODEL_ONLY')
            (bundle/'quotes.csv').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'checksum'):
                read_bundle(bundle)

if __name__=='__main__':unittest.main()
