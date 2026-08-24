#!/usr/bin/env python3
"""Causal dividend-lifecycle event study and forward shadow signal."""
import argparse,json,urllib.parse,urllib.request
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

STOCKS="2880 2886 2892 5880 2801 2834 2884 2885 2890 2891 2881 2882".split()
ROUTER={s:r for r,x in {"R1":["2880","2886","2892","5880"],"R2":["2801","2834"],"R3":["2884","2885","2890","2891"],"R4":["2881","2882"]}.items() for s in x}
BASE="https://api.finmindtrade.com/api/v4/data"

def fetch(sid,end):
    q=urllib.parse.urlencode({'dataset':'TaiwanStockDividend','data_id':sid,'start_date':'2005-01-01','end_date':end})
    req=urllib.request.Request(BASE+'?'+q,headers={'User-Agent':'v412e6-dividend-lifecycle/1.0'})
    with urllib.request.urlopen(req,timeout=90) as r:o=json.load(r)
    if o.get('status')!=200: raise RuntimeError(f"FinMind {sid}: {o}")
    return o.get('data',[])

def normalize(rows,calendar):
    out=[]
    for r in rows:
        sid=str(r['stock_id']); ann=pd.to_datetime(r.get('AnnouncementDate'),errors='coerce'); ex=pd.to_datetime(r.get('CashExDividendTradingDate'),errors='coerce')
        cash=float(r.get('CashEarningsDistribution') or 0)+float(r.get('CashStatutorySurplus') or 0)
        stock=float(r.get('StockEarningsDistribution') or 0)+float(r.get('StockStatutorySurplus') or 0)
        if pd.isna(ann) and pd.isna(ex): continue
        # Conservative causality: even a pre-open announcement becomes usable next trading session.
        pos=calendar.searchsorted(ann) if not pd.isna(ann) else len(calendar)
        while pos<len(calendar) and calendar[pos]<=ann: pos+=1
        signal_date=calendar[pos] if pos<len(calendar) else pd.NaT
        out.append({'stock_id':sid,'router':ROUTER[sid],'fiscal_year':r.get('year',''),'record_date':r.get('date',''),'announcement_date':ann,
                    'announcement_time':r.get('AnnouncementTime',''),'signal_date':signal_date,'cash_ex_date':ex,'cash_payment_date':pd.to_datetime(r.get('CashDividendPaymentDate'),errors='coerce'),
                    'cash_dividend':cash,'stock_dividend':stock})
    x=pd.DataFrame(out).sort_values(['stock_id','cash_ex_date','announcement_date'])
    x['prior_cash_dividend']=x.groupby('stock_id').cash_dividend.shift(1)
    x['dividend_growth']=x.cash_dividend/x.prior_cash_dividend.replace(0,np.nan)-1
    return x

