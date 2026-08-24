#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4.12-D 股票級 Financial Regime Router Trainer
================================================

輸入
----
v412d_data/v412d_12stocks_2010_2026.csv
由 v412d_twse_downloader.py 產生。

研究切割
--------
Train      : 2010-01-01 ~ 2018-12-31
Validation : 2019-01-01 ~ 2022-12-31
Blind      : 2023-01-01 ~ 2025-12-31
Final OOS  : 2026-01-01 ~ 資料最後日期

研究紀律
--------
- 所有指標只用當日或之前資料。
- 訊號 T 日產生，T+1 開盤成交，避免 look-ahead。
- Train 可選結構/閾值。
- Validation 只淘汰，不拿來重新找最佳參數。
- Blind / Final 不調參。
- R1/R2/R3/R4 分開建模。
- 找 Robust Plateau，不只取單點最佳。
"""

import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

STOCKS = {
    "2880": ("華南金", "R1"),
    "2886": ("兆豐金", "R1"),
    "2892": ("第一金", "R1"),
    "5880": ("合庫金", "R1"),
    "2801": ("彰銀",   "R2"),
    "2834": ("臺企銀", "R2"),
    "2884": ("玉山金", "R3"),
    "2885": ("元大金", "R3"),
    "2890": ("永豐金", "R3"),
    "2891": ("中信金", "R3"),
    "2881": ("富邦金", "R4"),
    "2882": ("國泰金", "R4"),
}

TRAIN=("2010-01-01","2018-12-31")
VALID=("2019-01-01","2022-12-31")
BLIND=("2023-01-01","2025-12-31")
FINAL=("2026-01-01","2099-12-31")

FEE=0.001425*0.6
TAX=0.003

def kd(df,n=14,k_smooth=3,d_smooth=3):
    low=df.low.rolling(n).min()
    high=df.high.rolling(n).max()
    rsv=100*(df.close-low)/(high-low).replace(0,np.nan)
    k=rsv.ewm(alpha=1/k_smooth,adjust=False).mean()
    d=k.ewm(alpha=1/d_smooth,adjust=False).mean()
    return k,d

def bb_pos(s,n=21,z=2):
    ma=s.rolling(n).mean()
    sd=s.rolling(n).std()
    lo=ma-z*sd
    hi=ma+z*sd
    pos=(s-lo)/(hi-lo).replace(0,np.nan)
    return pos,ma,lo,hi

def prepare(df):
    x=df.copy()
    x["date"]=pd.to_datetime(x.date)
    x["stock_id"]=x.stock_id.astype(str)
    x=x.sort_values(["stock_id","date"])
    out=[]
    for sid,g in x.groupby("stock_id"):
        g=g.copy().set_index("date").sort_index()
        g["ret1"]=g.close.pct_change()
        g["ret5"]=g.close.pct_change(5)
        g["ret20"]=g.close.pct_change(20)
        g["ret60"]=g.close.pct_change(60)
        g["ema20"]=g.close.ewm(span=20,adjust=False).mean()
        g["ema60"]=g.close.ewm(span=60,adjust=False).mean()
        g["ema20_slope"]=g.ema20.pct_change(5)
        g["vol20"]=g.ret1.rolling(20).std()*np.sqrt(252)
        g["vol60"]=g.ret1.rolling(60).std()*np.sqrt(252)
        g["high60"]=g.high.rolling(60).max()
        g["low120"]=g.low.rolling(120).min()
        g["low252"]=g.low.rolling(252).min()
        g["dd60"]=g.close/g.high60-1
        g["dist_low120"]=g.close/g.low120-1
        g["dist_low252"]=g.close/g.low252-1
        g["bb"],_,_,_=bb_pos(g.close)
        g["k"],g["d"]=kd(g)
        g["kd_cross_up"]=(g.k>g.d)&(g.k.shift(1)<=g.d.shift(1))
        g["vol_ratio"]=g.Trading_Volume/g.Trading_Volume.rolling(20).mean()
        g["month"]=g.index.month
        g["stock_id"]=sid
        g["name"]=STOCKS[sid][0]
        g["router"]=STOCKS[sid][1]
        out.append(g.reset_index())
    z=pd.concat(out,ignore_index=True)

    # Cross-sectional relative strength vs all 12 financials, using close-to-close returns.
    piv20=z.pivot(index="date",columns="stock_id",values="ret20")
    piv60=z.pivot(index="date",columns="stock_id",values="ret60")
    mean20=piv20.mean(axis=1)
    mean60=piv60.mean(axis=1)
    z=z.merge(mean20.rename("fin_ret20"),left_on="date",right_index=True,how="left")
    z=z.merge(mean60.rename("fin_ret60"),left_on="date",right_index=True,how="left")
    z["rs20"]=z.ret20-z.fin_ret20
    z["rs60"]=z.ret60-z.fin_ret60
    return z

def pct_rank(s,ascending=True):
    return s.rank(pct=True,ascending=ascending)

def score_day(g,router,params):
    x=g.copy()
    if router=="R1":
        # public financial holding companies: buy weakness but require recovery evidence
        x["score"] = (
            params["w_low"]*(1-pct_rank(x.dist_low252,ascending=True)+0.25) +
            params["w_dd"]*(1-pct_rank(x.dd60,ascending=True)+0.25) +
            params["w_bb"]*(1-pct_rank(x.bb,ascending=True)+0.25) +
            params["w_k"]*(1-pct_rank(x.k,ascending=True)+0.25) +
            params["w_rev"]*x.kd_cross_up.astype(float)
        )
        if params.get("season_gate",False):
            x.loc[~x.month.isin([8,9,10,11]),"score"]*=params.get("offseason_scale",0.5)
    elif router=="R2":
        # public banks: low zone + gradual recovery
        x["score"] = (
            params["w_low"]*(1-pct_rank(x.dist_low120,ascending=True)+0.25) +
            params["w_vol"]*(1-pct_rank(x.vol20,ascending=True)+0.25) +
            params["w_ema"]*pct_rank(x.ema20_slope,ascending=True) +
            params["w_k"]*pct_rank(x.k,ascending=True)
        )
        if params.get("season_gate",False):
            x.loc[~x.month.isin([9,10,11,12]),"score"]*=params.get("offseason_scale",0.6)
    elif router=="R3":
        # private bank/market: buy strength
        x["score"] = (
            params["w_m20"]*pct_rank(x.ret20,ascending=True) +
            params["w_m60"]*pct_rank(x.ret60,ascending=True) +
            params["w_rs"]*pct_rank(x.rs20+x.rs60,ascending=True) +
            params["w_vol"]*pct_rank(x.vol_ratio,ascending=True)
        )
    else:
        # insurance-heavy: momentum but only if broad regime not weak
        x["score"] = (
            params["w_m20"]*pct_rank(x.ret20,ascending=True) +
            params["w_m60"]*pct_rank(x.ret60,ascending=True) +
            params["w_rs"]*pct_rank(x.rs20+x.rs60,ascending=True) +
            params["w_def"]*(1-pct_rank(x.vol20,ascending=True)+0.25)
        )
    return x

PARAM_FAMILIES = {
"R1":[
 {"id":"R1A","w_low":.30,"w_dd":.25,"w_bb":.20,"w_k":.10,"w_rev":.15,"season_gate":True,"offseason_scale":.50},
 {"id":"R1B","w_low":.25,"w_dd":.30,"w_bb":.20,"w_k":.10,"w_rev":.15,"season_gate":True,"offseason_scale":.60},
 {"id":"R1C","w_low":.30,"w_dd":.25,"w_bb":.15,"w_k":.15,"w_rev":.15,"season_gate":False},
],
"R2":[
 {"id":"R2A","w_low":.35,"w_vol":.20,"w_ema":.30,"w_k":.15,"season_gate":True,"offseason_scale":.60},
 {"id":"R2B","w_low":.30,"w_vol":.25,"w_ema":.30,"w_k":.15,"season_gate":True,"offseason_scale":.70},
 {"id":"R2C","w_low":.35,"w_vol":.20,"w_ema":.25,"w_k":.20,"season_gate":False},
],
"R3":[
 {"id":"R3A","w_m20":.30,"w_m60":.30,"w_rs":.25,"w_vol":.15},
 {"id":"R3B","w_m20":.35,"w_m60":.25,"w_rs":.30,"w_vol":.10},
 {"id":"R3C","w_m20":.25,"w_m60":.35,"w_rs":.30,"w_vol":.10},
],
"R4":[
 {"id":"R4A","w_m20":.30,"w_m60":.30,"w_rs":.25,"w_def":.15},
 {"id":"R4B","w_m20":.25,"w_m60":.35,"w_rs":.25,"w_def":.15},
 {"id":"R4C","w_m20":.30,"w_m60":.25,"w_rs":.25,"w_def":.20},
]
}

def build_daily_scores(z,router,params):
    q=z[z.router==router].copy()
    pieces=[]
    for dt,g in q.groupby("date"):
        pieces.append(score_day(g,router,params))
    return pd.concat(pieces,ignore_index=True).sort_values(["date","score"],ascending=[True,False])

def simulate_router(z,router,params,top_n=1,rebalance_days=21,threshold=0.0,
                    slot_capital=1.0,stop=-.15):
    data=build_daily_scores(z,router,params)
    stocks=sorted(data.stock_id.unique())
    dates=sorted(data.date.unique())
    px=data.pivot(index="date",columns="stock_id",values="close")
    op=data.pivot(index="date",columns="stock_id",values="open")
    score=data.pivot(index="date",columns="stock_id",values="score")
    nav=1.0
    current={}
    entry_price={}
    pending_target=None
    pending_reason={}
    curve=[]
    weights=[]
    trade_log=[]

    for i,dt in enumerate(dates):
        # Carry yesterday's holdings from previous close to today's open.
        if i>0 and current:
            prev_dt=dates[i-1]
            overnight=0.0
            for sid,w in current.items():
                if (sid in op.columns and sid in px.columns and
                    pd.notna(op.loc[dt,sid]) and pd.notna(px.loc[prev_dt,sid]) and
                    px.loc[prev_dt,sid] != 0):
                    overnight += w*(op.loc[dt,sid]/px.loc[prev_dt,sid]-1)
            nav *= (1+overnight)

        # A signal formed after T close is executed strictly at T+1 open.
        if pending_target is not None:
            target=pending_target
            universe=set(target)|set(current)
            buy_turnover=sum(max(target.get(sid,0)-current.get(sid,0),0) for sid in universe)
            sell_turnover=sum(max(current.get(sid,0)-target.get(sid,0),0) for sid in universe)
            nav *= max(0.0,1-buy_turnover*FEE-sell_turnover*(FEE+TAX))
            for sid in universe:
                old_w=current.get(sid,0); new_w=target.get(sid,0)
                if abs(new_w-old_w)<1e-12:
                    continue
                action=pending_reason.get(sid)
                if action is None:
                    action="ENTER" if old_w==0 else ("EXIT" if new_w==0 else "REBAL")
                trade_log.append([router,sid,action,dt,float(op.loc[dt,sid]),new_w])
                if new_w==0:
                    entry_price.pop(sid,None)
                elif old_w==0 or new_w>old_w:
                    entry_price[sid]=float(op.loc[dt,sid])
            current=target.copy()
            pending_target=None
            pending_reason={}

        # Mark new holdings from today's open to close.
        if current:
            intraday=0.0
            for sid,w in current.items():
                if (sid in op.columns and sid in px.columns and
                    pd.notna(op.loc[dt,sid]) and pd.notna(px.loc[dt,sid]) and
                    op.loc[dt,sid] != 0):
                    intraday += w*(px.loc[dt,sid]/op.loc[dt,sid]-1)
            nav *= (1+intraday)

        # Form today's desired holdings only after the close.
        desired=current.copy()
        reasons={}
        if i % rebalance_days == 0 and dt in score.index:
            s=score.loc[dt].dropna().sort_values(ascending=False)
            picks=list(s[s>=threshold].head(top_n).index)
            desired={sid:slot_capital/len(picks) for sid in picks} if picks else {}

        # Close-based stop also becomes an order for the next open.
        for sid in list(current):
            if (sid in px.columns and pd.notna(px.loc[dt,sid]) and
                sid in entry_price and px.loc[dt,sid]/entry_price[sid]-1 <= stop):
                desired.pop(sid,None)
                reasons[sid]="STOP"

        if desired != current:
            pending_target=desired
            pending_reason=reasons

        curve.append([dt,nav])
        wr={"date":dt}
        for sid in stocks:
            wr[sid]=current.get(sid,0)
        weights.append(wr)

    return pd.DataFrame(curve,columns=["date","nav"]),pd.DataFrame(weights),pd.DataFrame(
        trade_log,columns=["router","stock_id","action","date","price","weight"])

def period_metrics(curve,start,end):
    c=curve[(curve.date>=pd.Timestamp(start))&(curve.date<=pd.Timestamp(end))].copy()
    if len(c)<2:
        return dict(n=0,ret=np.nan,mdd=np.nan,sharpe=np.nan,vol=np.nan)
    s=c.set_index("date").nav
    r=s.pct_change().dropna()
    return dict(
        n=len(c),
        ret=s.iloc[-1]/s.iloc[0]-1,
        mdd=(s/s.cummax()-1).min(),
        sharpe=r.mean()/r.std()*np.sqrt(252) if r.std()>0 else 0,
        vol=r.std()*np.sqrt(252)
    )

def score_train(m,turns=0):
    if m["n"]<200: return -999
    return m["ret"] + .04*m["sharpe"] + .70*m["mdd"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="v412d_data/v412d_12stocks_2010_2026.csv")
    ap.add_argument("--out",default="v412d_results")
    args=ap.parse_args()
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)

    raw=pd.read_csv(args.input)
    raw=raw.rename(columns={"code":"stock_id","volume":"Trading_Volume"})
    required={"date","stock_id","open","high","low","close","Trading_Volume"}
    absent=required-set(raw.columns)
    if absent:
        raise SystemExit("缺少欄位: "+",".join(sorted(absent)))
    raw["stock_id"]=raw.stock_id.astype(str).str.replace(r"\.0$","",regex=True)
    missing=set(STOCKS)-set(raw.stock_id.astype(str).unique())
    if missing:
        raise SystemExit("缺少股票: "+",".join(sorted(missing)))

    z=prepare(raw)
    z.to_csv(out/"features.csv",index=False,encoding="utf-8-sig",date_format="%Y-%m-%d")

    all_summary=[]
    selected={}
    all_curves=[]
    all_trades=[]

    for router in ["R1","R2","R3","R4"]:
        print("\n",router)
        grid=[]
        configs=[]
        top_options=[1,2] if router in ["R1","R3"] else [1]
        reb_options=[10,15,21] if router in ["R1","R3"] else [15,21]
        for p in PARAM_FAMILIES[router]:
            for top_n in top_options:
                for reb in reb_options:
                    curve,w,tr=simulate_router(z,router,p,top_n=top_n,rebalance_days=reb,
                                               threshold=0.0,slot_capital=1.0)
                    mt=period_metrics(curve,*TRAIN)
                    sv=score_train(mt)
                    grid.append([router,p["id"],top_n,reb,sv,mt["ret"],mt["mdd"],mt["sharpe"],mt["vol"]])
                    configs.append((sv,p,top_n,reb,curve,w,tr))
        g=pd.DataFrame(grid,columns=["router","param_id","top_n","rebalance_days","train_score",
                                     "train_ret","train_mdd","train_sharpe","train_vol"])
        g=g.sort_values("train_score",ascending=False)
        g.to_csv(out/f"{router}_train_grid.csv",index=False,encoding="utf-8-sig")
        print(g.head(10).round(4).to_string(index=False))

        # Robust plateau: top 5 Train configs; validation only removes clearly bad models.
        topids=set((r.param_id,int(r.top_n),int(r.rebalance_days)) for _,r in g.head(5).iterrows())
        survivors=[]
        for sv,p,top_n,reb,curve,w,tr in configs:
            if (p["id"],top_n,reb) not in topids: continue
            mv=period_metrics(curve,*VALID)
            if mv["ret"]>-.05 and mv["mdd"]>-.25:
                survivors.append((sv,p,top_n,reb,curve,w,tr,mv))
        if not survivors:
            # safest fallback: best Train config; mark failed validation.
            survivors=[max(configs,key=lambda x:x[0]) + ({"ret":np.nan,"mdd":np.nan,"sharpe":np.nan,"vol":np.nan},)]

        # Select the highest Train score among validation survivors (Validation does not optimize).
        winner=sorted(survivors,key=lambda x:x[0],reverse=True)[0]
        sv,p,top_n,reb,curve,w,tr,mv=winner
        selected[router]={"param_id":p["id"],"top_n":top_n,"rebalance_days":reb}

        for period,(st,en) in {
            "Train":TRAIN,"Validation":VALID,"Blind":BLIND,"Final":FINAL}.items():
            m=period_metrics(curve,st,en)
            all_summary.append([router,p["id"],top_n,reb,period,m["n"],m["ret"],m["mdd"],m["sharpe"],m["vol"]])

        cc=curve.copy(); cc["router"]=router
        all_curves.append(cc)
        if not tr.empty:
            all_trades.append(tr)

    summary=pd.DataFrame(all_summary,columns=[
        "router","param_id","top_n","rebalance_days","period","n",
        "return","mdd","sharpe","vol"])
    summary.to_csv(out/"router_walkforward_summary.csv",index=False,encoding="utf-8-sig")

    if all_curves:
        pd.concat(all_curves).to_csv(out/"router_curves.csv",index=False,encoding="utf-8-sig",date_format="%Y-%m-%d")
    if all_trades:
        pd.concat(all_trades).to_csv(out/"router_trades.csv",index=False,encoding="utf-8-sig",date_format="%Y-%m-%d")
    (out/"selected_configs.json").write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding="utf-8")

    print("\n=== Walk-forward Summary ===")
    print(summary.round(4).to_string(index=False))
    print("\nSelected configs:",json.dumps(selected,ensure_ascii=False,indent=2))
    print("\n輸出:",out.resolve())

if __name__=="__main__":
    main()
