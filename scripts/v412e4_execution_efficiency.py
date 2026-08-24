#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import v412d_formal_router as d
import v412e1_crisis_buffer as e1
import v412e11_graduated_crisis as e11
import v412e2_e3_three_rounds as e3mod

PERIODS={"2005_2014":("2005-03-01","2014-12-31"),"2015_2017":("2015-01-01","2017-12-31"),"2018_2020":("2018-01-01","2020-12-31"),"2021_2022":("2021-01-01","2022-12-31"),"2023_2025":("2023-01-01","2025-12-31"),"2026":("2026-01-01","2026-12-31")}

def partial_rebalance(target,fraction,min_change):
    cur=pd.Series(0.,index=target.columns); prev_target=cur.copy(); rows=[]
    for _,candidate in target.iterrows():
        changed=float((candidate-prev_target).abs().sum())>1e-12
        if changed:
            delta=candidate-cur
            if float(delta.abs().sum())>=min_change: cur=cur+fraction*delta
            prev_target=candidate.copy()
        rows.append(cur.copy())
    return pd.DataFrame(rows,index=target.index,columns=target.columns)

def stats(nav,w,cost,period):
    m=e1.metrics(nav,period); sl=slice(period[0],period[1])
    m["turnover"]=float(w.diff().abs().sum(axis=1).loc[sl].sum()); m["cost_sum"]=float(cost.loc[sl].sum())
    return m

def score(m): return m["ret"]+.12*m["sharpe"]+m["mdd"]-.0015*m["turnover"]

