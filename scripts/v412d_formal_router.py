#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

TRAIN=("2010-01-01","2018-12-31"); VALID=("2019-01-01","2022-12-31")
BLIND=("2023-01-01","2025-12-31"); FINAL=("2026-01-01","2099-12-31")
PERIODS={"Train":TRAIN,"Validation":VALID,"Blind":BLIND,"Final":FINAL}
GROUPS={"R1":["2880","2886","2892","5880"],"R2":["2801","2834"],
        "R3":["2884","2885","2890","2891"],"R4":["2881","2882"]}
FEE=.001425*.6; TAX=.003

def prep(raw):
    x=raw.rename(columns={"code":"stock_id","volume":"Trading_Volume"}).copy()
    x.stock_id=x.stock_id.astype(str).str.replace(r"\.0$","",regex=True); x.date=pd.to_datetime(x.date)
    out=[]
    for sid,g in x.sort_values("date").groupby("stock_id"):
        g=g.set_index("date").sort_index().copy(); r=g.close.pct_change()
        g["ret20"]=g.close.pct_change(20); g["ret60"]=g.close.pct_change(60)
        g["ema20"]=g.close.ewm(span=20,adjust=False).mean(); g["ema60"]=g.close.ewm(span=60,adjust=False).mean()
        g["ema20s"]=g.ema20.pct_change(5); g["vol20"]=r.rolling(20).std()*np.sqrt(252)
        g["high60"]=g.high.rolling(60).max(); g["low120"]=g.low.rolling(120).min(); g["low252"]=g.low.rolling(252).min()
        g["dd60"]=g.close/g.high60-1; g["low120d"]=g.close/g.low120-1; g["low252d"]=g.close/g.low252-1
        ma=g.close.rolling(21).mean(); sd=g.close.rolling(21).std(); g["bb"]=(g.close-(ma-2*sd))/(4*sd).replace(0,np.nan)
        lo=g.low.rolling(14).min(); hi=g.high.rolling(14).max(); rsv=100*(g.close-lo)/(hi-lo).replace(0,np.nan)
        g["k"]=rsv.ewm(alpha=1/3,adjust=False).mean(); g["d"]=g.k.ewm(alpha=1/3,adjust=False).mean()
        g["kup"]=(g.k>g.d)&(g.k.shift(1)<=g.d.shift(1)); g["volratio"]=g.Trading_Volume/g.Trading_Volume.rolling(20).mean()
        g["stock_id"]=sid; out.append(g.reset_index())
    z=pd.concat(out,ignore_index=True)
    p20=z.pivot(index="date",columns="stock_id",values="ret20"); p60=z.pivot(index="date",columns="stock_id",values="ret60")
    z=z.merge(p20.mean(axis=1).rename("fin20"),left_on="date",right_index=True).merge(p60.mean(axis=1).rename("fin60"),left_on="date",right_index=True)
    z["rs"]=z.ret20+z.ret60-z.fin20-z.fin60
    for rtr,sids in GROUPS.items(): z.loc[z.stock_id.isin(sids),"router"]=rtr
    return z

def rank(s,asc=True): return s.rank(pct=True,ascending=asc)

def stock_score(g,rtr,fam):
    x=g.copy()
    if rtr=="R1":
        x["score"]=.30*(1-rank(x.low252d))+.25*(1-rank(x.dd60))+.20*(1-rank(x.bb))+.10*(1-rank(x.k))+.15*x.kup
        season=x.date.dt.month.isin([8,9,10,11]); x.loc[~season,"score"]*=.5 if fam<2 else .7
        gate=(x.dd60<(-.04 if fam==0 else -.02))|(x.bb<(.30 if fam==0 else .45))
    elif rtr=="R2":
        x["score"]=.35*(1-rank(x.low120d))+.20*(1-rank(x.vol20))+.30*rank(x.ema20s)+.15*rank(x.k)
        gate=(x.ema20s>(0 if fam==0 else -.005))&(x.k>(25 if fam==0 else 15))
    elif rtr=="R3":
        x["score"]=.30*rank(x.ret20)+.30*rank(x.ret60)+.30*rank(x.rs)+.10*rank(x.volratio)
        gate=(x.ret20>(0 if fam==0 else -.02))&(x.close>x.ema60*(1 if fam==0 else .98))
    else:
        x["score"]=.30*rank(x.ret20)+.30*rank(x.ret60)+.25*rank(x.rs)+.15*(1-rank(x.vol20))
        broad=(x.fin20>(0 if fam==0 else -.02))&(x.fin60>(-.02 if fam==0 else -.05))
        gate=broader= broad & (x.close>x.ema60*(1 if fam==0 else .97))
    x["eligible"]=gate.fillna(False); return x

