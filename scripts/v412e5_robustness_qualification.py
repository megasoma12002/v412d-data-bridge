#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
import v412d_formal_router as d
import v412e1_crisis_buffer as e1
import v412e11_graduated_crisis as e11
import v412e2_e3_three_rounds as e3mod
import v412e4_execution_efficiency as e4

PERIODS={"2015_2020":("2015-01-01","2020-12-31"),"2021_2022":("2021-01-01","2022-12-31"),"2023_2025":("2023-01-01","2025-12-31"),"2026":("2026-01-01","2026-12-31")}

def nav_from_w(close,op,w,cost_mult=1,slip_bps=0):
    w=w.reindex(index=close.index,columns=close.columns).fillna(0); prev=w.shift(1).fillna(0)
    overnight=(prev*(op/close.shift(1)-1).replace([np.inf,-np.inf],np.nan).fillna(0)).sum(axis=1)
    intraday=(w*(close/op-1).replace([np.inf,-np.inf],np.nan).fillna(0)).sum(axis=1)
    delta=w-prev; turnover=delta.abs().sum(axis=1)
    cost=cost_mult*(delta.clip(lower=0).sum(axis=1)*d.FEE+(-delta.clip(upper=0)).sum(axis=1)*(d.FEE+d.TAX))+turnover*slip_bps/10000
    return (1+overnight+intraday-cost).cumprod(),cost,turnover