def run(ac,ao,signal,exposure,cost_mult=1): return e11.nav_with_exposure(ac,ao,signal,exposure,cost_mult)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--adjusted',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw); adj=pd.read_csv(a.adjusted); z=d.prep(raw); rc,ro,ac,ao=e1.aligned_matrices(raw,adj); scores=d.make_scores(z,1)
    q=e3mod.raw_risk_features(z); exposure=e3mod.exposure_controller(q,'voltarget',.5,20,.14,.5); ones=pd.Series(1.,index=rc.index)
    d_sig,_=d.targets(scores,list(rc.index),21,2,75); dnav,dw,dc,_=run(ac,ao,d_sig,ones)
    rt=2*d.FEE+d.TAX
    e3_sig=e1.buffered_targets(scores,list(rc.index),0,5*rt,42); e3nav,e3w,e3c,_=run(ac,ao,e3_sig,exposure)

    # E4-A: select only on data through 2020. 2021-2022 is reused confirmation, not new OOS.
    A=[]; aruns=[]; trainA=("2005-03-01","2020-12-31")
    for rb in (0,1):
      for hm in (5,10,20,30):
       for mh in (42,63,84):
        sig=e1.buffered_targets(scores,list(rc.index),rb,hm*rt,mh); nav,w,cost,_=run(ac,ao,sig,exposure); m=stats(nav,w,cost,trainA)
        row={"rank_buffer":rb,"hurdle_mult":hm,"min_hold":mh,**{"train_"+k:v for k,v in m.items()},"train_score":score(m)}; A.append(row); aruns.append((row,sig,nav,w,cost))
    Ag=pd.DataFrame(A).sort_values('train_score',ascending=False); Ag.to_csv(out/'e4a_grid.csv',index=False); awin=max(aruns,key=lambda x:x[0]['train_score'])
    aval=[]
    for runx in sorted(aruns,key=lambda x:x[0]['train_score'],reverse=True)[:8]:
        r,sig,nav,w,cost=runx; m=stats(nav,w,cost,PERIODS['2021_2022']); b=stats(e3nav,e3w,e3c,PERIODS['2021_2022'])
        aval.append({**{k:r[k] for k in ['rank_buffer','hurdle_mult','min_hold']},**{'confirm_'+k:v for k,v in m.items()},'e3_ret':b['ret'],'e3_sharpe':b['sharpe'],'e3_turnover':b['turnover']})
    pd.DataFrame(aval).to_csv(out/'e4a_confirmation.csv',index=False)

    # E4-B: partial execution around the A target. Select through 2022; 2023-2025 is reused confirmation.
    _,asig,_,_,_=awin; B=[]; bruns=[]; trainB=("2005-03-01","2022-12-31")
    for frac in (.25,.50,.75,1.0):
      for threshold in (.05,.10,.20):
        sig=partial_rebalance(asig,frac,threshold); nav,w,cost,_=run(ac,ao,sig,exposure); m=stats(nav,w,cost,trainB)
        row={"partial_fraction":frac,"min_weight_change":threshold,**{"train_"+k:v for k,v in m.items()},"train_score":score(m)}; B.append(row); bruns.append((row,sig,nav,w,cost))
    Bg=pd.DataFrame(B).sort_values('train_score',ascending=False); Bg.to_csv(out/'e4b_grid.csv',index=False); bwin=max(bruns,key=lambda x:x[0]['train_score'])
    bconfirm=[]
    for runx in sorted(bruns,key=lambda x:x[0]['train_score'],reverse=True):
        r,sig,nav,w,cost=runx; m=stats(nav,w,cost,PERIODS['2023_2025']); base=stats(e3nav,e3w,e3c,PERIODS['2023_2025'])
        bconfirm.append({**{k:r[k] for k in ['partial_fraction','min_weight_change']},**{'confirm_'+k:v for k,v in m.items()},'e3_ret':base['ret'],'e3_sharpe':base['sharpe'],'e3_turnover':base['turnover']})
    pd.DataFrame(bconfirm).to_csv(out/'e4b_confirmation.csv',index=False)

    # E4-C: blend execution targets, but retain the frozen E3 risk controller. Selection uses data through 2025.
    _,bsig,_,_,_=bwin; C=[]; cruns=[]; trainC=("2005-03-01","2025-12-31")
    for efficient_weight in (.25,.50,.75,1.0):
        sig=efficient_weight*bsig+(1-efficient_weight)*d_sig
        nav,w,cost,_=run(ac,ao,sig,exposure); m=stats(nav,w,cost,trainC)
        # minimax across known regimes guards against one-period domination.
        sharpes=[e1.metrics(nav,p)['sharpe'] for p in PERIODS.values() if p[1]<='2025-12-31']
        robust=score(m)+.08*min(sharpes)
        row={"efficient_weight":efficient_weight,**{"train_"+k:v for k,v in m.items()},"min_regime_sharpe":min(sharpes),"robust_score":robust}; C.append(row); cruns.append((row,sig,nav,w,cost))
    Cg=pd.DataFrame(C).sort_values('robust_score',ascending=False); Cg.to_csv(out/'e4c_grid.csv',index=False); cwin=max(cruns,key=lambda x:x[0]['robust_score'])

    # Full descriptive comparison. These later windows are not relabeled as fresh OOS.
    selected={'Frozen_D':(dnav,dw,dc),'Frozen_E3':(e3nav,e3w,e3c),'E4_A':awin[2:5],'E4_B':bwin[2:5],'E4_C':cwin[2:5]}
    summary=[]
    for name,(nav,w,cost) in selected.items():
      for period,p in PERIODS.items(): summary.append({'strategy':name,'period':period,**stats(nav,w,cost,p)})
    pd.DataFrame(summary).to_csv(out/'e4_multiregime_summary.csv',index=False)
    # Cost stress for the final engineering candidate.
    rr=cwin[0]; csig=cwin[1]; stress=[]
    for cm in (0,1,2,3):
        nav,w,cost,_=run(ac,ao,csig,exposure,cm)
        for period in ('2021_2022','2023_2025','2026'): stress.append({'cost_multiple':cm,'period':period,**stats(nav,w,cost,PERIODS[period])})
    pd.DataFrame(stress).to_csv(out/'e4c_cost_stress.csv',index=False)
    cwin[3].reset_index().to_csv(out/'e4c_weights.csv',index=False)
    status={"version":"V4.12-E4","rounds":3,"new_unseen_oos_available":False,"promotion_eligible":False,
            "formal_strategy":"V4.12-D","frozen_risk_overlay":"E3 voltarget max_cut=.5 target_vol=.14 blend=.5 up_days=20",
            "E4_A_winner":{k:awin[0][k] for k in ['rank_buffer','hurdle_mult','min_hold']},
            "E4_B_winner":{k:bwin[0][k] for k in ['partial_fraction','min_weight_change']},
            "E4_C_winner":{"efficient_weight":cwin[0]['efficient_weight']},
            "warning":"2021-2026 were previously revealed; confirmations are robustness engineering, not fresh blind validation"}
    (out/'e4_status.json').write_text(json.dumps(status,indent=2)); print(Ag.head(8).to_string(index=False)); print(Bg.to_string(index=False)); print(Cg.to_string(index=False)); print(pd.DataFrame(summary).round(4).to_string(index=False)); print(status)

if __name__=='__main__': main()
