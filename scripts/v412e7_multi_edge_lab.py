#!/usr/bin/env python3
"""V4.12-E7 frozen multi-edge lab for the 12-stock financial universe."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd

BUY_COST=.000855
SELL_COST=.003855
ANNUAL=252

def metrics(nav):
    r=nav.pct_change().dropna(); years=max((nav.index[-1]-nav.index[0]).days/365.25,1/365.25)
    cagr=(nav.iloc[-1]/nav.iloc[0])**(1/years)-1
    vol=r.std()*np.sqrt(ANNUAL); sharpe=(r.mean()/r.std()*np.sqrt(ANNUAL)) if r.std()>0 else np.nan
    mdd=(nav/nav.cummax()-1).min()
    return {'cagr':cagr,'volatility':vol,'sharpe':sharpe,'max_drawdown':mdd,'total_return':nav.iloc[-1]/nav.iloc[0]-1}

def backtest(score,returns,exposure=None,rebalance=21,topn=3,core_weight=.80):
    dates=returns.index; w=pd.DataFrame(0.,index=dates,columns=returns.columns)
    base=pd.Series(core_weight/len(returns.columns),index=returns.columns)
    current=base.copy()
    for i,d in enumerate(dates):
        if i%rebalance==0:
            s=score.loc[d].dropna().sort_values(ascending=False)
            current=base.copy()
            if len(s): current.loc[s.index[:min(topn,len(s))]]+=(1-core_weight)/min(topn,len(s))
        w.loc[d]=current
    if exposure is not None: w=w.mul(exposure.reindex(dates).ffill().fillna(0),axis=0)
    # Signal and exposure at close T become active for next session return.
    held=w.shift(1).fillna(0)
    gross=(held*returns).sum(axis=1)
    delta=held.diff().fillna(held); cost=delta.clip(lower=0).sum(axis=1)*BUY_COST+(-delta.clip(upper=0)).sum(axis=1)*SELL_COST
    net=gross-cost
    return (1+net).cumprod(),float(delta.abs().sum(axis=1).mean()*ANNUAL),float(cost.sum())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--adjusted',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    x=pd.read_csv(a.adjusted); x.date=pd.to_datetime(x.date); x.code=x.code.astype(str)
    close=x.pivot(index='date',columns='code',values='adjusted_close').sort_index().ffill(limit=3)
    volume=x.pivot(index='date',columns='code',values='volume').sort_index().reindex(close.index).fillna(0)
    ret=close.pct_change(fill_method=None).fillna(0); bench=(1+ret.mean(axis=1)).cumprod()
    mom63=close.shift(21)/close.shift(63)-1
    mom126=close.shift(21)/close.shift(126)-1
    mom252=close.shift(21)/close.shift(252)-1
    vol63=ret.rolling(63).std()
    downside=ret.clip(upper=0).rolling(126).std()
    trend=close.rolling(20).mean()/close.rolling(120).mean()-1
    vol_ratio=volume.rolling(20).mean()/volume.rolling(120).mean().replace(0,np.nan)
    peak126=close.rolling(126).max(); drawdown=close/peak126-1
    ew=ret.mean(axis=1); ew_index=(1+ew).cumprod(); breadth=(close>close.rolling(120).mean()).mean(axis=1)
    trend_exposure=pd.Series(np.where(ew_index<ew_index.rolling(200).mean(),.65,1.),index=close.index)
    breadth_exposure=pd.Series(np.where(breadth<.40,.70,1.),index=close.index)
    ew_vol=ew.rolling(63).std()*np.sqrt(ANNUAL); vol_threshold=ew_vol.rolling(756,min_periods=252).quantile(.75).shift(1)
    vol_exposure=pd.Series(np.where(ew_vol>vol_threshold,.70,1.),index=close.index)
    candidates={
      'E7A_momentum_63_skip21':(mom63,None),
      'E7B_momentum_126_skip21':(mom126,None),
      'E7C_momentum_252_skip21':(mom252,None),
      'E7D_low_volatility_63':(-vol63,None),
      'E7E_downside_resilience_126':(-downside,None),
      'E7F_trend_20_120':(trend,None),
      'E7G_volume_confirmed_momentum':(mom63.rank(axis=1,pct=True)+vol_ratio.rank(axis=1,pct=True),None),
      'E7H_drawdown_recovery':(mom63.rank(axis=1,pct=True)+drawdown.rank(axis=1,pct=True),None),
      'E7I_trend_with_market_budget':(trend,trend_exposure),
      'E7J_volume_momentum_market_budget':(mom63.rank(axis=1,pct=True)+vol_ratio.rank(axis=1,pct=True),trend_exposure),
      'E7K_recovery_breadth_budget':(mom63.rank(axis=1,pct=True)+drawdown.rank(axis=1,pct=True),breadth_exposure),
      'E7L_downside_volatility_budget':(-downside,vol_exposure)
    }
    splits={'Train_2010_2018':('2010-01-01','2018-12-31'),'Validation_2019_2022':('2019-01-01','2022-12-31'),'Blind_2023_2025':('2023-01-01','2025-12-31'),'FinalOOS_2026':('2026-01-01','2026-12-31')}
    rows=[]; navs=[]
    for name,(score,exposure) in candidates.items():
        nav,turn,cost=backtest(score,ret,exposure)
        navs.append(nav.rename(name))
        for split,(s,e) in splits.items():
            q=nav.loc[s:e]; b=bench.loc[s:e]
            if len(q)<2: continue
            q=q/q.iloc[0]; b=b/b.iloc[0]; m=metrics(q); bm=metrics(b)
            rows.append({'edge':name,'split':split,**m,'benchmark_sharpe':bm['sharpe'],'benchmark_cagr':bm['cagr'],'sharpe_delta':m['sharpe']-bm['sharpe'],'cagr_delta':m['cagr']-bm['cagr'],'annual_turnover_full':turn,'cost_drag_full':cost})
    res=pd.DataFrame(rows); res.to_csv(out/'e7_edge_metrics.csv',index=False)
    pd.concat([bench.rename('equal_weight')]+navs,axis=1).to_csv(out/'e7_nav.csv')
    verdict=[]
    for edge in candidates:
        q=res[res.edge==edge].set_index('split')
        train=q.loc['Train_2010_2018']; val=q.loc['Validation_2019_2022']; blind=q.loc['Blind_2023_2025']; oos=q.loc['FinalOOS_2026']
        validation_pass=bool(val.total_return>0 and val.max_drawdown>-.25 and val.sharpe>0 and val.sharpe>=val.benchmark_sharpe and train.sharpe_delta>0)
        robust=bool(validation_pass and blind.sharpe_delta>0 and blind.cagr_delta>0)
        verdict.append({'edge':edge,'validation_pass':validation_pass,'blind_confirmed':robust,'final_oos_sharpe_delta':oos.sharpe_delta,'final_oos_cagr_delta':oos.cagr_delta,'status':'usable_shadow' if robust else 'reject_or_watch'})
    v=pd.DataFrame(verdict); v.to_csv(out/'e7_edge_verdict.csv',index=False)
    status={'version':'V4.12-E7','candidate_count':len(candidates),'validation_pass_count':int(v.validation_pass.sum()),'blind_confirmed_count':int(v.blind_confirmed.sum()),'usable_edges':v.loc[v.blind_confirmed,'edge'].tolist(),'integration':'80% equal-weight core + 20% edge tilt, shadow only; D/E4 frozen; no historical promotion','costs':{'buy':BUY_COST,'sell':SELL_COST},'rebalance_sessions':21,'top_n':3,'core_weight':.80,'tilt_weight':.20}
    (out/'e7_status.json').write_text(json.dumps(status,indent=2)+'\n')
    print(v.to_string(index=False)); print(json.dumps(status,indent=2))

if __name__=='__main__': main()
