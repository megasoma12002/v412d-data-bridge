#!/usr/bin/env python3
"""V4.12-E9: build/QC Taiwan telecom data and test a separate telecom sleeve."""
import argparse,json,urllib.parse,urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from v412e7_multi_edge_lab import metrics

TELCOS=['2412','3045','4904']; BASE='https://api.finmindtrade.com/api/v4/data'; BUY=.000855; SELL=.003855

def fetch(ds,sid,start,end):
    q=urllib.parse.urlencode({'dataset':ds,'data_id':sid,'start_date':start,'end_date':end})
    req=urllib.request.Request(BASE+'?'+q,headers={'User-Agent':'v412e9-telecom/1.0'})
    with urllib.request.urlopen(req,timeout=120) as r:o=json.load(r)
    if o.get('status')!=200:raise RuntimeError(f'{ds}/{sid}: {o}')
    return o.get('data',[])

def portfolio(ret,target):
    held=target.shift(1).ffill().fillna(0); delta=held.diff().fillna(held)
    cost=delta.clip(lower=0).sum(axis=1)*BUY+(-delta.clip(upper=0)).sum(axis=1)*SELL
    return (1+(held*ret).sum(axis=1)-cost).cumprod(),float(delta.abs().sum(axis=1).mean()*252),float(cost.sum())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--financial-adjusted',required=True); ap.add_argument('--out',required=True); ap.add_argument('--end-date',required=True);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True); raws=[];actions=[]
    for sid in TELCOS:
        for r in fetch('TaiwanStockPrice',sid,'2010-01-01',a.end_date):
            raws.append({'code':sid,'date':r['date'],'open':r['open'],'high':r['max'],'low':r['min'],'close':r['close'],'volume':r['Trading_Volume']})
        for r in fetch('TaiwanStockDividendResult',sid,'2010-01-01',a.end_date):
            before=float(r['before_price']);after=float(r['after_price'])
            if before>0 and after>0:actions.append({'code':sid,'date':r['date'],'factor':after/before,'type':'dividend_or_rights'})
        for r in fetch('TaiwanStockCapitalReductionReferencePrice',sid,'2010-01-01',a.end_date):
            before=float(r['ClosingPriceonTheLastTradingDay']);after=float(r['OpeningReferencePrice'])
            if before>0 and after>0:actions.append({'code':sid,'date':r['date'],'factor':after/before,'type':'capital_reduction'})
    raw=pd.DataFrame(raws);raw.date=pd.to_datetime(raw.date);raw=raw.sort_values(['date','code']).drop_duplicates(['date','code'],keep='last')
    for c in ['open','high','low','close','volume']:raw[c]=pd.to_numeric(raw[c],errors='coerce')
    required=raw[['open','high','low','close','volume']]
    qc={'status':'PASS','stocks':TELCOS,'rows':len(raw),'first_date':raw.date.min().date().isoformat(),'latest_date':raw.date.max().date().isoformat(),'duplicates':int(raw.duplicated(['date','code']).sum()),'nulls':int(required.isna().sum().sum()),'bad_high':int((raw.high<raw[['open','low','close']].max(axis=1)).sum()),'bad_low':int((raw.low>raw[['open','high','close']].min(axis=1)).sum()),'negative_volume':int((raw.volume<0).sum()),'rows_by_stock':raw.groupby('code').size().to_dict()}
    if any(qc[k] for k in ['duplicates','nulls','bad_high','bad_low','negative_volume']) or raw.date.max().year!=2026:qc['status']='FAIL'
    raw.assign(date=raw.date.dt.date).to_csv(out/'e9_telecom_raw_ohlcv.csv',index=False)
    act=pd.DataFrame(actions);act.date=pd.to_datetime(act.date);act.to_csv(out/'e9_telecom_actions.csv',index=False)
    adj=[]
    for _,r in raw.iterrows():
        future=act[(act.code==r.code)&(act.date>r.date)];factor=float(future.factor.prod()) if len(future) else 1.
        adj.append({'code':r.code,'date':r.date,'adjusted_close':r.close*factor,'volume':r.volume,'backward_adjustment_factor':factor})
    adj=pd.DataFrame(adj);adj.assign(date=adj.date.dt.date).to_csv(out/'e9_telecom_adjusted.csv',index=False)
    fin=pd.read_csv(a.financial_adjusted);fin.date=pd.to_datetime(fin.date);fin.code=fin.code.astype(str)
    fc=fin.pivot(index='date',columns='code',values='adjusted_close').sort_index();tc=adj.pivot(index='date',columns='code',values='adjusted_close').sort_index()
    dates=fc.index.intersection(tc.index);fc=fc.reindex(dates).ffill(limit=3);tc=tc.reindex(dates).ffill(limit=3)
    fr=fc.pct_change(fill_method=None).fillna(0);tr=tc.pct_change(fill_method=None).fillna(0);allret=pd.concat([fr,tr],axis=1)
    fi=(1+fr.mean(axis=1)).cumprod();ti=(1+tr.mean(axis=1)).cumprod(); fvol=fr.mean(axis=1).rolling(63).std()*np.sqrt(252); tvol=tr.mean(axis=1).rolling(63).std()*np.sqrt(252)
    candidates={}
    def weights(tel):
        w=pd.DataFrame(0.,index=dates,columns=allret.columns);w.loc[:,fr.columns]=(1-tel.values[:,None])/len(fr.columns);w.loc[:,tr.columns]=tel.values[:,None]/len(tr.columns);return w
    candidates['E9A_static_10pct_telco']=weights(pd.Series(.10,index=dates))
    candidates['E9B_static_20pct_telco']=weights(pd.Series(.20,index=dates))
    trend_crisis=fi<fi.rolling(200).mean(); candidates['E9C_trend_defensive_10_30']=weights(pd.Series(np.where(trend_crisis,.30,.10),index=dates))
    rel=(ti/ti.shift(63)-1)/(tvol.replace(0,np.nan)) > (fi/fi.shift(63)-1)/(fvol.replace(0,np.nan)); candidates['E9D_relative_strength_10_30']=weights(pd.Series(np.where(rel,.30,.10),index=dates))
    stress=(trend_crisis)&(fvol>fvol.rolling(756,min_periods=252).quantile(.75).shift(1));candidates['E9E_stress_defensive_10_35']=weights(pd.Series(np.where(stress,.35,.10),index=dates))
    splits={'Train_2010_2018':('2010-01-01','2018-12-31'),'Validation_2019_2022':('2019-01-01','2022-12-31'),'Blind_2023_2025':('2023-01-01','2025-12-31'),'FinalOOS_2026':('2026-01-01','2026-12-31')};rows=[];navs=[]
    benchmark=(1+fr.mean(axis=1)).cumprod()
    for name,w in candidates.items():
        nav,turn,cost=portfolio(allret,w);navs.append(nav.rename(name))
        for split,(s,e) in splits.items():
            q=nav.loc[s:e];b=benchmark.loc[s:e]
            if len(q)<2:continue
            q=q/q.iloc[0];b=b/b.iloc[0];m=metrics(q);bm=metrics(b)
            rows.append({'model':name,'split':split,**m,'benchmark_cagr':bm['cagr'],'benchmark_sharpe':bm['sharpe'],'cagr_delta':m['cagr']-bm['cagr'],'sharpe_delta':m['sharpe']-bm['sharpe'],'turnover':turn,'cost_drag':cost})
    res=pd.DataFrame(rows);res.to_csv(out/'e9_metrics.csv',index=False);pd.concat([benchmark.rename('financial_equal_weight')]+navs,axis=1).to_csv(out/'e9_nav.csv')
    verdict=[]
    for name in candidates:
        q=res[res.model==name].set_index('split');t=q.loc['Train_2010_2018'];v=q.loc['Validation_2019_2022'];b=q.loc['Blind_2023_2025'];o=q.loc['FinalOOS_2026']
        vp=bool(t.sharpe_delta>0 and v.total_return>0 and v.max_drawdown>-.25 and v.sharpe_delta>=0);bc=bool(vp and b.sharpe_delta>0 and b.cagr_delta>=0)
        verdict.append({'model':name,'validation_pass':vp,'blind_confirmed':bc,'final_oos_cagr_delta':o.cagr_delta,'final_oos_sharpe_delta':o.sharpe_delta,'status':'telecom_sleeve_candidate' if bc else 'reject_or_watch'})
    vd=pd.DataFrame(verdict);vd.to_csv(out/'e9_verdict.csv',index=False)
    status={'version':'V4.12-E9','telecom_stocks':TELCOS,'data_qc':qc,'validation_pass_count':int(vd.validation_pass.sum()),'blind_confirmed_count':int(vd.blind_confirmed.sum()),'candidates':vd.loc[vd.blind_confirmed,'model'].tolist(),'integration':'separate telecom sleeve; D/E4 frozen until qualification','known_breaks':['Taiwan Mobile/Taiwan Star merger 2023','Far EasTone/Asia Pacific Telecom merger 2023']}
    (out/'e9_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');print(vd.to_string(index=False));print(json.dumps(status,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