def event_return(close,bench,sid,anchor,start,end):
    if pd.isna(anchor) or sid not in close: return None
    idx=close.index; p=idx.searchsorted(anchor)
    if p>=len(idx) or p+start<0 or p+end>=len(idx): return None
    a,b=p+start,p+end; sr=close[sid].iloc[b]/close[sid].iloc[a]-1; br=bench.iloc[b]/bench.iloc[a]-1
    return sr,br,sr-br,idx[a],idx[b]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--raw',required=True); ap.add_argument('--adjusted',required=True); ap.add_argument('--out',required=True); ap.add_argument('--end-date',default=date.today().isoformat())
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    raw=pd.read_csv(a.raw); raw['date']=pd.to_datetime(raw.date); raw['stock_id']=raw.code.astype(str)
    adj=pd.read_csv(a.adjusted); adj['date']=pd.to_datetime(adj.date); adj['stock_id']=adj.code.astype(str)
    close=adj.pivot(index='date',columns='stock_id',values='adjusted_close').sort_index(); raw_close=raw.pivot(index='date',columns='stock_id',values='close').sort_index(); calendar=close.index
    bench=(1+close.pct_change(fill_method=None).mean(axis=1,skipna=True).fillna(0)).cumprod()
    rows=[]
    for sid in STOCKS: rows.extend(fetch(sid,a.end_date))
    events=normalize(rows,calendar); events.to_csv(out/'e6_dividend_events.csv',index=False)
    studies=[]; windows=[('announcement_m20_p20','signal_date',-20,20),('announcement_0_p20','signal_date',0,20),('pre_ex_m60_m1','cash_ex_date',-60,-1),('pre_ex_m20_m1','cash_ex_date',-20,-1),('post_ex_0_p20','cash_ex_date',0,20),('post_ex_0_p60','cash_ex_date',0,60)]
    for _,r in events.iterrows():
        sid=r.stock_id
        for name,col,s,e in windows:
            z=event_return(close,bench,sid,r[col],s,e)
            if z: studies.append({'stock_id':sid,'router':r.router,'event_year':pd.Timestamp(r[col]).year,'window':name,'stock_return':z[0],'benchmark_return':z[1],'abnormal_return':z[2],'start_date':z[3],'end_date':z[4]})
        # User hypothesis: Q4 through Q1 seasonal accumulation before that year's dividend cycle.
        if not pd.isna(r.cash_ex_date):
            y=r.cash_ex_date.year; start=pd.Timestamp(y-1,11,1); end=pd.Timestamp(y,3,31)
            i=calendar.searchsorted(start); j=calendar.searchsorted(end,side='right')-1
            if i<j and j<len(calendar):
                sr=close[sid].iloc[j]/close[sid].iloc[i]-1; br=bench.iloc[j]/bench.iloc[i]-1
                studies.append({'stock_id':sid,'router':r.router,'event_year':y,'window':'q4_q1_accumulation','stock_return':sr,'benchmark_return':br,'abnormal_return':sr-br,'start_date':calendar[i],'end_date':calendar[j]})
    study=pd.DataFrame(studies); study['split']=np.select([study.event_year<=2014,study.event_year<=2018,study.event_year<=2022],['Train_2005_2014','Validation_2015_2018','Confirm_2019_2022'],'Recent_2023_2026')
    study.to_csv(out/'e6_event_study.csv',index=False)
    summary=study.groupby(['split','window']).agg(n=('abnormal_return','size'),mean_stock_return=('stock_return','mean'),median_stock_return=('stock_return','median'),mean_abnormal_return=('abnormal_return','mean'),median_abnormal_return=('abnormal_return','median'),abnormal_win_rate=('abnormal_return',lambda x:(x>0).mean())).reset_index()
    summary.to_csv(out/'e6_event_summary.csv',index=False)

    # Latest point-in-time shadow score. It never changes D/E4 orders.
    latest=raw_close.index[-1]; latest_rows=[]
    for sid in STOCKS:
        known=events[(events.stock_id==sid)&(events.signal_date<=latest)].sort_values('signal_date'); last=known.iloc[-1] if len(known) else None
        price=float(raw_close.loc[latest,sid]); score=0.; reasons=[]; cash=np.nan; ex=pd.NaT; growth=np.nan
        if last is not None:
            cash=float(last.cash_dividend); ex=last.cash_ex_date; growth=float(last.dividend_growth) if pd.notna(last.dividend_growth) else np.nan
            trailing_yield=cash/price if price>0 else np.nan
            if latest.month in (11,12,1,2,3) and trailing_yield>=.04: score+=.5; reasons.append('Q4-Q1 trailing yield >=4%')
            if pd.notna(ex):
                days=int((ex-latest).days)
                if 5<=days<=60 and (pd.isna(growth) or growth>=0): score+=1.; reasons.append('announced positive/pre-ex lifecycle')
                if -20<=days<0: score-=.5; reasons.append('first 20 calendar days post-ex')
        else: trailing_yield=np.nan
        latest_rows.append({'stock_id':sid,'router':ROUTER[sid],'date':latest.date().isoformat(),'shadow_score':score,'cash_dividend':cash,'trailing_yield':trailing_yield,'dividend_growth':growth,'cash_ex_date':ex.date().isoformat() if pd.notna(ex) else None,'reasons':'; '.join(reasons) or 'neutral'})
    latest_df=pd.DataFrame(latest_rows); pos=latest_df.shadow_score.clip(lower=0); tilt=pos/pos.sum()*.20 if pos.sum()>0 else pos
    latest_df['suggested_shadow_tilt']=tilt; latest_df.to_csv(out/'e6_latest_shadow.csv',index=False)
    clean_latest=latest_df.astype(object).where(pd.notna(latest_df),None)
    shadow={'version':'V4.12-E6-shadow','date':latest.date().isoformat(),'execution_effect':'NONE; research shadow only','positive_edge_count':int((latest_df.shadow_score>0).sum()),'suggested_tilt_total':float(tilt.sum()),'stocks':clean_latest.to_dict('records')}
    (out/'e6_latest_shadow.json').write_text(json.dumps(shadow,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    # Frozen research gate: Validation mean abnormal >0 and win rate >50% in either Q4-Q1 or pre-ex window, with same sign in Train.
    def row(split,window):
        q=summary[(summary.split==split)&(summary.window==window)]; return None if q.empty else q.iloc[0]
    passed=[]
    for w in ('q4_q1_accumulation','pre_ex_m60_m1','pre_ex_m20_m1'):
        t=row('Train_2005_2014',w); v=row('Validation_2015_2018',w)
        if t is not None and v is not None and t.mean_abnormal_return>0 and v.mean_abnormal_return>0 and v.abnormal_win_rate>.5: passed.append(w)
    status={'version':'V4.12-E6','event_rows':len(events),'study_rows':len(study),'research_gate_pass':bool(passed),'passing_windows':passed,'integration':'shadow only; D/E4 frozen','known_gap':'earliest board dividend-proposal announcement is not provided by this dataset; AnnouncementDate is treated conservatively as usable next session','latest_date':latest.date().isoformat()}
    (out/'e6_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n'); print(summary.round(4).to_string(index=False)); print(json.dumps(status,ensure_ascii=False,indent=2)); print(json.dumps(shadow,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
