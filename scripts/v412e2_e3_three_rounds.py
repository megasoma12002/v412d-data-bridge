#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import v412d_formal_router as d
import v412e1_crisis_buffer as e1
import v412e11_graduated_crisis as e11

ROUNDS=[
 ("E2",("2005-03-01","2014-12-31"),("2015-01-01","2017-12-31"),"linear"),
 ("E2.1",("2005-03-01","2017-12-31"),("2018-01-01","2020-12-31"),"tail"),
 ("E3",("2005-03-01","2020-12-31"),("2021-01-01","2022-12-31"),"voltarget"),
]

def raw_risk_features(z):
    q=e1.risk_state(z,-.18,.30,.30)
    dd=np.clip((-q.dd120-.03)/.27,0,1)
    vol=np.clip((q.vol20-.16)/.24,0,1)
    breadth=np.clip((.60-q.breadth60)/.50,0,1)
    return q.assign(dd_risk=dd,vol_risk=vol,breadth_risk=breadth)

def exposure_controller(q,mode,max_cut,up_days,target_vol=.16,blend=.5):
    avg=.4*q.dd_risk+.3*q.vol_risk+.3*q.breadth_risk
    if mode=="linear": risk=avg
    elif mode=="tail": risk=.5*avg+.5*q[["dd_risk","vol_risk","breadth_risk"]].max(axis=1)
    else:
        vol_exp=(target_vol/q.vol20.replace(0,np.nan)).clip(.2,1).fillna(1)
        continuous=1-max_cut*avg
        desired=blend*continuous+(1-blend)*vol_exp
        return stateful_weekly(desired.clip(1-max_cut,1),up_days)
    return stateful_weekly((1-max_cut*risk).clip(1-max_cut,1),up_days)

def stateful_weekly(desired,up_days):
    cur=1.; out=[]
    for i,x in enumerate(desired.fillna(1.)):
        if i%5==0:
            if x<cur: cur=float(x)                       # fast down
            else: cur=min(float(x),cur+(1-cur)/up_days) # slow up
        out.append(cur)
    return pd.Series(out,index=desired.index,name="exposure")

def definitions(mode):
    out=[]
    if mode=="linear":
        risk=[(.3,10,.16,.5),(.5,10,.16,.5),(.5,20,.16,.5),(.7,20,.16,.5)]
    elif mode=="tail":
        risk=[(.4,10,.16,.5),(.5,20,.16,.5),(.6,20,.16,.5)]
    else:
        risk=[(.4,10,.14,.5),(.5,20,.14,.5),(.4,10,.18,.75),(.6,20,.18,.75)]
    for max_cut,up,target,blend in risk:
        for rb in (0,1):
            for cost_mult in (5,10):
                for mh in (21,42): out.append(dict(mode=mode,max_cut=max_cut,up_days=up,target_vol=target,blend=blend,rank_buffer=rb,cost_hurdle_mult=cost_mult,min_hold=mh))
    return out