def make_scores(z,fam):
    allx=[]
    for (dt,rtr),g in z.groupby(["date","router"]): allx.append(stock_score(g,rtr,fam))
    return pd.concat(allx,ignore_index=True)

def targets(scores,dates,reb,top_n,lock_days,core=.8,tilt=.2):
    stocks=sorted(scores.stock_id.unique()); cur={}; entry_i={}; rows=[]; state=[]
    bydate={d:g for d,g in scores.groupby("date")}; last_month=None
    tilt_router={r:0 for r in GROUPS}
    for i,dt in enumerate(dates):
        # monthly low-frequency upper router, based only on data at today's close
        month=(dt.year,dt.month)
        if month!=last_month:
            g=bydate[dt]; agg=g.groupby("router").agg(m20=("ret20","mean"),m60=("ret60","mean"),vol=("vol20","mean"),dd=("dd60","mean"))
            q=.35*rank(agg.m20)+.35*rank(agg.m60)+.15*(1-rank(agg.vol))+.15*rank(agg.dd)
            active=[r for r in GROUPS if bool(g[(g.router==r)&g.eligible].shape[0])]
            pos=q.loc[active].clip(lower=0) if active else pd.Series(dtype=float)
            tilt_router={r:0 for r in GROUPS}
            if len(pos) and pos.sum()>0:
                for r,v in (pos/pos.sum()*tilt).items(): tilt_router[r]=v
            last_month=month
        if i%reb==0:
            g=bydate[dt]; new={}
            for rtr,sids in GROUPS.items():
                # C2 rule: the 80% Core never exits on a short-term gate.
                # R0 cash applies only to the 20% Tilt when no eligible Edge exists.
                cand=g[g.router==rtr].sort_values("score",ascending=False)
                # V4.6c Capital-Lock: expiring names cannot be renewed at this rebalance.
                keep=cand.stock_id.map(lambda s: not (s in entry_i and i-entry_i[s]>=lock_days)).astype(bool)
                cand=cand.loc[keep]
                picks=list(cand.head(top_n).stock_id)
                if picks:
                    for sid in picks: new[sid]=new.get(sid,0)+(core/4)/len(picks)
                tilt_cand=cand[cand.eligible]
                tilt_picks=list(tilt_cand.head(top_n).stock_id)
                extra=tilt_router.get(rtr,0)
                if tilt_picks and extra>0:
                    for sid in tilt_picks: new[sid]=new.get(sid,0)+extra/len(tilt_picks)
            for sid in new:
                if sid not in cur: entry_i[sid]=i
            for sid in set(cur)-set(new): entry_i.pop(sid,None)
            cur=new
        row={"date":dt,**{s:cur.get(s,0) for s in stocks}}; rows.append(row)
        state.append({"date":dt,"cash":1-sum(cur.values()),**{r:sum(cur.get(s,0) for s in ids) for r,ids in GROUPS.items()}})
    return pd.DataFrame(rows).set_index("date"),pd.DataFrame(state)

def simulate(z,fam,reb,top_n,lock_days,cost_mult=1,scores=None):
    close=z.pivot(index="date",columns="stock_id",values="close").sort_index(); op=z.pivot(index="date",columns="stock_id",values="open").reindex(close.index)
    scores=make_scores(z,fam) if scores is None else scores
    signal_w,state=targets(scores,list(close.index),reb,top_n,lock_days)
    # target formed at T close applies at T+1 open
    w=signal_w.shift(1).fillna(0); prev=w.shift(1).fillna(0)
    overnight=(prev*(op/close.shift(1)-1).fillna(0)).sum(axis=1)
    intraday=(w*(close/op-1).fillna(0)).sum(axis=1)
    d=w-prev; cost=cost_mult*(d.clip(lower=0).sum(axis=1)*FEE+(-d.clip(upper=0)).sum(axis=1)*(FEE+TAX))
    nav=(1+overnight+intraday-cost).cumprod()
    return nav,w,state,cost

