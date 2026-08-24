#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

import v412d_formal_router as d

TRAIN = ("2005-03-01", "2011-12-30")
VALID = ("2012-01-01", "2014-12-31")
OOS = {
    "Train": TRAIN, "Validation": VALID,
    "OOS_2015_2017": ("2015-01-01", "2017-12-31"),
    "OOS_2018_2020": ("2018-01-01", "2020-12-31"),
    "OOS_2021_2022": ("2021-01-01", "2022-12-31"),
    "Blind_2023_2025": ("2023-01-01", "2025-12-31"),
    "Final_2026": ("2026-01-01", "2026-12-31"),
}


def metrics(nav, period):
    s = nav.loc[period[0]:period[1]].dropna()
    if len(s) < 2:
        return {"n": len(s), "ret": np.nan, "mdd": np.nan, "sharpe": np.nan, "vol": np.nan}
    r = s.pct_change().dropna()
    return {"n": len(s), "ret": s.iloc[-1]/s.iloc[0]-1,
            "mdd": (s/s.cummax()-1).min(),
            "sharpe": r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else 0,
            "vol": r.std()*np.sqrt(252)}


def risk_state(z, dd_cut, vol_cut, breadth_cut):
    close = z.pivot(index="date", columns="stock_id", values="close").sort_index()
    ret = close.pct_change(fill_method=None)
    ew = (1 + ret.mean(axis=1, skipna=True).fillna(0)).cumprod()
    dd120 = ew / ew.rolling(120, min_periods=60).max() - 1
    vol20 = ret.mean(axis=1, skipna=True).rolling(20).std() * np.sqrt(252)
    breadth = (close > close.ewm(span=60, adjust=False).mean()).mean(axis=1)
    votes = (dd120 <= dd_cut).astype(int) + (vol20 >= vol_cut).astype(int) + (breadth <= breadth_cut).astype(int)
    raw = votes >= 2
    # Two-day confirmation; five clear days to restore exposure. Uses information through T only.
    state, on_count, off_count = False, 0, 0
    smooth = []
    for flag in raw.fillna(False):
        if flag:
            on_count += 1; off_count = 0
            if on_count >= 2: state = True
        else:
            off_count += 1; on_count = 0
            if off_count >= 5: state = False
        smooth.append(state)
    return pd.DataFrame({"ew_raw_index": ew, "dd120": dd120, "vol20": vol20,
                         "breadth60": breadth, "votes": votes, "crisis": smooth}, index=close.index)


def buffered_targets(scores, dates, rank_buffer, score_gap, min_hold, lock_days=75,
                     rebalance=21, top_n=2, core=.8, tilt=.2):
    stocks = sorted(scores.stock_id.unique())
    bydate = {x: g for x, g in scores.groupby("date")}
    cur, entry_i, rows = {}, {}, []
    tilt_router = {r: 0 for r in d.GROUPS}; last_month = None
    for i, dt in enumerate(dates):
        g = bydate[dt]
        month = (dt.year, dt.month)
        if month != last_month:
            agg = g.groupby("router").agg(m20=("ret20","mean"), m60=("ret60","mean"),
                                            vol=("vol20","mean"), dd=("dd60","mean"))
            q = .35*d.rank(agg.m20)+.35*d.rank(agg.m60)+.15*(1-d.rank(agg.vol))+.15*d.rank(agg.dd)
            active = [r for r in d.GROUPS if len(g[(g.router == r) & g.eligible])]
            pos = q.loc[active].clip(lower=0) if active else pd.Series(dtype=float)
            tilt_router = {r: 0 for r in d.GROUPS}
            if len(pos) and pos.sum() > 0:
                tilt_router.update((pos/pos.sum()*tilt).to_dict())
            last_month = month
        if i % rebalance == 0:
            new = {}
            for router in d.GROUPS:
                cand = g[g.router == router].sort_values("score", ascending=False).copy()
                cand["rank"] = np.arange(1, len(cand)+1)
                # Capital lock expiry blocks renewal at this rebalance.
                cand = cand[cand.stock_id.map(lambda s: not (s in entry_i and i-entry_i[s] >= lock_days))]
                incumbent = [s for s in cand.stock_id if s in cur]
                held_long_enough = {s: (i-entry_i.get(s, i) >= min_hold) for s in incumbent}
                retained = []
                for _, row in cand.iterrows():
                    s = row.stock_id
                    if s in incumbent and (row["rank"] <= top_n + rank_buffer or not held_long_enough[s]):
                        retained.append(s)
                retained = retained[:top_n]
                for _, row in cand.iterrows():
                    if len(retained) >= top_n: break
                    s = row.stock_id
                    if s in retained: continue
                    replaceable = [x for x in retained if held_long_enough.get(x, True)]
                    if retained and replaceable:
                        worst = min(replaceable, key=lambda x: float(cand.loc[cand.stock_id == x, "score"].iloc[0]))
                        old_score = float(cand.loc[cand.stock_id == worst, "score"].iloc[0])
                        if float(row.score) < old_score + score_gap: continue
                    retained.append(s)
                picks = retained[:top_n]
                if picks:
                    for s in picks: new[s] = new.get(s, 0) + (core/4)/len(picks)
                elig = [s for s in picks if bool(cand.loc[cand.stock_id == s, "eligible"].iloc[0])]
                extra = tilt_router.get(router, 0)
                if elig and extra > 0:
                    for s in elig: new[s] = new.get(s, 0) + extra/len(elig)
            for s in new:
                if s not in cur: entry_i[s] = i
            for s in set(cur)-set(new): entry_i.pop(s, None)
            cur = new
        rows.append({"date": dt, **{s: cur.get(s, 0) for s in stocks}})
    return pd.DataFrame(rows).set_index("date")


