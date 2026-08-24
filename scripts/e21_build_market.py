#!/usr/bin/env python3
"""Build the canonical E21 forward market panel from frozen research layers."""
import argparse
from pathlib import Path
import pandas as pd

FIN=['2880','2886','2892','5880']; TEL=['2412','3045','4904']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--financial-raw',required=True);ap.add_argument('--financial-adjusted',required=True)
    ap.add_argument('--telecom-0050-raw',required=True);ap.add_argument('--telecom-adjusted',required=True)
    ap.add_argument('--etf0050-adjusted',required=True);ap.add_argument('--taiex',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args(); pieces=[]
    fr=pd.read_csv(a.financial_raw,dtype={'code':str});fa=pd.read_csv(a.financial_adjusted,dtype={'code':str})
    fr.date=pd.to_datetime(fr.date);fa.date=pd.to_datetime(fa.date)
    f=fr[fr.code.isin(FIN)].merge(fa[['date','code','adjusted_close']],on=['date','code'],how='inner').rename(columns={'adjusted_close':'adj_close'})
    pieces.append(f[['date','code','open','high','low','close','adj_close','volume']])
    raw=pd.read_csv(a.telecom_0050_raw,dtype={'code':str});raw.date=pd.to_datetime(raw.date)
    ta=pd.read_csv(a.telecom_adjusted,dtype={'code':str});ta.date=pd.to_datetime(ta.date)
    raw_cols=['date','code','open','high','low','close','volume']
    t=raw[raw.code.isin(TEL)][raw_cols].merge(ta[['date','code','adjusted_close']],on=['date','code'],how='inner').rename(columns={'adjusted_close':'adj_close'})
    pieces.append(t[['date','code','open','high','low','close','adj_close','volume']])
    ea=pd.read_csv(a.etf0050_adjusted);ea.date=pd.to_datetime(ea.date);ea['code']='0050'
    e=raw[raw.code.eq('0050')][raw_cols].merge(ea[['date','code','adjusted_close']],on=['date','code'],how='inner').rename(columns={'adjusted_close':'adj_close'})
    pieces.append(e[['date','code','open','high','low','close','adj_close','volume']])
    ix=pd.read_csv(a.taiex);ix.date=pd.to_datetime(ix.date);ix['code']='TAIEX';ix['open']=ix.close;ix['high']=ix.close;ix['low']=ix.close;ix['adj_close']=ix.close;ix['volume']=0
    pieces.append(ix[['date','code','open','high','low','close','adj_close','volume']])
    z=pd.concat(pieces,ignore_index=True).sort_values(['date','code']).drop_duplicates(['date','code'],keep='last')
    required=set(FIN+TEL+['0050','TAIEX']);good=z.groupby('date').code.apply(lambda s:required.issubset(set(s)))
    dates=good[good].index;z=z[z.date.isin(dates)]
    if len(dates)<500:raise RuntimeError(f'insufficient complete E21 history: {len(dates)} dates')
    for c in ['open','high','low','close','adj_close','volume']:
        if z[c].isna().any():raise RuntimeError(f'null values in {c}')
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);z.to_csv(p,index=False)
    print({'rows':len(z),'common_dates':len(dates),'first':str(dates.min().date()),'latest':str(dates.max().date()),'out':str(p)})
if __name__=='__main__':main()