def bootstrap_pair(e4r,dr,block,nboot=1000,seed=4125):
    x=pd.concat([e4r.rename('e4'),dr.rename('d')],axis=1).dropna().values; n=len(x); rng=np.random.default_rng(seed+block+n)
    out=[]
    for _ in range(nboot):
        idx=[]
        while len(idx)<n:
            s=int(rng.integers(0,max(1,n-block+1))); idx.extend(range(s,min(s+block,n)))
        z=x[np.array(idx[:n])]
        navs=np.cumprod(1+z,axis=0); rets=navs[-1]-1; mdds=np.min(navs/np.maximum.accumulate(navs,axis=0)-1,axis=0)
        shp=np.mean(z,axis=0)/np.std(z,axis=0)*np.sqrt(252)
        out.append((rets[0]>rets[1],mdds[0]>mdds[1],shp[0]>shp[1],rets[0]-rets[1],mdds[0]-mdds[1],shp[0]-shp[1]))
    a=np.asarray(out,float)
    return dict(n=n,block=block,p_ret_gt=float(a[:,0].mean()),p_mdd_better=float(a[:,1].mean()),p_sharpe_gt=float(a[:,2].mean()),median_excess_ret=float(np.median(a[:,3])),median_mdd_improvement=float(np.median(a[:,4])),median_sharpe_improvement=float(np.median(a[:,5])))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--adjusted',required=True); ap.add_argument('--weights',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw); adj=pd.read_csv(a.adjusted); z=d.prep(raw); rc,ro,ac,ao=e1.aligned_matrices(raw,adj)
    e4w=pd.read_csv(a.weights); e4w['date']=pd.to_datetime(e4w.date); e4w=e4w.set_index('date'); e4nav,e4cost,e4to=nav_from_w(ac,ao,e4w)
    scores=d.make_scores(z,1); dsig,_=d.targets(scores,list(rc.index),21,2,75); dw=dsig.shift(1).fillna(0); dnav,dcost,dto=nav_from_w(ac,ao,dw)
    # Baseline reconciliation with E4 output.
    prior=pd.read_csv('v412e4_results/e4_multiregime_summary.csv'); rec=[]
    for label,p in [('2021_2022',PERIODS['2021_2022']),('2023_2025',PERIODS['2023_2025']),('2026',PERIODS['2026'])]:
        now=e1.metrics(e4nav,p); old=prior[(prior.strategy=='E4_C')&(prior.period==label)].iloc[0]
        rec.append({'period':label,'ret_diff':now['ret']-old.ret,'mdd_diff':now['mdd']-old.mdd,'sharpe_diff':now['sharpe']-old.sharpe})
    pd.DataFrame(rec).to_csv(out/'e5_baseline_reconciliation.csv',index=False)

    # Round 1: paired moving-block bootstrap; weights are frozen.
    b=[]
    er=e4nav.pct_change(); dr=dnav.pct_change()
    for name,p in PERIODS.items():
      for block in (21,63): b.append({'period':name,**bootstrap_pair(er.loc[p[0]:p[1]],dr.loc[p[0]:p[1]],block)})
    pd.DataFrame(b).to_csv(out/'e5_round1_block_bootstrap.csv',index=False)

    # Round 2: leave one stock out and redistribute only among currently held names, preserving exposure.
    loo=[]
    for sid in e4w.columns:
        w=e4w.copy(); total=w.sum(axis=1); w[sid]=0; remain=w.sum(axis=1); factor=(total/remain.replace(0,np.nan)).fillna(0); w=w.mul(factor,axis=0)
        nav,cost,to=nav_from_w(ac,ao,w)
        for name,p in PERIODS.items(): loo.append({'excluded':sid,'period':name,**e1.metrics(nav,p),'turnover':float(to.loc[p[0]:p[1]].sum())})
    pd.DataFrame(loo).to_csv(out/'e5_round2_leave_one_out.csv',index=False)

    # Round 3: frozen neighborhood, no winner selection. All combinations must remain usable.
    q=e3mod.raw_risk_features(z); exposure=e3mod.exposure_controller(q,'voltarget',.5,20,.14,.5); rt=2*d.FEE+d.TAX; hood=[]
    for hold in (63,84,105):
        base=e1.buffered_targets(scores,list(rc.index),0,5*rt,hold)
        for frac in (.20,.25,.33):
            sig=e4.partial_rebalance(base,frac,.05); nav,w,cost,_=e11.nav_with_exposure(ac,ao,sig,exposure)
            for name,p in PERIODS.items(): hood.append({'min_hold':hold,'partial_fraction':frac,'period':name,**e1.metrics(nav,p),'turnover':float(w.diff().abs().sum(axis=1).loc[p[0]:p[1]].sum())})
    pd.DataFrame(hood).to_csv(out/'e5_round3_parameter_neighborhood.csv',index=False)

    # Round 4: operational shocks to frozen E4 weights.
    shocks=[]
    for delay in (0,1,2):
      for cm in (1,2,3):
       for slip in (0,10,25):
        w=e4w.shift(delay).fillna(0); nav,cost,to=nav_from_w(ac,ao,w,cm,slip)
        for name,p in PERIODS.items(): shocks.append({'extra_delay_days':delay,'cost_multiple':cm,'slippage_bps':slip,'period':name,**e1.metrics(nav,p),'turnover':float(to.loc[p[0]:p[1]].sum())})
    pd.DataFrame(shocks).to_csv(out/'e5_round4_execution_shocks.csv',index=False)

    B=pd.DataFrame(b); L=pd.DataFrame(loo); H=pd.DataFrame(hood); X=pd.DataFrame(shocks)
    # Predeclared qualification: numerical reconcile; MDD+Sharpe bootstrap majority in >=3/4 periods;
    # all LOO/neighborhood later-period returns positive; worst operational shock positive in all periods.
    reconcile=max(abs(x) for r in rec for x in r.values() if not isinstance(x,str))<1e-10
    bq=((B.groupby('period').p_mdd_better.mean()>.5)&(B.groupby('period').p_sharpe_gt.mean()>.5)).sum()>=3
    lq=bool((L.ret>0).all()); hq=bool((H.ret>0).all()); worst=X[(X.extra_delay_days==2)&(X.cost_multiple==3)&(X.slippage_bps==25)]; xq=bool((worst.ret>0).all())
    status={'version':'V4.12-E5','rounds':4,'baseline_reconciled':bool(reconcile),'bootstrap_qualified':bool(bq),'leave_one_out_qualified':lq,'parameter_neighborhood_qualified':hq,'execution_shock_qualified':xq,'robustness_qualified':bool(reconcile and bq and lq and hq and xq),'promotion_eligible':False,'formal_strategy':'V4.12-D','forward_challenger':'Frozen E4','warning':'No new unseen OOS; qualification supports robustness only'}
    (out/'e5_status.json').write_text(json.dumps(status,indent=2)); print(pd.DataFrame(rec).to_string(index=False)); print(B.to_string(index=False)); print(L.groupby('period').agg(min_ret=('ret','min'),max_mdd=('mdd','min'),min_sharpe=('sharpe','min')).to_string()); print(H.groupby('period').agg(min_ret=('ret','min'),worst_mdd=('mdd','min'),min_sharpe=('sharpe','min')).to_string()); print(worst.to_string(index=False)); print(status)

if __name__=='__main__': main()
