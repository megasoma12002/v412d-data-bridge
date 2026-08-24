#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

import v412d_formal_router as d
import v412e1_crisis_buffer as e1

TRAIN=e1.TRAIN; VALID=e1.VALID; OOS=e1.OOS


def graduated_exposure(risk, medium, severe, ramp_days):
    desired=np.where(risk.votes>=3,severe,np.where(risk.votes>=2,medium,1.0))
    current=1.0; worsen_count=0; out=[]
    for target in desired:
        if target < current:
            worsen_count += 1
            if worsen_count >= 2: current=float(target)
        else:
            worsen_count=0
            if target > current: current=min(float(target),current+(1.0-current)/ramp_days)
        out.append(current)
    return pd.Series(out,index=risk.index,name="exposure")


def no_trade_band(signal_w, band):
    cur=pd.Series(0.0,index=signal_w.columns); rows=[]
    for _,candidate in signal_w.iterrows():
        if float((candidate-cur).abs().sum()) >= band-1e-12: cur=candidate.copy()
        rows.append(cur.copy())
    return pd.DataFrame(rows,index=signal_w.index,columns=signal_w.columns)


def nav_with_exposure(eval_close,eval_open,signal_w,exposure,cost_mult=1):
    scaled=signal_w.mul(exposure,axis=0); w=scaled.shift(1).fillna(0); prev=w.shift(1).fillna(0)
    overnight=(prev*(eval_open/eval_close.shift(1)-1).replace([np.inf,-np.inf],np.nan).fillna(0)).sum(axis=1)
    intraday=(w*(eval_close/eval_open-1).replace([np.inf,-np.inf],np.nan).fillna(0)).sum(axis=1)
    delta=w-prev
    cost=cost_mult*(delta.clip(lower=0).sum(axis=1)*d.FEE+(-delta.clip(upper=0)).sum(axis=1)*(d.FEE+d.TAX))
    return (1+overnight+intraday-cost).cumprod(),w,cost,scaled


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",required=True); ap.add_argument("--adjusted",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw); adj=pd.read_csv(a.adjusted); z=d.prep(raw)
    rc,ro,ac,ao=e1.aligned_matrices(raw,adj); scores=d.make_scores(z,1)
    d_sig,_=d.targets(scores,list(rc.index),21,2,75); d_nav,d_w,d_cost,_=nav_with_exposure(ac,ao,d_sig,pd.Series(1.0,index=rc.index))
    ew=(1+ac.pct_change(fill_method=None).mean(axis=1,skipna=True).fillna(0)).cumprod()
    # Thresholds are inherited from the E1 Train plateau; E1.1 changes structure, not post-Validation thresholds.
    risk=e1.risk_state(z,-.18,.30,.30)
    risk_defs=[(.80,.50,10),(.70,.40,10),(.80,.40,20)]
    buffer_defs=[(rb,gap,mh,band) for rb in (0,1) for gap in (0,.05) for mh in (21,42) for band in (.05,.10)]
    sig_cache={}
    for rb,gap,mh,band in buffer_defs:
        base=e1.buffered_targets(scores,list(rc.index),rb,gap,mh)
        sig_cache[(rb,gap,mh,band)]=no_trade_band(base,band)
    grid=[]; runs=[]
    for medium,severe,ramp in risk_defs:
        exposure=graduated_exposure(risk,medium,severe,ramp)
        for rb,gap,mh,band in buffer_defs:
            sig=sig_cache[(rb,gap,mh,band)]; nav,w,cost,scaled=nav_with_exposure(ac,ao,sig,exposure)
            m=e1.metrics(nav,TRAIN); crisis=e1.metrics(nav,("2008-01-01","2009-12-31"))
            turnover=float(w.diff().abs().sum(axis=1).loc[TRAIN[0]:TRAIN[1]].sum())
            score=m["ret"]+.10*m["sharpe"]+m["mdd"]-.0005*turnover
            row={"medium_exposure":medium,"severe_exposure":severe,"recovery_ramp":ramp,"rank_buffer":rb,
                 "score_gap":gap,"min_hold":mh,"no_trade_band":band,"train_score":score,"train_ret":m["ret"],
                 "train_mdd":m["mdd"],"train_sharpe":m["sharpe"],"train_turnover":turnover,
                 "crisis_2008_09_ret":crisis["ret"],"crisis_2008_09_mdd":crisis["mdd"]}
            grid.append(row); runs.append((row,nav,w,cost,exposure,scaled))
    g=pd.DataFrame(grid).sort_values("train_score",ascending=False); g.to_csv(out/"e11_train_grid.csv",index=False)
    top=g.head(max(12,len(g)//4)); keys={tuple(r[k] for k in ["medium_exposure","severe_exposure","recovery_ramp","rank_buffer","score_gap","min_hold","no_trade_band"]) for _,r in top.iterrows()}
    candidates=[]
    for run in runs:
        r=run[0]; key=tuple(r[k] for k in ["medium_exposure","severe_exposure","recovery_ramp","rank_buffer","score_gap","min_hold","no_trade_band"])
        if key not in keys: continue
        near=sum((r["medium_exposure"],r["severe_exposure"],r["recovery_ramp"],rb,gap,mh,band) in keys
                 for rb,gap,mh,band in buffer_defs)-1
        if near>=2: candidates.append(run)
    candidates=sorted(candidates,key=lambda x:x[0]["train_score"],reverse=True)[:8]
    base_val=e1.metrics(d_nav,VALID); valrows=[]; survivors=[]
    for run in candidates:
        r,nav,*_=run; m=e1.metrics(nav,VALID)
        passed=m["ret"]>0 and m["mdd"]>-.25 and m["sharpe"]>=base_val["sharpe"] and m["ret"]>=.80*base_val["ret"]
        valrows.append({**{k:r[k] for k in ["medium_exposure","severe_exposure","recovery_ramp","rank_buffer","score_gap","min_hold","no_trade_band"]},
                        **{"val_"+k:v for k,v in m.items()},"baseline_ret":base_val["ret"],"baseline_mdd":base_val["mdd"],"baseline_sharpe":base_val["sharpe"],"passed":passed})
        if passed: survivors.append(run)
    pd.DataFrame(valrows).to_csv(out/"e11_validation_gate.csv",index=False)
    status={"version":"V4.12-E1.1","train":TRAIN,"validation":VALID,"candidate_count":len(grid),
            "validation_candidate_count":len(candidates),"gate":"ret>0; mdd>-25%; Sharpe>=frozen D; ret>=80% frozen D","validation_pass":bool(survivors)}
    if not survivors:
        status["reason"]="No Train-selected robust-plateau candidate passed the frozen Validation gate"
        (out/"e11_status.json").write_text(json.dumps(status,indent=2)); print(g.head(12).to_string(index=False)); print(pd.DataFrame(valrows).to_string(index=False)); print(status); return
    winner=max(survivors,key=lambda x:x[0]["train_score"]); r,nav,w,cost,exposure,scaled=winner
    summary=[]
    for name,p in OOS.items():
        for label,series in (("E1.1",nav),("Frozen_D",d_nav),("EqualWeight12",ew)): summary.append({"strategy":label,"period":name,**e1.metrics(series,p)})
    pd.DataFrame(summary).to_csv(out/"e11_walkforward_summary.csv",index=False)
    pd.DataFrame({"date":nav.index,"e11_nav":nav.values,"frozen_d_nav":d_nav.values,"equal_weight_nav":ew.values,
                  "cost":cost.values,"risk_votes":risk.votes.values,"exposure":exposure.values}).to_csv(out/"e11_curves.csv",index=False)
    w.reset_index().to_csv(out/"e11_weights.csv",index=False)
    sens=[]
    for cm in (0,1,2,3):
        snav,*_=nav_with_exposure(ac,ao,sig_cache[(r["rank_buffer"],r["score_gap"],r["min_hold"],r["no_trade_band"])],exposure,cm)
        for name,p in OOS.items(): sens.append({"cost_multiple":cm,"period":name,**e1.metrics(snav,p)})
    pd.DataFrame(sens).to_csv(out/"e11_cost_sensitivity.csv",index=False)
    status.update({"winner":{k:(int(v) if k in ("recovery_ramp","rank_buffer","min_hold") else float(v)) for k,v in r.items() if k in ["medium_exposure","severe_exposure","recovery_ramp","rank_buffer","score_gap","min_hold","no_trade_band"]},
                   "signals":"raw/unadjusted only through T","execution":"T+1 open","evaluation":"corporate-action-adjusted","later_windows_used_for_selection":False})
    (out/"e11_status.json").write_text(json.dumps(status,indent=2)); print(g.head(12).to_string(index=False)); print(pd.DataFrame(valrows).to_string(index=False)); print(pd.DataFrame(summary).round(4).to_string(index=False)); print(status)

if __name__=="__main__": main()
