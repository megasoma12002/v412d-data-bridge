#!/usr/bin/env python3
"""Isolated original-lineage reconstruction. Never reads R1 runtime or writes live.

Preserves legacy simulation/stitch semantics intentionally for prefix parity.
Passing parity is not a causal-execution or jointly-funded portfolio validation.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import fin_sat_path3_path4_livestack_twin_stageb as ls
import tipsoft_ip3_fill_lock_stagea as fl
import live_tipsoft_dd_switch as live_gate
from path3_comp_sat_daily_share_ssot import shares_panel_from_long
from live_path3_t0_switch_emitter import build_sat_lead_signal
from e45_paper_harness import load_market, load_dividends
from dd_switch_original_inputs import append_market,append_dividends

ROOT=Path(__file__).resolve().parents[1]
CUTOFF=pd.Timestamp('2026-09-29')

def compare(old,new):
    old=old.copy();new=new.copy()
    old['date']=pd.to_datetime(old.date);new['date']=pd.to_datetime(new.date)
    new=new[new.date<=old.date.max()]
    o=old.set_index('date').nav.astype(float);n=new.set_index('date').nav.astype(float)
    idx=o.index.intersection(n.index)
    err=(n.loc[idx]/o.loc[idx]-1).abs()
    bad=err[err>1e-10]
    return dict(rows=len(idx),missing_reference_dates=int(len(o.index.difference(n.index))),
                extra_dates=int(len(n.index.difference(o.index))),max_relative_error=float(err.max()),
                first_mismatch=None if bad.empty else str(bad.index[0].date()),
                pass_parity=bool(not len(bad) and len(idx)==len(o) and len(n)==len(o)))

def normalize_signal(sig):
    sig=sig.copy()
    if 'sat_lead' not in sig and 'w_sat' in sig:sig['sat_lead']=sig.w_sat.astype(float)>.5
    if 'w_sat' not in sig:sig['w_sat']=sig.sat_lead.astype(float)
    if 'book' not in sig:sig['book']=np.where(sig.sat_lead.astype(bool),ls.BOOK_SAT,ls.BOOK_COMP)
    return sig.sort_values('date').reset_index(drop=True)

def main():
    global CUTOFF
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--asof',default='2026-09-29')
    p.add_argument('--extended-parents',type=Path)
    p.add_argument('--market-tip',type=Path,default=ROOT/'forward/e21/live_market.csv')
    p.add_argument('--dividend-tip',type=Path,default=ROOT/'data/dividend_events/e22_dividend_events.csv')
    p.add_argument('--e22-version',default=ls.E22_VERSION)
    p.add_argument('--upper-input-ref',default='97933be85192e8d0ef89695be0c292342bba694d')
    p.add_argument('--input-ref',help='Git commit that generated archived mothers; freeze its input files')
    a=p.parse_args();CUTOFF=pd.Timestamp(a.asof);a.out=a.out.resolve()
    if not (ROOT/'repro').resolve() in a.out.parents:raise ValueError('output must be isolated under repro')
    a.out.mkdir(parents=True,exist_ok=False)
    inputs=set();results={}
    def materialize(path):
        path=Path(path)
        if a.input_ref:
            rel=path.relative_to(ROOT)
            target=a.out/'source_snapshot'/a.input_ref/rel
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                result=subprocess.run(['git','show',a.input_ref+':'+str(rel)],cwd=ROOT,capture_output=True,check=True)
                target.write_bytes(result.stdout)
            path=target
        inputs.add(path)
        return path
    def read(path):
        path=materialize(path)
        d=pd.read_csv(path,dtype={'code':str});d['date']=pd.to_datetime(d.date)
        d=d[d.date<=CUTOFF].copy()
        if a.extended_parents:
            if path.name.startswith('daily_shares_'):
                tip_path=a.extended_parents/'outputs'/path.name
                inputs.add(tip_path.resolve())
                tip=pd.read_csv(tip_path,dtype={'code':str},parse_dates=['date'])
                d=pd.concat([d[d.date<='2026-09-29'],tip[tip.date>'2026-09-29']],ignore_index=True)
            elif path.name=='p3_t0_state_signal.csv':
                comp=pd.read_csv(a.extended_parents/'nav_COMP_H150_x_A20.csv',parse_dates=['date'])
                sat=pd.read_csv(a.extended_parents/'nav_SAT_A20_RELAX.csv',parse_dates=['date'])
                inputs.update([(a.extended_parents/('nav_'+b+'.csv')).resolve() for b in (ls.BOOK_COMP,ls.BOOK_SAT)])
                tip=build_sat_lead_signal(comp=comp,sat=sat)
                d=pd.concat([normalize_signal(d[d.date<='2026-09-29']),tip[tip.date>'2026-09-29']],ignore_index=True)
            elif path.name=='live_market.csv':
                tip=pd.read_csv(a.market_tip,dtype={'code':str},parse_dates=['date'])
                inputs.add(a.market_tip.resolve())
                d=pd.concat([d[d.date<='2026-09-29'],tip[(tip.date>'2026-09-29')&(tip.date<=CUTOFF)]],ignore_index=True)
        return d
    def nav(path):
        path=Path(path);inputs.add(path)
        d=pd.read_csv(path,parse_dates=['date'])
        return d[d.date<=CUTOFF][['date','nav']]
    def save(name,d):d.to_csv(a.out/(name+'.csv'),index=False)
    def check(name,d,path):
        save(name,d);results[name]=compare(nav(path),d)
        print(name,results[name],flush=True)
        (a.out/'parity_progress.json').write_text(json.dumps(results,indent=2))
    print('Building original live-stack features through 9/29',flush=True)
    market_file=materialize(ROOT/'forward/e21/live_market.csv')
    market=load_market(market_file)
    if a.extended_parents:
        market=market[market.date<='2026-09-29']
        market=append_market(market,load_market(a.market_tip),CUTOFF)
        inputs.add(a.market_tip.resolve())
    market=market[market.date<=CUTOFF].copy()
    dividend_path=materialize(ROOT/'data/dividend_events/e22_dividend_events.csv')
    if a.extended_parents:
        dividend_path=append_dividends(dividend_path,a.dividend_tip,a.out/'dividends_append_only.csv',CUTOFF)
        inputs.add(a.dividend_tip.resolve())
    dividends=load_dividends(dividend_path)
    _,sleeve,_,regime=ls.e16_features(market)
    cal=pd.DatetimeIndex(sorted(market.date.unique()))
    lows,highs=ls.build_low_high_catalog(market,cal,list(ls.FIN))
    kd=ls.build_kd_season_tilt_scores(market,dividends,list(ls.FIN),
        k_thresh=float(ls.LIVE_KD['k_thresh']),season_start=ls.LIVE_KD['season_start'],
        season_end=ls.LIVE_KD['season_end'],pre_days=int(ls.LIVE_KD['pre_days']),
        active_score=float(ls.LIVE_KD['active_score']))
    buy_ok=ls.build_pre_exdiv_window_buy_ok(cal,dividends,list(ls.FIN),pre_days=int(ls.LIVE_KD['pre_days']),also_stock_ex=True)
    scores=ls._buy(kd,lows);sell=ls._sell(highs)
    target=ls._target_live(ls._sleeve_score(market,sleeve,ls.LIVE_SLEEVE_ALPHA),regime)
    px=ls._close_panel(market,ls.SOFT_CORE)
    shares={book:shares_panel_from_long(read(ROOT/'repro/fin-sat-path3-daily-share-ssot-stagea/outputs'/('daily_shares_'+book+'.csv'))) for book in (ls.BOOK_COMP,ls.BOOK_SAT)}
    sig=normalize_signal(read(ROOT/'repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_signal.csv'))
    fin,tel=ls._path3_mix_score_panels(sig=sig,shares_by_book=shares,px=px,cal=cal)
    fin.to_csv(a.out/'financial_scores.csv');tel.to_csv(a.out/'telecom_scores.csv');target.to_csv(a.out/'sleeve_targets.csv')
    ls.E22_VERSION=a.e22_version
    print('Simulating offense for original COOL exposure',flush=True)
    off,_,_=ls.simulate_core(market,target,regime,dividends,apply_e22=True,apply_stock_div=True,
       capital=float(ls.DEFAULT_CAPITAL),lot_size=int(ls.BOARD_LOT),financial_alloc=ls.FIN_PRE_EXDIV_KD,
       telecom_alloc=ls.TEL_EQUAL,fin_name_scores=scores,fin_buy_ok=buy_ok,fin_sell_scores=sell,e22_version=a.e22_version)
    cool=ls._cool_from_offense(market,off);cool.to_csv(a.out/'cool_exposure.csv')
    sim=ls.simulate_core
    current_sink=[]
    def captured(*args,**kwargs):return sim(*args,**kwargs,daily_pos_sink=current_sink)
    ls.simulate_core=captured
    for name,fs,ts,fa,ta,bo in [
        ('BASE',scores,None,ls.FIN_PRE_EXDIV_KD,ls.TEL_EQUAL,buy_ok),
        ('P3',fin,tel,ls.FIN_RS_SOFT_TILT,ls.TEL_RS_SOFT_TILT,None)]:
        print('Simulating original '+name,flush=True);current_sink=[]
        n,f,meta=ls._sim(market,target,regime,dividends,scores=fs,buy_ok=bo,sell=sell,exposure=cool,
            financial_alloc=fa,telecom_alloc=ta,tel_scores=ts)
        filename='nav_BASE_LIVE_FUSE_COOL.csv' if name=='BASE' else 'nav_LIVE_P3_WITHIN.csv'
        check('nav_'+name,n,ls.OUT/filename)
        save('fills_'+name,f);save('shares_'+name,pd.DataFrame(current_sink))
        (a.out/('meta_'+name+'.json')).write_text(json.dumps(meta,indent=2,default=str))
    # Exact archived upper-layer reconstruction independent of current base rerun.
    # This isolates stitching/gate semantics from mutable lower-layer inputs.
    base=nav(ls.OUT/'nav_BASE_LIVE_FUSE_COOL.csv');p3=nav(ls.OUT/'nav_LIVE_P3_WITHIN.csv')
    l4=nav(fl.ALIGN/'nav_L4_LIVE_P3_WITHIN.csv')
    if a.extended_parents:
        base=pd.read_csv(a.out/'nav_BASE.csv',parse_dates=['date'])[['date','nav']]
        p3=pd.read_csv(a.out/'nav_P3.csv',parse_dates=['date'])[['date','nav']]
        l4=p3.copy()
    rp=fl._returns(p3);rb=fl._returns(base)
    prem=pd.concat({'p':rp,'b':rb},axis=1,join='inner').dropna()
    gate=(fl._trail_sum(prem.p-prem.b,42).fillna(0)>=-.01).astype(float)
    lower_ref=a.input_ref
    a.input_ref=a.upper_input_ref
    shares={book:shares_panel_from_long(read(ROOT/'repro/fin-sat-path3-daily-share-ssot-stagea/outputs'/('daily_shares_'+book+'.csv'))) for book in (ls.BOOK_COMP,ls.BOOK_SAT)}
    sig=normalize_signal(read(ROOT/'repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_signal.csv'))
    raw=read(ROOT/'forward/e21/live_market.csv')
    sc_px=ls._close_panel(raw,ls.SOFT_CORE)
    weights={b:fl._book_soft_weights(s,sc_px) for b,s in shares.items()}
    sc_on,_=fl.simulate_fill(fill='ALWAYS_WITHIN',weights_by_book=weights,px=sc_px,signal=sig,i3_on=pd.Series(1.,index=prem.index))
    sc_cash,_=fl.simulate_fill(fill='FT_TO_CASH',weights_by_book=weights,px=sc_px,signal=sig,i3_on=gate)
    unlock=ROOT/'repro/tipsoft-ip3-unlock-path-stagea/outputs'
    check('nav_SC_WITHIN',sc_on,unlock/'nav_B_ALWAYS_WITHIN.csv')
    check('nav_SC_TRAIL42_CASH',sc_cash,unlock/'nav_B_TRAIL42_GE_m001__FT_TO_CASH.csv')
    panel=pd.concat({'l4':fl._returns(l4),'on':fl._returns(sc_on),'cash':fl._returns(sc_cash)},axis=1,join='inner').dropna()
    trail=pd.DataFrame({'date':panel.index,'nav':(1+(panel.l4+(panel.cash-panel.on))).cumprod().values})
    check('nav_TRAIL',trail,ROOT/'repro/tipsoft-ip3-trail42-cash-paper-observe/outputs/nav_TRAIL42_FT_CASH.csv')
    save('nav_L4',l4)
    paired=pd.concat({'l4':fl._returns(l4),'trail':fl._returns(trail)},axis=1,join='inner').dropna()
    curves=(1+paired).cumprod();dd=curves/curves.cummax()-1
    want=dd.trail>=dd.l4
    dd_nav=pd.DataFrame({'date':paired.index,'nav':(1+paired.trail.where(want,paired.l4)).cumprod().values})
    check('nav_DD_SWITCH',dd_nav,ROOT/'repro/tipsoft-ip3-trail42-l4-switch-paper-observe/outputs/nav_TRAIL42_L4_DD_SWITCH.csv')
    controls=pd.DataFrame({'want_trail':want,'l4_dd':dd.l4,'trail_dd':dd.trail,'premium42':fl._trail_sum(prem.p-prem.b,42),
                           'trail_on':gate.astype(bool)})
    controls=controls.dropna(subset=['l4_dd','trail_dd'])
    # Match actual consumers: CSV roundtrip can flip exact DD ties at machine precision.
    controls['want_trail']=live_gate.want_trail_series(l4_nav_path=a.out/'nav_L4.csv',trail_nav_path=a.out/'nav_TRAIL.csv')
    controls['trail_on']=live_gate.trail42_on_series(l3_nav_path=a.out/'nav_BASE.csv',p3_nav_path=a.out/'nav_P3.csv')
    controls['active']=~controls.want_trail.astype(bool)|controls.trail_on.fillna(True).astype(bool)
    controls.to_csv(a.out/'original_controls.csv')
    (a.out/'summary.json').write_text(json.dumps(dict(status='PREFIX_PARITY' if all(x['pass_parity'] for x in results.values()) else 'PREFIX_MISMATCH',
        cutoff=str(CUTOFF.date()),extended_parents=None if not a.extended_parents else str(a.extended_parents),input_ref=lower_ref,upper_input_ref=a.upper_input_ref,e22_version=a.e22_version,parity=results,
        program_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(inputs)},
        limits=['BASE/P3 fully rerun, share parents and signal are archived inputs, not regenerated',
                'Upper layers replay archived BASE/P3 to isolate original stitch parity',
                'No T0 validation or shared-capital proof for return stitching; append-only legacy diagnostic is not production-ready']),indent=2))
    print('Finished',results,flush=True)

if __name__=='__main__':main()
