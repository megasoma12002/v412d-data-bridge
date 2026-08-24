#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd

TRAIN=("2010-01-01","2018-12-31")
VALID=("2019-01-01","2022-12-31")
PERIODS={"Train":TRAIN,"Validation":VALID,"Blind":("2023-01-01","2025-12-31"),"Final":("2026-01-01","2099-12-31")}
FEE=0.001425*0.6
TAX=0.003

def metrics(nav,start,end):
    s=nav.loc[start:end].dropna()
    if len(s)<2: return {"n":len(s),"return":np.nan,"mdd":np.nan,"sharpe":np.nan,"vol":np.nan}
    r=s.pct_change().dropna()
    return {"n":len(s),"return":s.iloc[-1]/s.iloc[0]-1,
            "mdd":(s/s.cummax()-1).min(),
            "sharpe":r.mean()/r.std()*np.sqrt(252) if r.std()>0 else 0,
            "vol":r.std()*np.sqrt(252)}

def backtest(ret,lookback,rebalance,top_n,cost_mult=1.0):
    # Score at T close using returns through T; new weights affect T+1 return.
    score=ret.rolling(lookback).mean()/ret.rolling(lookback).std().replace(0,np.nan)
    w=pd.DataFrame(0.0,index=ret.index,columns=ret.columns)
    target=pd.Series(0.0,index=ret.columns)
    for i,dt in enumerate(ret.index):
        w.loc[dt]=target
        if i % rebalance==0:
            s=score.loc[dt].dropna().sort_values(ascending=False)
            picks=list(s.head(top_n).index)
            target=pd.Series(0.0,index=ret.columns)
            if picks: target.loc[picks]=1/len(picks)
    gross=(w*ret).sum(axis=1)
    delta=w.diff().fillna(w)
    buys=delta.clip(lower=0).sum(axis=1)
    sells=(-delta.clip(upper=0)).sum(axis=1)
    costs=cost_mult*(buys*FEE+sells*(FEE+TAX))
    nav=(1+gross-costs).cumprod()
    return nav,w,costs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--curves",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    c=pd.read_csv(a.curves,parse_dates=["date"])
    piv=c.pivot(index="date",columns="router",values="nav").sort_index()
    ret=piv.pct_change().fillna(0)
    grid=[]; runs=[]
    for lb in (20,60,120):
      for rb in (10,21,42):
       for top in (1,2):
        nav,w,cost=backtest(ret,lb,rb,top)
        mt=metrics(nav,*TRAIN)
        train_score=mt["return"]+.04*mt["sharpe"]+.70*mt["mdd"]
        grid.append([lb,rb,top,train_score,mt["return"],mt["mdd"],mt["sharpe"]])
        runs.append((train_score,lb,rb,top,nav,w,cost))
    g=pd.DataFrame(grid,columns=["lookback","rebalance","top_n","train_score","train_return","train_mdd","train_sharpe"]).sort_values("train_score",ascending=False)
    g.to_csv(out/"dynamic_train_grid.csv",index=False)
    topkeys={(int(r.lookback),int(r.rebalance),int(r.top_n)) for _,r in g.head(5).iterrows()}
    survivors=[]
    for run in runs:
        _,lb,rb,top,nav,w,cost=run
        if (lb,rb,top) not in topkeys: continue
        mv=metrics(nav,*VALID)
        if mv["return"]>-.05 and mv["mdd"]>-.25: survivors.append(run)
    validation_pass=bool(survivors)
    winner=max(survivors or runs,key=lambda x:x[0])
    _,lb,rb,top,nav,w,cost=winner
    rows=[]
    for name,(st,en) in PERIODS.items():
        rows.append({"strategy":"DynamicRouter","period":name,**metrics(nav,st,en)})
    # Frozen equal-weight control; no hindsight selection.
    ew=(1+ret.mean(axis=1)).cumprod()
    for name,(st,en) in PERIODS.items(): rows.append({"strategy":"EqualWeight4","period":name,**metrics(ew,st,en)})
    pd.DataFrame(rows).to_csv(out/"dynamic_summary.csv",index=False)
    sensitivity=[]
    for mult in (0.0,1.0,2.0,3.0):
        snav,_,_=backtest(ret,lb,rb,top,cost_mult=mult)
        for name,(st,en) in PERIODS.items():
            sensitivity.append({"cost_multiple":mult,"period":name,**metrics(snav,st,en)})
    pd.DataFrame(sensitivity).to_csv(out/"dynamic_cost_sensitivity.csv",index=False)
    pd.DataFrame({"date":nav.index,"dynamic_nav":nav.values,"equal_weight_nav":ew.values,"cost":cost.values}).to_csv(out/"dynamic_curves.csv",index=False)
    w.reset_index().to_csv(out/"dynamic_weights.csv",index=False)
    config={"lookback":lb,"rebalance":rb,"top_n":top,"validation_pass":validation_pass,
            "signal_t_execute":"weights apply to T+1 return","costs":{"buy":FEE,"sell":FEE+TAX}}
    (out/"dynamic_config.json").write_text(json.dumps(config,indent=2),encoding="utf-8")
    print(g.head(10).to_string(index=False)); print(pd.DataFrame(rows).round(4).to_string(index=False)); print(config)

if __name__=="__main__": main()
