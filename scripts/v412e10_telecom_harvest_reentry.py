#!/usr/bin/env python3
"""V4.12-E10 Telecom Harvest -> Financial Reentry state-machine research."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from v412e7_multi_edge_lab import metrics

BUY=.000855; SELL=.003855; FIN='2880 2886 2892 5880 2801 2834 2884 2885 2890 2891 2881 2882'.split(); TEL=['2412','3045','4904']

def portfolio(ret,w):
    held=w.shift(1).fillna(0);d=held.diff().fillna(held)
    costs=d.clip(lower=0).sum(axis=1)*BUY+(-d.clip(upper=0)).sum(axis=1)*SELL
    net=(held*ret).sum(axis=1)-costs
    return (1+net).cumprod(),costs,float(d.abs().sum(axis=1).mean()*252)

def make_weights(dates,cols,fin_index,tel_index,fin_close,mode):
    fr=fin_index.pct_change(fill_method=None);vol=fr.rolling(63).std()*np.sqrt(252);vth=vol.rolling(756,min_periods=252).quantile(.75).shift(1)
    dd=fin_index/fin_index.rolling(126).max()-1; ma200=fin_index.rolling(200).mean();ma120=fin_index.rolling(120).mean();ma20=fin_index.rolling(20).mean()
    breadth=(fin_close>fin_close.rolling(60).mean()).mean(axis=1); recovery=((fin_index>ma120)&(ma20>ma20.shift(5))&(breadth>=.5)).rolling(5).sum()>=5
    w=pd.DataFrame(0.,index=dates,columns=cols);events=[];state='NORMAL';stages=set();ratio0=np.nan;stepdown_date=None
    for d in dates:
        crisis=bool(mode not in ('benchmark','static10') and pd.notna(vth.loc[d]) and dd.loc[d]<=-.12 and fin_index.loc[d]<ma200.loc[d] and vol.loc[d]>vth.loc[d])
        if state=='NORMAL' and crisis:
            state='CRISIS';stages=set();ratio0=tel_index.loc[d]/fin_index.loc[d];events.append({'date':d,'event':'crisis_enter','drawdown':dd.loc[d],'relative_gain':0.})
        if state in ('CRISIS','REENTRY'):
            rel=tel_index.loc[d]/fin_index.loc[d]/ratio0-1
            thresholds=[(-.15,.03,1),(-.20,.06,2),(-.25,.09,3)]
            for cut,rel_req,n in thresholds:
                eligible=dd.loc[d]<=cut and n not in stages and (mode!='relative_harvest' or rel>=rel_req)
                if eligible:stages.add(n);state='REENTRY';events.append({'date':d,'event':f'reentry_{n}','drawdown':dd.loc[d],'relative_gain':rel})
            # Recovery must always allow exit; relative-gain gates apply only to harvesting tranches.
            if bool(recovery.loc[d]) and 4 not in stages:
                stages.add(4);state='RECOVERY';stepdown_date=d;events.append({'date':d,'event':'recovery_confirm','drawdown':dd.loc[d],'relative_gain':rel})
        elif state=='RECOVERY' and (d-stepdown_date).days>=30:
            state='NORMAL';stages=set();events.append({'date':d,'event':'normal_restore','drawdown':dd.loc[d],'relative_gain':np.nan})
        if mode=='benchmark':fw,tw,cash=1.,0.,0.
        elif mode=='static10':fw,tw,cash=.90,.10,0.
        elif state=='NORMAL':fw,tw,cash=.90,.10,0.
        elif state in ('CRISIS','REENTRY'):
            n=len(stages);fw=.55+.05*n;tw=.35-.05*n;cash=.10
        else:fw,tw,cash=.825,.125,.05
        w.loc[d,FIN]=fw/len(FIN);w.loc[d,TEL]=tw/len(TEL)
    return w,pd.DataFrame(events),pd.DataFrame({'drawdown126':dd,'financial_vol63':vol,'vol_threshold':vth,'breadth60':breadth,'recovery':recovery})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--financial-adjusted',required=True);ap.add_argument('--telecom-adjusted',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    f=pd.read_csv(a.financial_adjusted);t=pd.read_csv(a.telecom_adjusted)
    for x in (f,t):x.date=pd.to_datetime(x.date);x.code=x.code.astype(str)
    fc=f.pivot(index='date',columns='code',values='adjusted_close').sort_index();tc=t.pivot(index='date',columns='code',values='adjusted_close').sort_index();dates=fc.index.intersection(tc.index);fc=fc.reindex(dates).ffill(limit=3);tc=tc.reindex(dates).ffill(limit=3)
    ret=pd.concat([fc.pct_change(fill_method=None),tc.pct_change(fill_method=None)],axis=1).fillna(0);fi=(1+ret[FIN].mean(axis=1)).cumprod();ti=(1+ret[TEL].mean(axis=1)).cumprod()
    modes={'E10A_financial_benchmark':'benchmark','E10B_static10_telco':'static10','E10C_staged_reentry':'staged','E10D_relative_harvest_reentry':'relative_harvest'};navs=[];rows=[];all_events=[]
    splits={'Train_2010_2018':('2010-01-01','2018-12-31'),'Validation_2019_2022':('2019-01-01','2022-12-31'),'Blind_2023_2025':('2023-01-01','2025-12-31'),'FinalOOS_2026':('2026-01-01','2026-12-31')}
    for name,mode in modes.items():
        w,events,diag=make_weights(dates,ret.columns,fi,ti,fc,mode);nav,cost,turn=portfolio(ret,w);navs.append(nav.rename(name));w.to_csv(out/f'{name}_weights.csv');events['model']=name;all_events.append(events)
        for split,(s,e) in splits.items():
            q=nav.loc[s:e];b=fi.loc[s:e]
            if len(q)<2:continue
            q=q/q.iloc[0];b=b/b.iloc[0];m=metrics(q);bm=metrics(b)
            rows.append({'model':name,'split':split,**m,'benchmark_cagr':bm['cagr'],'benchmark_sharpe':bm['sharpe'],'benchmark_max_drawdown':bm['max_drawdown'],'cagr_delta':m['cagr']-bm['cagr'],'sharpe_delta':m['sharpe']-bm['sharpe'],'turnover':turn,'cost_drag_full':float(cost.sum())})
    res=pd.DataFrame(rows);res.to_csv(out/'e10_metrics.csv',index=False);pd.concat(navs,axis=1).to_csv(out/'e10_nav.csv');ev=pd.concat(all_events,ignore_index=True);ev.to_csv(out/'e10_events.csv',index=False);diag.to_csv(out/'e10_diagnostics.csv')
    verdict=[]
    for name in list(modes)[1:]:
        q=res[res.model==name].set_index('split');tr=q.loc['Train_2010_2018'];v=q.loc['Validation_2019_2022'];bl=q.loc['Blind_2023_2025'];o=q.loc['FinalOOS_2026']
        vp=bool(tr.sharpe_delta>0 and v.total_return>0 and v.max_drawdown>-.25 and v.sharpe_delta>=0);bc=bool(vp and bl.sharpe_delta>0 and bl.max_drawdown>bl.benchmark_max_drawdown)
        verdict.append({'model':name,'validation_pass':vp,'blind_confirmed':bc,'final_oos_cagr_delta':o.cagr_delta,'final_oos_sharpe_delta':o.sharpe_delta,'crisis_entries':int(((ev.model==name)&(ev.event=='crisis_enter')).sum()),'status':'qualified_shadow' if bc else 'reject_or_watch'})
    vd=pd.DataFrame(verdict);vd.to_csv(out/'e10_verdict.csv',index=False)
    status={'version':'V4.12-E10','validation_pass_count':int(vd.validation_pass.sum()),'blind_confirmed_count':int(vd.blind_confirmed.sum()),'qualified_models':vd.loc[vd.blind_confirmed,'model'].tolist(),'execution':'T close signal -> T+1 weights; full transaction costs','integration':'research only; D/E4/E9 forward remain frozen pending qualification'}
    (out/'e10_status.json').write_text(json.dumps(status,indent=2)+'\n');print(vd.to_string(index=False));print(json.dumps(status,indent=2))

if __name__=='__main__':main()