def key(r): return tuple(r[x] for x in ["mode","max_cut","up_days","target_vol","blend","rank_buffer","cost_hurdle_mult","min_hold"])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--adjusted',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw); adj=pd.read_csv(a.adjusted); z=d.prep(raw); rc,ro,ac,ao=e1.aligned_matrices(raw,adj); scores=d.make_scores(z,1)
    q=raw_risk_features(z); ones=pd.Series(1.,index=rc.index)
    d_sig,_=d.targets(scores,list(rc.index),21,2,75); d_nav,dw,dc,ds=e11.nav_with_exposure(ac,ao,d_sig,ones)
    ew=(1+ac.pct_change(fill_method=None).mean(axis=1,skipna=True).fillna(0)).cumprod()
    # Score hurdle is explicitly tied to estimated round-trip cost, not target-weight distance.
    rt_cost=2*d.FEE+d.TAX
    sig_cache={}
    for rb in (0,1):
      for cm in (5,10):
       for mh in (21,42):
        gap=cm*rt_cost
        sig_cache[(rb,cm,mh)]=e1.buffered_targets(scores,list(rc.index),rb,gap,mh)
    all_status=[]; final_winner=None
    for version,train,valid,mode in ROUNDS:
        rows=[]; runs=[]
        for cfg in definitions(mode):
            exp=exposure_controller(q,mode,cfg['max_cut'],cfg['up_days'],cfg['target_vol'],cfg['blend'])
            sig=sig_cache[(cfg['rank_buffer'],cfg['cost_hurdle_mult'],cfg['min_hold'])]
            nav,w,cost,scaled=e11.nav_with_exposure(ac,ao,sig,exp)
            m=e1.metrics(nav,train); crisis=e1.metrics(nav,("2008-01-01","2009-12-31")); turnover=float(w.diff().abs().sum(axis=1).loc[train[0]:train[1]].sum())
            score=m['ret']+.10*m['sharpe']+m['mdd']-.0005*turnover
            row={**cfg,'train_score':score,'train_ret':m['ret'],'train_mdd':m['mdd'],'train_sharpe':m['sharpe'],'train_turnover':turnover,'crisis_mdd':crisis['mdd']}
            rows.append(row); runs.append((row,nav,w,cost,exp,scaled))
        g=pd.DataFrame(rows).sort_values('train_score',ascending=False); g.to_csv(out/f'{version.lower().replace(".","")}_train_grid.csv',index=False)
        top=g.head(max(8,len(g)//4)); topkeys={key(r) for _,r in top.iterrows()}; candidates=[]
        for run in runs:
            if key(run[0]) not in topkeys: continue
            r=run[0]; near=sum((r['mode'],mc,ud,tv,bl,rb,cm,mh) in topkeys for mc,ud,tv,bl in {(x['max_cut'],x['up_days'],x['target_vol'],x['blend']) for x in definitions(mode)} for rb in (0,1) for cm in (5,10) for mh in (21,42))-1
            if near>=2: candidates.append(run)
        candidates=sorted(candidates,key=lambda x:x[0]['train_score'],reverse=True)[:8]
        base=e1.metrics(d_nav,valid); valrows=[]; survivors=[]
        for run in candidates:
            r,nav,*_=run; m=e1.metrics(nav,valid)
            passed=m['ret']>0 and m['mdd']>-.25 and m['sharpe']>=base['sharpe'] and m['ret']>=.80*base['ret']
            valrows.append({**{k:r[k] for k in ['mode','max_cut','up_days','target_vol','blend','rank_buffer','cost_hurdle_mult','min_hold']},**{'val_'+k:v for k,v in m.items()},'baseline_ret':base['ret'],'baseline_mdd':base['mdd'],'baseline_sharpe':base['sharpe'],'passed':passed})
            if passed: survivors.append(run)
        pd.DataFrame(valrows).to_csv(out/f'{version.lower().replace(".","")}_validation_gate.csv',index=False)
        status={'version':version,'train':train,'validation':valid,'candidate_count':len(rows),'validation_candidate_count':len(candidates),'validation_pass':bool(survivors),'gate':'ret>0; mdd>-25%; Sharpe>=frozen D; ret>=80% frozen D'}
        if survivors:
            win=max(survivors,key=lambda x:x[0]['train_score']); status['winner']={k:win[0][k] for k in ['mode','max_cut','up_days','target_vol','blend','rank_buffer','cost_hurdle_mult','min_hold']}
            final_winner=win if version=='E3' else final_winner
        else: status['reason']='No Train-selected robust-plateau candidate passed the frozen gate'
        (out/f'{version.lower().replace(".","")}_status.json').write_text(json.dumps(status,indent=2)); all_status.append(status)
        print('\n',version); print(g.head(8).to_string(index=False)); print(pd.DataFrame(valrows).to_string(index=False)); print(status)
    if final_winner is not None:
        r,nav,w,cost,exp,scaled=final_winner; summary=[]
        periods={'E3_Validation':('2021-01-01','2022-12-31'),'Blind_2023_2025':('2023-01-01','2025-12-31'),'Final_2026':('2026-01-01','2026-12-31')}
        for name,p in periods.items():
            for label,series in [('E3',nav),('Frozen_D',d_nav),('EqualWeight12',ew)]: summary.append({'strategy':label,'period':name,**e1.metrics(series,p)})
        pd.DataFrame(summary).to_csv(out/'e3_oos_summary.csv',index=False)
        sens=[]
        sig=sig_cache[(r['rank_buffer'],r['cost_hurdle_mult'],r['min_hold'])]
        for cm in (0,1,2,3):
            snav,*_=e11.nav_with_exposure(ac,ao,sig,exp,cm)
            for name,p in periods.items(): sens.append({'cost_multiple':cm,'period':name,**e1.metrics(snav,p)})
        pd.DataFrame(sens).to_csv(out/'e3_cost_sensitivity.csv',index=False)
        pd.DataFrame({'date':nav.index,'e3_nav':nav.values,'frozen_d_nav':d_nav.values,'equal_weight_nav':ew.values,'exposure':exp.values,'cost':cost.values}).to_csv(out/'e3_curves.csv',index=False)
        w.reset_index().to_csv(out/'e3_weights.csv',index=False)
    (out/'three_round_status.json').write_text(json.dumps({'rounds':all_status,'blind_opened':final_winner is not None},indent=2))

if __name__=='__main__': main()
