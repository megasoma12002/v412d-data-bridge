#!/usr/bin/env python3
"""Frozen DD gate historical events + actual planner/fill lifecycle probes.

Historical shadow controls are audited, not certified full-history live wealth.
Exit probes use explicitly synthetic lot-sized parent-shaped holdings; no
counterfactual CAGR, dividends, or complete portfolio drawdown are claimed.
"""
import argparse,hashlib,json,tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import live_tipsoft_dd_switch as gate
from dd_switch_live_replay import verify_runtime_generation
from dd_switch_full_live_books import load_prices,reconstruct
from e22_dividend_accounting import load_dividend_events
from live_fill_core import _paper_fill_rows,_iter_pending
from live_order_lifecycle import prepare_order_events
from path3_comp_sat_daily_share_ssot import plan_delta_ledger_scaled,FIN,TEL,dollar_mix
from twse_session_sources import cached_load_calendar_window
ROOT=Path(__file__).resolve().parents[1]
CORE=FIN+TEL

def features(frames):
    def returns(key):return frames[key].set_index('date').nav.astype(float).pct_change().fillna(0.)
    pair=pd.concat({'l4':returns('l4'),'trail':returns('trail')},axis=1,join='inner').dropna()
    curve=(1+pair).cumprod();dd=curve/curve.cummax()-1
    prem=pd.concat({'p3':returns('l4'),'base':returns('base')},axis=1,join='inner').dropna()
    score=(prem.p3-prem.base).shift(1).rolling(42,min_periods=14).sum()
    out=pd.DataFrame({'l4_dd':dd.l4,'trail_dd':dd.trail,'premium42_lag1':score}).dropna(subset=['l4_dd','trail_dd'])
    out['want_trail']=out.trail_dd>=out.l4_dd;out['trail42_on']=out.premium42_lag1.fillna(0)>=-.01
    out['active']=~out.want_trail|out.trail42_on
    return out

def market_episodes(prices,threshold=.10):
    """All running-peak drawdown episodes reaching threshold; no date picking."""
    peak=float(prices.iloc[0]);peakday=prices.index[0];trough=peak;troughday=peakday;rows=[]
    for day,value in prices.items():
        value=float(value)
        if value>=peak:
            if trough/peak-1<=-threshold:
                rows.append(dict(peak_date=peakday,trough_date=troughday,recovery_date=day,market_drawdown_pct=(trough/peak-1)*100))
            peak=value;peakday=day;trough=value;troughday=day
        elif value<trough:trough=value;troughday=day
    if trough/peak-1<=-threshold:rows.append(dict(peak_date=peakday,trough_date=troughday,recovery_date=None,market_drawdown_pct=(trough/peak-1)*100))
    return rows

