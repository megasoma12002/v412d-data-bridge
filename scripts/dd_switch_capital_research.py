#!/usr/bin/env python3
"""Fixed small policy screen + retrospective annual walk-forward; return proxy.

This is not the full live portfolio or a share fill reconstruction. It cannot
establish executable optimality. Parameters and ranking are declared beforehand.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from dd_switch_capital_policy import POLICIES, CapitalController

ROOT=Path(__file__).resolve().parents[1]

def stats(frame):
    if frame.empty:return {}
    # Include starting capital when computing window return and MDD.
    capital=float(frame.pre_nav.iloc[0])
    values=np.r_[capital,frame.nav.to_numpy()]
    years=(frame.date.iloc[-1]-frame.date.iloc[0]).days/365.25
    return dict(return_pct=(values[-1]/capital-1)*100,
                cagr_pct=((values[-1]/capital)**(1/years)-1)*100 if years>0 else None,
                mdd_pct=float((values/np.maximum.accumulate(values)-1).min()*100),
                n=len(frame),scale_mean=float(frame.scale.mean()),
                extra_drag_sum_pct=float(frame.drag.sum()*100))

def simulate(returns,policy,drag_bp=10,schedule=None):
    controller=CapitalController(policy)
    value=1.0;old_scale=1.0;past=[];rows=[]
    for day,r in returns.items():
        if schedule is not None and day.year in schedule:
            controller.policy=schedule[day.year]
        momentum=float(np.prod(1+np.array(past[-20:]))-1) if past else 0.0
        decision=controller.observe(value,momentum)
        scale=decision['scale']
        drag=abs(scale-old_scale)*drag_bp/10000
        before=value
        value*=1+scale*float(r)-drag
        if value<=0:raise ValueError('Non-positive model NAV')
        rows.append(dict(date=day,pre_nav=before,nav=value,scale=scale,drag=drag,
                         policy=controller.policy.name,regime=decision['regime'],
                         account_dd_at_signal=decision['account_dd'],parent_return=float(r)))
        past.append(value/before-1);old_scale=scale
    return pd.DataFrame(rows)

def choose(returns,drag_bp=10):
    scored=[]
    for p in POLICIES:
        s=stats(simulate(returns,p,drag_bp))
        # First meet MDD <=15%; then maximize CAGR. If all fail, minimize MDD.
        key=(s['mdd_pct']>=-15,s['cagr_pct'] if s['mdd_pct']>=-15 else s['mdd_pct'])
        scored.append((key,p,s))
    return max(scored,key=lambda r:r[0])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'repro/dd-switch-clock-attribution/interval_DD_lag1_proxy.csv')
    p.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-capital-research')
    a=p.parse_args()
    source=pd.read_csv(a.source,parse_dates=['date']).set_index('date').nav
    if not source.index.is_unique or not source.index.is_monotonic_increasing or source.isna().any() or (source<=0).any():
        raise ValueError('Invalid proxy NAV')
    returns=source.pct_change().fillna(0)
    cutoff=pd.Timestamp('2019-01-01')
    selected=choose(returns[returns.index<cutoff])
    schedule={};selection=[]
    for year in range(2019,int(returns.index.max().year)+1):
        train=returns[(returns.index<pd.Timestamp(year,1,1))&(returns.index>=pd.Timestamp(year-5,1,1))]
        _,policy,s=choose(train)
        schedule[year]=policy
        selection.append(dict(year=year,train_start=str(train.index.min().date()),train_end=str(train.index.max().date()),
                              policy=policy.name,train_metrics=s))
    windows={'full':(returns.index.min(),returns.index.max()),
             'pre2019':(returns.index.min(),pd.Timestamp('2018-12-31')),
             '2019_2022':(cutoff,pd.Timestamp('2022-12-31')),
             '2023_plus':(pd.Timestamp('2023-01-01'),returns.index.max()),
             '2019_plus':(cutoff,returns.index.max())}
    metrics=[];runs={}
    for drag_bp in (0,10,30):
        for policy in POLICIES:
            name=policy.name+'_'+str(drag_bp)+'bp'
            runs[name]=simulate(returns,policy,drag_bp)
        # Training and annual selection use the matching cost assumption.
        cost_schedule={year:choose(returns[(returns.index<pd.Timestamp(year,1,1))&(returns.index>=pd.Timestamp(year-5,1,1))],drag_bp)[1] for year in schedule}
        name='AUTO_WALKFORWARD_'+str(drag_bp)+'bp'
        runs[name]=simulate(returns,POLICIES[0],drag_bp,cost_schedule)
    for name,frame in runs.items():
        for window,(start,end) in windows.items():
            s=stats(frame[(frame.date>=start)&(frame.date<=end)])
            metrics.append(dict(model=name,window=window,**s,
                                meets_20cagr_15mdd=s['cagr_pct']>=20 and s['mdd_pct']>=-15))
    a.out.mkdir(parents=True,exist_ok=True)
    result=pd.DataFrame(metrics)
    result.to_csv(a.out/'metrics.csv',index=False)
    for name in ('BASELINE_10bp','AUTO_WALKFORWARD_10bp',selected[1].name+'_10bp'):
        runs[name].to_csv(a.out/(name+'.csv'),index=False)
    summary=dict(status='RESEARCH_PROXY_NO_LIVE_PROMOTION',source=str(a.source.relative_to(ROOT)) if a.source.is_relative_to(ROOT) else str(a.source),
                 source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),
                 fixed_policies=[vars(p) for p in POLICIES],ranking='Meet observed MDD <=15%, then highest CAGR; otherwise smallest MDD',
                 pre2019_selected=selected[1].name,annual_selection_10bp=selection,
                 constraints=dict(target_cagr_pct=20,max_observed_mdd_pct=15),
                 limitations=['Input is fixed-parent DD one-common-observation-lag interval return proxy, not complete live portfolio',
                              'Missing mother dates are aggregated; no daily decisions/fills inside gaps',
                              'Cash return assumed zero; extra drag bps per allocation change is assumed, not measured share turnover',
                              'Annual selection retrospective and causal, not a new blind out-of-sample experiment',
                              'CAGR calendar-based, MDD observed intervals only; no brokerage or corporate-action replay',
                              'Whole-account historical live replay and genuine intraday evidence remain prerequisites'])
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(result[(result.window=='2019_plus')&result.model.str.endswith('10bp')].to_string(index=False))
    print('Pre2019 selection:',selected[1].name)
    print('Annual selections:',[(x['year'],x['policy']) for x in selection])

if __name__=='__main__':main()