def nav_from_weights(raw_close, raw_open, eval_close, eval_open, signal_w, risk, scale, cost_mult=1):
    scaled = signal_w.mul(np.where(risk.crisis, scale, 1.0), axis=0)
    w = scaled.shift(1).fillna(0); prev = w.shift(1).fillna(0)
    overnight = (prev*(eval_open/eval_close.shift(1)-1).replace([np.inf,-np.inf],np.nan).fillna(0)).sum(axis=1)
    intraday = (w*(eval_close/eval_open-1).replace([np.inf,-np.inf],np.nan).fillna(0)).sum(axis=1)
    delta = w-prev
    cost = cost_mult*(delta.clip(lower=0).sum(axis=1)*d.FEE + (-delta.clip(upper=0)).sum(axis=1)*(d.FEE+d.TAX))
    nav = (1+overnight+intraday-cost).cumprod()
    return nav, w, cost, scaled


def aligned_matrices(raw, adjusted):
    def mats(x):
        x=x.copy(); x["date"]=pd.to_datetime(x.date); x["stock_id"]=x.code.astype(str).str.replace(r"\.0$","",regex=True)
        x=x.rename(columns={"adjusted_open":"open","adjusted_close":"close"})
        return (x.pivot(index="date",columns="stock_id",values="close").sort_index(),
                x.pivot(index="date",columns="stock_id",values="open").sort_index())
    rc, ro = mats(raw); ac, ao = mats(adjusted)
    ac=ac.reindex(index=rc.index,columns=rc.columns); ao=ao.reindex(index=rc.index,columns=rc.columns)
    return rc, ro.reindex_like(rc), ac, ao


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--raw",required=True); ap.add_argument("--adjusted",required=True); ap.add_argument("--out",required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw); adjusted=pd.read_csv(a.adjusted); z=d.prep(raw)
    rc,ro,ac,ao=aligned_matrices(raw,adjusted); scores=d.make_scores(z,1)
    # Frozen D baseline, evaluated on the same adjusted layer.
    d_signal,_=d.targets(scores,list(rc.index),21,2,75)
    neutral=pd.DataFrame({"crisis":False},index=rc.index)
    d_nav,d_w,d_cost,_=nav_from_weights(rc,ro,ac,ao,d_signal,neutral,1.0)
    ew_ret=ac.pct_change(fill_method=None).mean(axis=1,skipna=True).fillna(0); ew=(1+ew_ret).cumprod()

    crisis_defs=[(-.12,.25,.40,.25),(-.18,.30,.30,.25),(-.18,.30,.30,.50),(-.25,.35,.25,.50)]
    grid=[]; runs=[]
    for dd_cut,vol_cut,breadth_cut,scale in crisis_defs:
        risk=risk_state(z,dd_cut,vol_cut,breadth_cut)
        for rank_buffer in (0,1):
            for gap in (0,.05,.10):
                for min_hold in (0,21,42):
                    sig=buffered_targets(scores,list(rc.index),rank_buffer,gap,min_hold)
                    nav,w,cost,scaled=nav_from_weights(rc,ro,ac,ao,sig,risk,scale)
                    m=metrics(nav,TRAIN); turnover=float(w.diff().abs().sum(axis=1).loc[TRAIN[0]:TRAIN[1]].sum())
                    crisis_mdd=metrics(nav,("2008-01-01","2009-12-31"))["mdd"]
                    score=m["ret"]+.10*m["sharpe"]+1.00*m["mdd"]-.0005*turnover
                    row={"dd_cut":dd_cut,"vol_cut":vol_cut,"breadth_cut":breadth_cut,"crisis_scale":scale,
                         "rank_buffer":rank_buffer,"score_gap":gap,"min_hold":min_hold,"train_score":score,
                         "train_ret":m["ret"],"train_mdd":m["mdd"],"train_sharpe":m["sharpe"],
                         "train_turnover":turnover,"crisis_2008_09_mdd":crisis_mdd}
                    grid.append(row); runs.append((row,nav,w,cost,risk,scaled))
    g=pd.DataFrame(grid).sort_values("train_score",ascending=False); g.to_csv(out/"e1_train_grid.csv",index=False)
    # Robust plateau: Train top quartile, candidate must have at least two nearby buffer variants.
    top=g.head(max(12,len(g)//4)); keys={(r.dd_cut,r.vol_cut,r.breadth_cut,r.crisis_scale,int(r.rank_buffer),r.score_gap,int(r.min_hold)) for _,r in top.iterrows()}
    candidates=[]
    for run in runs:
        r=run[0]; key=(r["dd_cut"],r["vol_cut"],r["breadth_cut"],r["crisis_scale"],r["rank_buffer"],r["score_gap"],r["min_hold"])
        if key not in keys: continue
        near=sum((r["dd_cut"],r["vol_cut"],r["breadth_cut"],r["crisis_scale"],rb,gp,mh) in keys
                 for rb in (0,1) for gp in (0,.05,.10) for mh in (0,21,42))-1
        if near>=2: candidates.append(run)
    candidates=sorted(candidates,key=lambda x:x[0]["train_score"],reverse=True)[:8]
    base_val=metrics(d_nav,VALID); valrows=[]; survivors=[]
    for run in candidates:
        r,nav,*_=run; m=metrics(nav,VALID)
        passed=(m["ret"]>0 and m["mdd"]>-.25 and m["sharpe"]>=base_val["sharpe"] and m["ret"]>=.80*base_val["ret"])
        valrows.append({**{k:r[k] for k in ("dd_cut","vol_cut","breadth_cut","crisis_scale","rank_buffer","score_gap","min_hold")},
                        **{"val_"+k:v for k,v in m.items()},"baseline_ret":base_val["ret"],
                        "baseline_mdd":base_val["mdd"],"baseline_sharpe":base_val["sharpe"],"passed":passed})
        if passed: survivors.append(run)
    pd.DataFrame(valrows).to_csv(out/"e1_validation_gate.csv",index=False)
    status={"version":"V4.12-E1","train":TRAIN,"validation":VALID,
            "gate":"ret>0; mdd>-25%; Sharpe>=frozen D; ret>=80% frozen D", "validation_pass":bool(survivors)}
    if not survivors:
        status["reason"]="No Train-selected robust-plateau candidate passed the frozen Validation gate"
        (out/"e1_status.json").write_text(json.dumps(status,indent=2)); print(g.head(12).to_string(index=False)); print(pd.DataFrame(valrows).to_string(index=False)); print(status); return
    # Validation only rejects; among passers preserve the highest pre-validation Train score.
    winner=max(survivors,key=lambda x:x[0]["train_score"]); r,nav,w,cost,risk,scaled=winner
    summary=[]
    for name,p in OOS.items():
        for label,series in (("E1",nav),("Frozen_D",d_nav),("EqualWeight12",ew)):
            summary.append({"strategy":label,"period":name,**metrics(series,p)})
    pd.DataFrame(summary).to_csv(out/"e1_walkforward_summary.csv",index=False)
    pd.DataFrame({"date":nav.index,"e1_nav":nav.values,"frozen_d_nav":d_nav.values,"equal_weight_nav":ew.values,
                  "cost":cost.values,"crisis":risk.crisis.values,"exposure":scaled.sum(axis=1).values}).to_csv(out/"e1_curves.csv",index=False)
    w.reset_index().to_csv(out/"e1_weights.csv",index=False); risk.reset_index().to_csv(out/"e1_risk_state.csv",index=False)
    sens=[]
    for cm in (0,1,2,3):
        snav,*_=nav_from_weights(rc,ro,ac,ao,buffered_targets(scores,list(rc.index),r["rank_buffer"],r["score_gap"],r["min_hold"]),risk,r["crisis_scale"],cm)
        for name,p in OOS.items(): sens.append({"cost_multiple":cm,"period":name,**metrics(snav,p)})
    pd.DataFrame(sens).to_csv(out/"e1_cost_sensitivity.csv",index=False)
    status.update({"winner":{k:(int(v) if k in ("rank_buffer","min_hold") else float(v)) for k,v in r.items() if k in ("dd_cut","vol_cut","breadth_cut","crisis_scale","rank_buffer","score_gap","min_hold")},
                   "signals":"raw/unadjusted only through T","execution":"T+1 open","evaluation":"corporate-action-adjusted layer","later_windows_used_for_selection":False})
    (out/"e1_status.json").write_text(json.dumps(status,indent=2)); print(g.head(12).to_string(index=False)); print(pd.DataFrame(valrows).to_string(index=False)); print(pd.DataFrame(summary).round(4).to_string(index=False)); print(status)


if __name__ == "__main__": main()
