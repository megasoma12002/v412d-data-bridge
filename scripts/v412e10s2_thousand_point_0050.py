#!/usr/bin/env python3
"""V4.12-E10S3: single-day and cumulative TAIEX 1000-point shocks with 0050."""
import argparse,json,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from v412e7_multi_edge_lab import metrics

FIN='2880 2886 2892 5880 2801 2834 2884 2885 2890 2891 2881 2882'.split();TEL=['2412','3045','4904'];BASE='https://api.finmindtrade.com/api/v4/data';BUY=.000855;SELL=.003855

def get(ds,sid,start,end):
    q={'dataset':ds,'start_date':start,'end_date':end}
    if sid:q['data_id']=sid
    req=urllib.request.Request(BASE+'?'+urllib.parse.urlencode(q),headers={'User-Agent':'v412e10s2/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:o=json.load(r)
    if o.get('status')!=200:raise RuntimeError(f'{ds}/{sid}: {o}')
    return o.get('data',[])

def build_0050(end,out):
    rows=get('TaiwanStockPrice','0050','2010-01-01',end);x=pd.DataFrame([{'code':'0050','date':r['date'],'open':r['open'],'high':r['max'],'low':r['min'],'close':r['close'],'volume':r['Trading_Volume']} for r in rows]);x.date=pd.to_datetime(x.date)
    actions=[]
    for r in get('TaiwanStockDividendResult','0050','2010-01-01',end):
        b=float(r['before_price']);a=float(r['after_price'])
        if b>0 and a>0:actions.append({'date':pd.Timestamp(r['date']),'factor':a/b,'type':'distribution'})
    for r in get('TaiwanStockSplitPrice',None,'2010-01-01',end):
        if str(r.get('stock_id'))!='0050':continue
        b=float(r['before_price']);a=float(r['after_price'])
        if b>0 and a>0:actions.append({'date':pd.Timestamp(r['date']),'factor':a/b,'type':'split'})
    act=pd.DataFrame(actions);adj=[]
    for _,r in x.iterrows():
        factor=float(act.loc[act.date>r.date,'factor'].prod()) if len(act) else 1.;adj.append({'date':r.date,'adjusted_close':r.close*factor,'factor':factor})
    x.assign(date=x.date.dt.date).to_csv(out/'e10s2_0050_raw.csv',index=False);act.assign(date=act.date.dt.date).to_csv(out/'e10s2_0050_actions.csv',index=False);z=pd.DataFrame(adj).set_index('date').adjusted_close.sort_index();pd.DataFrame(adj).assign(date=lambda q:q.date.dt.date).to_csv(out/'e10s2_0050_adjusted.csv',index=False)
    return x.set_index('date').close.sort_index(),z

def target_weights(dates,cols,shock,mode):
    w=pd.DataFrame(0.,index=dates,columns=cols);age=999;events=[]
    for d in dates:
        if bool(shock.loc[d]) and age>=10:age=0;events.append(d)
        if age<10:
            if mode=='financial':fw,tw,ew=.95,.05,0
            elif mode=='0050':fw,tw,ew=.90,.05,.05
            else:fw,tw,ew=.925,.05,.025
        else:fw,tw,ew=.90,.10,0
        w.loc[d,FIN]=fw/len(FIN);w.loc[d,TEL]=tw/len(TEL);w.loc[d,'0050']=ew;age+=1
    return w,events

def portfolio(ret,w):
    held=w.shift(1).fillna(0);d=held.diff().fillna(held);cost=d.clip(lower=0).sum(axis=1)*BUY+(-d.clip(upper=0)).sum(axis=1)*SELL
    return (1+(held*ret).sum(axis=1)-cost).cumprod(),float(d.abs().sum(axis=1).mean()*252),float(cost.sum())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--financial-adjusted',required=True);ap.add_argument('--telecom-adjusted',required=True);ap.add_argument('--out',required=True);ap.add_argument('--end-date',required=True);a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    f=pd.read_csv(a.financial_adjusted);t=pd.read_csv(a.telecom_adjusted)
    for x in(f,t):x.date=pd.to_datetime(x.date);x.code=x.code.astype(str)
    fc=f.pivot(index='date',columns='code',values='adjusted_close').sort_index();tc=t.pivot(index='date',columns='code',values='adjusted_close').sort_index();raw0050,adj0050=build_0050(a.end_date,out)
    ta=pd.DataFrame(get('TaiwanStockPrice','TAIEX','2010-01-01',a.end_date));ta.date=pd.to_datetime(ta.date);ta=ta.set_index('date').sort_index();ta.close=pd.to_numeric(ta.close);dates=fc.index.intersection(tc.index).intersection(adj0050.index).intersection(ta.index)
    fc=fc.reindex(dates).ffill(limit=3);tc=tc.reindex(dates).ffill(limit=3);adj0050=adj0050.reindex(dates).ffill(limit=3);ta=ta.reindex(dates)
    ret=pd.concat([fc.pct_change(fill_method=None),tc.pct_change(fill_method=None),adj0050.pct_change(fill_method=None).rename('0050')],axis=1).fillna(0);fr=ret[FIN].mean(axis=1);tr=ret[TEL].mean(axis=1);er=ret['0050']
    horizons=[1,2,3,5]; shock_table=pd.DataFrame(index=dates)
    for h in horizons:
        shock_table[f'point_drop_{h}d']=ta.close-ta.close.shift(h)
        shock_table[f'pct_drop_{h}d']=ta.close/ta.close.shift(h)-1
        shock_table[f'shock_{h}d']=(shock_table[f'point_drop_{h}d']<=-1000)&(shock_table[f'pct_drop_{h}d']<=-.02)
    shock_guarded=shock_table[[f'shock_{h}d' for h in horizons]].any(axis=1)
    shock_table.assign(close=ta.close,shock_combined=shock_guarded).to_csv(out/'e10s2_taiex.csv')
    selected=[];last=-99
    for i,d in enumerate(dates):
        if shock_guarded.loc[d] and i-last>=10:
            hit=[h for h in horizons if bool(shock_table.loc[d,f'shock_{h}d'])]
            h=min(hit);selected.append((i,d,h,float(shock_table.loc[d,f'point_drop_{h}d']),float(shock_table.loc[d,f'pct_drop_{h}d'])));last=i
    study=[]
    for i,d,trigger_h,p,pr in selected:
        for h in [1,5,10,20]:
            if i+h>=len(dates):continue
            vals={k:(1+s.iloc[i+1:i+h+1]).prod()-1 for k,s in [('financial',fr),('telecom',tr),('0050',er)]};study.append({'date':d,'trigger_window':trigger_h,'point_drop':p,'taiex_return':pr,'horizon':h,**vals,'financial_minus_telecom':vals['financial']-vals['telecom'],'0050_minus_telecom':vals['0050']-vals['telecom']})
    es=pd.DataFrame(study);es.to_csv(out/'e10s2_event_study.csv',index=False);summary=es.groupby('horizon').agg(n=('date','size'),financial_vs_telco=('financial_minus_telecom','mean'),etf_vs_telco=('0050_minus_telecom','mean'),financial_win=('financial_minus_telecom',lambda z:(z>0).mean()),etf_win=('0050_minus_telecom',lambda z:(z>0).mean())).reset_index();summary.to_csv(out/'e10s2_event_summary.csv',index=False)
    modes={'E10S2_A_telco_to_financial':'financial','E10S2_B_telco_to_0050':'0050','E10S2_C_split_financial_0050':'split'};splits={'Train_2010_2018':('2010-01-01','2018-12-31'),'Validation_2019_2022':('2019-01-01','2022-12-31'),'Blind_2023_2025':('2023-01-01','2025-12-31'),'FinalOOS_2026':('2026-01-01','2026-12-31')};basew=pd.DataFrame(0.,index=dates,columns=ret.columns);basew[FIN]=.9/len(FIN);basew[TEL]=.1/len(TEL);base,_t,_c=portfolio(ret,basew);rows=[];navs=[base.rename('static_90F_10T')];events=[]
    for name,mode in modes.items():
        w,ev=target_weights(dates,ret.columns,shock_guarded,mode);nav,turn,cost=portfolio(ret,w);navs.append(nav.rename(name));events += [{'model':name,'date':d} for d in ev];w.to_csv(out/f'{name}_weights.csv')
        for split,(s,z) in splits.items():
            q=nav.loc[s:z];b=base.loc[s:z]
            if len(q)<2:continue
            q=q/q.iloc[0];b=b/b.iloc[0];m=metrics(q);bm=metrics(b);rows.append({'model':name,'split':split,**m,'base_cagr':bm['cagr'],'base_sharpe':bm['sharpe'],'base_mdd':bm['max_drawdown'],'cagr_delta':m['cagr']-bm['cagr'],'sharpe_delta':m['sharpe']-bm['sharpe'],'turnover':turn,'cost_drag':cost})
    res=pd.DataFrame(rows);res.to_csv(out/'e10s2_metrics.csv',index=False);pd.concat(navs,axis=1).to_csv(out/'e10s2_nav.csv');pd.DataFrame(events).to_csv(out/'e10s2_events.csv',index=False)
    q0050={'status':'PASS' if len(raw0050)>3000 and raw0050.index.is_unique and raw0050.notna().all() and raw0050.index.max().year==2026 else 'FAIL','rows':len(raw0050),'first_date':raw0050.index.min().date().isoformat(),'latest_date':raw0050.index.max().date().isoformat(),'duplicates':int(raw0050.index.duplicated().sum()),'nulls':int(raw0050.isna().sum())}
    counts={f'{h}d':int(shock_table[f'shock_{h}d'].sum()) for h in horizons}
    status={'version':'V4.12-E10S3','shock_rule':'TAIEX cumulative close change <= -1000 and return <= -2% over 1/2/3/5 sessions; 10-session cooldown','candidate_days_by_window':counts,'guarded_shock_days':int(shock_guarded.sum()),'independent_events':len(selected),'0050_qc':q0050,'integration':'forward shadow monitor only; overlapping windows deduplicated'};(out/'e10s2_status.json').write_text(json.dumps(status,indent=2)+'\n');print(summary.round(4).to_string(index=False));print(res[['model','split','cagr_delta','sharpe_delta','max_drawdown']].round(4).to_string(index=False));print(json.dumps(status,indent=2))

if __name__=='__main__':main()
