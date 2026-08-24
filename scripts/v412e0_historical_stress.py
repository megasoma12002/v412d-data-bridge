#!/usr/bin/env python3
"""Evaluate the frozen V4.12-D model on expanded history; no parameter selection."""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
import v412d_formal_router as model

WINDOWS={"PreModel_2005_2007":("2005-03-01","2007-12-31"),"GFC_2008_2009":("2008-01-01","2009-12-31"),
         "2010_2014":("2010-01-01","2014-12-31"),"2015_2017":("2015-01-01","2017-12-31"),
         "2018_2020":("2018-01-01","2020-12-31"),"2021_2022":("2021-01-01","2022-12-31"),
         "Revealed_2023_2025":("2023-01-01","2025-12-31"),"Final_2026":("2026-01-01","2099-12-31")}

def met(nav,st,en):
    s=nav.loc[st:en].dropna();r=s.pct_change().dropna()
    return {"n":len(s),"ret":s.iloc[-1]/s.iloc[0]-1 if len(s)>1 else np.nan,"mdd":(s/s.cummax()-1).min() if len(s)>1 else np.nan,"sharpe":r.mean()/r.std()*np.sqrt(252) if len(r) and r.std()>0 else np.nan}

def main():
    p=argparse.ArgumentParser();p.add_argument("--raw",required=True);p.add_argument("--adjusted",required=True);p.add_argument("--out",required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw);z=model.prep(raw);scores=model.make_scores(z,1)
    raw_nav,w,state,cost=model.simulate(z,1,21,2,75,1,scores=scores)
    adj=pd.read_csv(a.adjusted,parse_dates=["date"]);adj.code=adj.code.astype(str)
    ac=adj.pivot(index="date",columns="code",values="adjusted_close").reindex(w.index);ao=adj.pivot(index="date",columns="code",values="adjusted_open").reindex(w.index)
    ww=w.reindex(columns=ac.columns).fillna(0);prev=ww.shift(1).fillna(0)
    adjret=(prev*(ao/ac.shift(1)-1).fillna(0)).sum(axis=1)+(ww*(ac/ao-1).fillna(0)).sum(axis=1)-cost
    adj_nav=(1+adjret).cumprod();bench=(1+ac.pct_change(fill_method=None).mean(axis=1).fillna(0)).cumprod()
    rows=[]
    for name,(st,en) in WINDOWS.items():
        for label,nav in (("FormalRouter_adjusted",adj_nav),("EqualWeight12_adjusted",bench),("FormalRouter_raw",raw_nav)):
            rows.append({"window":name,"strategy":label,**met(nav,st,en)})
    pd.DataFrame(rows).to_csv(out/"historical_stress_summary.csv",index=False);pd.DataFrame({"date":adj_nav.index,"formal_adjusted":adj_nav,"benchmark_adjusted":bench,"formal_raw":raw_nav}).to_csv(out/"historical_stress_curves.csv",index=False)
    status={"model":"frozen family1/top2/21D/75D","selection":"none; historical stress only","first_date":str(adj_nav.index.min().date()),"last_date":str(adj_nav.index.max().date())}
    (out/"historical_stress_status.json").write_text(json.dumps(status,indent=2));print(pd.DataFrame(rows).round(4).to_string(index=False));print(status)
if __name__=="__main__":main()