def lifecycle_probe(exit_day,reentry_day,exit_fill_day,px_exit,px_open,ledger_exit,ledger_on,px_on,book):
    # Parent-shaped synthetic account: 95% allocated to FIN/TEL, 5% reserve.
    allocation=dollar_mix(ledger_exit,px_exit,CORE)
    if not allocation:raise ValueError('Exit probe parent has no core holdings')
    pos={c:float(int(475000000*w/px_exit[c]//1000)*1000) for c,w in allocation.items()}
    pos={c:q for c,q in pos.items() if q};cash=500000000-sum(q*px_exit[c] for c,q in pos.items())
    state_before=dict(pos)
    fakegate={'ok':True,'asof':exit_day,'path3_active':False,'want_trail':True,'trail42_on':False,'fill':'FT_TO_CASH'}
    with patch.object(gate,'is_on',return_value=True),patch.object(gate,'compute_gate_state',return_value=fakegate):
        delta,meta=gate.apply_to_path3_deltas({'2892':1000.},pos,exit_day,market_tip=exit_day)
    assert delta==gate.flatten_fin_tel_deltas(pos)
    pending=pd.DataFrame([dict(order_id=exit_day+'-'+c+'-SELL-P3T0',signal_date=exit_day,code=c,side='SELL',quantity=-q) for c,q in delta.items()])
    after,cash_after,fills=_paper_fill_rows(pending=pending,latest=pd.Timestamp(exit_fill_day),open_prices=px_open,pos=dict(pos),cash=cash,carve_authorized=False)
    assert len(fills)==len(pending) and all(float(after.get(c,0))==0 for c in CORE)
    assert all(f['fill_date']>f['signal_date'] for f in fills)
    # Valid ON cannot refill a zero sleeve: actual production scaled planner.
    refill,plan=plan_delta_ledger_scaled(live_pos=after,prices=px_on,ledger_shares=ledger_on)
    ong={'ok':True,'asof':reentry_day,'path3_active':True,'want_trail':False,'trail42_on':True,'fill':'WITHIN'}
    with patch.object(gate,'is_on',return_value=True),patch.object(gate,'compute_gate_state',return_value=ong):
        actual,apply=gate.apply_to_path3_deltas(refill,after,reentry_day,market_tip=reentry_day)
    expected_mix=dollar_mix(ledger_on,px_on,CORE)
    # Demand probe only: restore saved sleeve notional, without inventing policy.
    saved_fin=sum(state_before.get(c,0)*px_exit[c] for c in FIN)
    saved_tel=sum(state_before.get(c,0)*px_exit[c] for c in TEL)
    return dict(exit_signal=exit_day,exit_fill=exit_fill_day,reentry_signal=reentry_day,book_on=book,
        initial_nav=500000000.,synthetic_positions=state_before,exit_orders=len(pending),exit_fills=len(fills),
        overnight_exit_pnl=sum(q*(px_open[c]-px_exit[c]) for c,q in state_before.items()),
        exit_slippage=sum(f['quantity']*px_open[f['code']]*.0005 for f in fills),exit_fees=sum(f['fees_tax'] for f in fills),
        cash_after_exit=cash_after,fin_remaining=sum(after.get(c,0) for c in FIN),tel_remaining=sum(after.get(c,0) for c in TEL),
        on_parent_core_notional=sum(ledger_on.get(c,0)*px_on[c] for c in CORE),
        on_parent_has_core=bool(expected_mix),on_new_buy_orders=sum(q>0 for q in actual.values()),
        on_fin_planner_budget=plan['fin_notional'],on_tel_planner_budget=plan['tel_notional'],
        saved_fin_notional=saved_fin,saved_tel_notional=saved_tel,
        reentry_blocked_by_zero_sleeve=bool(expected_mix) and not any(q>0 for q in actual.values()))

def stale_pending_probe():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        old=dict(order_id='unfunded-before-off',signal_date='2026-09-29',code='2892',side='BUY',quantity=1000)
        pd.DataFrame([old]).to_csv(root/'orders.csv',index=False)
        pd.DataFrame(columns=['fill_id','quantity']).to_csv(root/'fills.csv',index=False)
        events=prepare_order_events(root,'2026-09-30',[],[],True)
        pd.DataFrame(events).to_csv(root/'order_events.csv',index=False)
        pending=_iter_pending(root,pd.Timestamp('2026-10-01'),carve_authorized=False)
        assert pending.empty
        return dict(cancelled=True,status=events[0]['status'],following_session_pending=0)

def full_pipeline_probe(source,panel,calendar,out):
    events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    nav,positions,_,_,_,_,report=reconstruct(source,panel,calendar,events)
    orders=pd.read_csv(source/'orders.csv',dtype={'code':str});fills=pd.read_csv(source/'fills.csv',dtype={'code':str})
    signals=pd.read_csv(source/'signals.csv');post=signals[signals.date>'2026-09-29']
    assert post[post.date<'2026-10-02'].tipsoft_dd_path3_active.eq(0).all()
    assert post[post.date>='2026-10-02'].tipsoft_dd_path3_active.eq(1).all()
    corebuys=orders[(orders.signal_date>='2026-10-02')&orders.code.isin(CORE)&orders.side.eq('BUY')]
    assert corebuys.empty
    trace=[]
    for day in post.date:
        rows=positions[positions.date==day];prices=panel.loc[day,'close'].to_dict()
        exposure=lambda mask:sum(r.quantity*prices[r.code] for r in rows[mask].itertuples())
        trace.append(dict(date=day,active=bool(post.loc[post.date==day,'tipsoft_dd_path3_active'].iloc[0]),
            fin_tel_notional=exposure(rows.code.isin(CORE)),etf_notional=exposure(rows.code=='0050'),
            other_equity_notional=exposure(~rows.code.isin(CORE+['0050','00631L'])),
            cash=float(nav.loc[nav.date==day,'cash'].iloc[0])))
    assert all(r['fin_tel_notional']==0 for r in trace if r['date']>='2026-10-01')
    offdays=post.loc[post.tipsoft_dd_path3_active.eq(0),'date']
    outside=orders[orders.signal_date.isin(offdays)&~orders.code.isin(CORE)&orders.side.eq('BUY')]
    pd.DataFrame(trace).to_csv(out/'synthetic_pipeline_exposure_trace.csv',index=False)
    outside.to_csv(out/'outside_core_buy_intents_while_off.csv',index=False)
    for name in ['orders.csv','fills.csv','signals.csv','nav.csv','portfolio_state.json','order_events.csv','order_lifecycle.csv','qc_status.json','pipeline_t1_audit.json']:
        import shutil
        target=out/'pipeline-probe';target.mkdir(exist_ok=True);shutil.copyfile(source/name,target/name)
    return dict(kind='SYNTHETIC_OFF_ON_FAULT_INJECTION_NOT_STRATEGY_PERFORMANCE',off_dates=list(offdays),
        on_dates=post.loc[post.tipsoft_dd_path3_active.eq(1),'date'].tolist(),
        core_exit_fills=int((fills.fill_date.eq('2026-10-01')&fills.code.isin(CORE)&fills.side.eq('SELL')).sum()),
        on_core_buy_orders=len(corebuys),outside_core_buy_intents_while_off=len(outside),
        outside_core_codes=sorted(outside.code.unique().tolist()),qc=json.loads((source/'qc_status.json').read_text())['status'],
        max_nav_residual=report['max_nav_residual'],final_position_residual=report['final_position_residual'])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--runtime',type=Path,default=ROOT/'repro/dd-switch-live-repair-runtime-certified');p.add_argument('--pipeline-probe',type=Path,default=ROOT/'repro/dd-switch-crisis-pipeline-probe');a=p.parse_args()
    a.out=a.out.resolve()
    if (ROOT/'repro').resolve() not in a.out.parents:raise SystemExit('Research output only')
    a.out.mkdir(parents=True,exist_ok=False)
    meta=json.loads((a.runtime/'current.json').read_text());generation=verify_runtime_generation(a.runtime,meta)
    frames={k:pd.read_csv(generation/meta['files'][k],parse_dates=['date']) for k in ['base','l4','trail']}
    f=features(frames);w=gate.want_trail_series(l4_nav_path=generation/meta['files']['l4'],trail_nav_path=generation/meta['files']['trail']);t=gate.trail42_on_series(l3_nav_path=generation/meta['files']['base'],p3_nav_path=generation/meta['files']['l4']);active=gate.path3_active_series(w,t)
    pd.testing.assert_series_equal(f.active,active.reindex(f.index),check_names=False)
    exits=f.index[(~f.active)&f.active.shift(1,fill_value=True)]
    ons=f.index[f.active&~f.active.shift(1,fill_value=True)]
    panel,calendar=load_prices();calendar=[d for d in calendar if str(f.index.min().date())<=d<=str(f.index.max().date())]
    next_day=dict(zip(calendar[:-1],calendar[1:]));signals=pd.read_csv(generation/meta['files']['signal']).set_index('date')
    ledgers={book:pd.read_csv(generation/meta['files']['shares_'+book],dtype={'code':str}).set_index('date') for book in ['COMP_H150_x_A20','SAT_A20_RELAX']}
    probes=[];prefix=[];official=[]
    for stamp in exits:
        later=ons[ons>stamp]
        if len(later)==0:continue
        on=later[0];day=str(stamp.date());on_day=str(on.date());fill=next_day[day];onfill=next_day[on_day]
        for dt in [day,on_day]:
            sliced={key:frame[frame.date<=pd.Timestamp(dt)] for key,frame in frames.items()}
            point=features(sliced).loc[pd.Timestamp(dt)]
            for key in ['active','want_trail','trail42_on','premium42_lag1']:
                full=f.loc[pd.Timestamp(dt),key]
                assert (pd.isna(point[key]) and pd.isna(full)) or point[key]==full
            prefix.append(dict(date=dt,passed=True))
        for dt,expected in [(day,fill),(on_day,onfill)]:
            try:
                sessions,_=cached_load_calendar_window(int(dt[:4]));after=[str(x) for x in sessions if str(x)>dt]
            except FileNotFoundError:
                official.append(dict(signal=dt,next_session=expected,official=False,reason='Historical official calendar unavailable; next observed market date only'))
            else:
                assert after[0]==expected
                official.append(dict(signal=dt,next_session=expected,official=True))
        def ledger_for(dt):
            book=signals.loc[dt,'book'];rows=ledgers[book].loc[dt]
            if isinstance(rows,pd.Series):rows=rows.to_frame().T
            return book,dict(zip(rows.code,rows.shares))
        exitbook,le=ledger_for(day);onbook,lo=ledger_for(on_day)
        probes.append(lifecycle_probe(day,on_day,fill,panel.loc[day,'close'].to_dict(),panel.loc[fill,'open'].to_dict(),le,lo,panel.loc[on_day,'close'].to_dict(),onbook))
    pd.DataFrame(probes).to_json(a.out/'exit_reentry_probes.jsonl',orient='records',lines=True)
    pd.DataFrame([{k:v for k,v in row.items() if k!='synthetic_positions'} for row in probes]).to_csv(a.out/'exit_reentry_events.csv',index=False)
    f.rename_axis('date').to_csv(a.out/'historical_gate_features.csv')
    index=panel.xs('TAIEX',level='code').close.reindex(calendar).dropna()
    episodes=market_episodes(index);rows=[]
    for ep in episodes:
        start=ep['peak_date'];trough=ep['trough_date'];end=ep['recovery_date'] or index.index[-1]
        window=f[(f.index>=pd.Timestamp(start))&(f.index<=pd.Timestamp(end))]
        falling=window[window.index<=pd.Timestamp(trough)]
        exitdates=[str(x.date()) for x in exits if pd.Timestamp(start)<=x<=pd.Timestamp(trough)]
        rows.append(dict(**ep,falling_sessions=len(falling),off_sessions_before_trough=int((~falling.active).sum()),
            off_fraction_before_trough=float((~falling.active).mean()),exit_signals_before_trough=len(exitdates),first_exit=exitdates[0] if exitdates else None,
            market_loss_at_first_exit_pct=None if not exitdates else (float(index.loc[exitdates[0]])/float(index.loc[start])-1)*100))
    pd.DataFrame(rows).to_csv(a.out/'market_drawdown_episodes.csv',index=False)
    source_hashes={str((generation/name).relative_to(ROOT)):hashlib.sha256((generation/name).read_bytes()).hexdigest() for name in meta['files'].values()}
    booksummary=json.loads((ROOT/'repro/dd-switch-live-repair-books/summary.json').read_text())
    assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in booksummary['source_sha256'].items() if n.startswith('forward/e21/'))
    pipeline_probe=full_pipeline_probe(a.pipeline_probe,panel,calendar,a.out)
    result=dict(status='FROZEN_CRISIS_GATE_AUDIT_REENTRY_FUNDING_GAP_CONFIRMED',start=str(f.index.min().date()),end=str(f.index.max().date()),
        gate_sessions=len(f),off_sessions=int((~f.active).sum()),exit_events=len(exits),reentry_events=len(ons),completed_probes=len(probes),
        parent_positive_but_zero_reentry=sum(p['reentry_blocked_by_zero_sleeve'] for p in probes),
        prefix_checks=prefix,official_next_sessions=official,stale_pending_probe=stale_pending_probe(),market_episodes=rows,full_pipeline_probe=pipeline_probe,
        source_sha256=source_hashes,canonical_history_unchanged=True,
        pipeline_probe_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.pipeline_probe).iterdir() if p.is_file() and p.suffix in ['.csv','.json']},
        program_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'scripts/dd_switch_crisis_pipeline_probe.py',ROOT/'scripts/dd_switch_live_replay.py',ROOT/'scripts/live_tipsoft_dd_switch.py',ROOT/'scripts/path3_comp_sat_daily_share_ssot.py',ROOT/'scripts/live_fill_core.py',ROOT/'scripts/live_order_lifecycle.py']},
        limits=['Frozen original research shadows retain historical stitches and corporate-action assumptions; not new full-history exact live backtest',
        'TAIEX drawdown is a market comparator, not DD portfolio loss; 10% threshold used only to identify all episodes',
        'Lifecycle probes use synthetic 500m lot-sized parent-shaped FIN/TEL holdings; not archived broker positions',
        'Only next-open exit execution and reentry demand are probed; no long holding PnL, dividend or reentry performance claim',
        'Missing historical official calendars are flagged; historical next-open clocks are next observed market session, not formally certified',
        'No refilling cash without an approved funding contract; no production logic or risk thresholds changed',
        '5bp paper slippage and fees; no real auction capacity proof; no merge or deployment'])
    (a.out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ['status','gate_sessions','off_sessions','exit_events','parent_positive_but_zero_reentry']},indent=2));print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':main()