def metrics(nav,p):
    s=nav.loc[p[0]:p[1]]
    if len(s)<2:return dict(n=len(s),ret=np.nan,mdd=np.nan,sharpe=np.nan,vol=np.nan)
    r=s.pct_change().dropna(); return dict(n=len(s),ret=s.iloc[-1]/s.iloc[0]-1,mdd=(s/s.cummax()-1).min(),sharpe=r.mean()/r.std()*np.sqrt(252) if r.std()>0 else 0,vol=r.std()*np.sqrt(252))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); z=prep(pd.read_csv(a.input))
    close=z.pivot(index="date",columns="stock_id",values="close").sort_index(); bench=(1+close.pct_change().mean(axis=1).fillna(0)).cumprod()
    score_cache={fam:make_scores(z,fam) for fam in (0,1,2)}
    grid=[]; runs=[]
    for fam in (0,1,2):
      for reb in (15,21):
       for top in (1,2):
        for lock in (60,75,90):
         nav,w,state,cost=simulate(z,fam,reb,top,lock,scores=score_cache[fam]); m=metrics(nav,TRAIN)
         score=m["ret"]+.08*m["sharpe"]+.70*m["mdd"]
         grid.append([fam,reb,top,lock,score,m["ret"],m["mdd"],m["sharpe"],m["vol"]]); runs.append((score,fam,reb,top,lock,nav,w,state,cost))
    g=pd.DataFrame(grid,columns="family rebalance top_n lock_days train_score train_ret train_mdd train_sharpe train_vol".split()).sort_values("train_score",ascending=False)
    g.to_csv(out/"train_grid.csv",index=False)
    # robust plateau: top 10 Train, require a neighbor in rebalance/lock space
    top10=g.head(10); keys={(int(r.family),int(r.rebalance),int(r.top_n),int(r.lock_days)) for _,r in top10.iterrows()}
    plateau=[]
    for run in runs:
        _,f,rb,t,l,*_=run
        if (f,rb,t,l) not in keys: continue
        neigh=sum((f,rr,t,ll) in keys for rr in (15,21) for ll in (60,75,90))-1
        if neigh>=1: plateau.append(run)
    candidates=plateau or sorted(runs,reverse=True)[:5]
    valrows=[]; survivors=[]; bm=metrics(bench,VALID)
    for run in candidates:
        score,f,rb,t,l,nav,*_=run; m=metrics(nav,VALID)
        # fixed hard gate: positive, controlled DD, positive Sharpe, and better risk-adjusted result than 12-stock EW.
        passed=m["ret"]>0 and m["mdd"]>-.25 and m["sharpe"]>0 and m["sharpe"]>=bm["sharpe"]
        valrows.append([f,rb,t,l,m["ret"],m["mdd"],m["sharpe"],bm["ret"],bm["mdd"],bm["sharpe"],passed])
        if passed: survivors.append(run)
    v=pd.DataFrame(valrows,columns="family rebalance top_n lock_days val_ret val_mdd val_sharpe benchmark_ret benchmark_mdd benchmark_sharpe passed".split())
    v.to_csv(out/"validation_gate.csv",index=False)
    if not survivors:
        (out/"status.json").write_text(json.dumps({"validation_pass":False,"reason":"No Train-selected robust-plateau candidate passed the frozen Validation gate"},indent=2))
        print(g.head(10).to_string(index=False)); print(v.to_string(index=False)); print("VALIDATION_GATE_FAILED"); return
    winner=max(survivors,key=lambda x:x[0]); _,f,rb,t,l,nav,w,state,cost=winner
    rows=[]
    for name,p in PERIODS.items(): rows.append({"strategy":"FormalRouter","period":name,**metrics(nav,p)}); rows.append({"strategy":"EqualWeight12","period":name,**metrics(bench,p)})
    pd.DataFrame(rows).to_csv(out/"walkforward_summary.csv",index=False); pd.DataFrame({"date":nav.index,"nav":nav.values,"benchmark":bench.values,"cost":cost.values}).to_csv(out/"curves.csv",index=False)
    w.reset_index().to_csv(out/"weights.csv",index=False); state.to_csv(out/"router_states.csv",index=False)
    sens=[]
    for cm in (0,1,2,3):
        snav,*_=simulate(z,f,rb,t,l,cm,scores=score_cache[f])
        for name,p in PERIODS.items(): sens.append({"cost_multiple":cm,"period":name,**metrics(snav,p)})
    pd.DataFrame(sens).to_csv(out/"cost_sensitivity.csv",index=False)
    cfg={"validation_pass":True,"family":f,"rebalance":rb,"top_n":t,"lock_days":l,"architecture":"80% core + 20% monthly tilt; R0 cash; intra-router daily features; T+1 open"}
    (out/"status.json").write_text(json.dumps(cfg,indent=2)); print(g.head(10).to_string(index=False)); print(v.to_string(index=False)); print(pd.DataFrame(rows).round(4).to_string(index=False)); print(cfg)

if __name__=="__main__": main()
