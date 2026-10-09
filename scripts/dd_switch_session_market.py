"""Explicit historical marks, actual opens, and split/eligibility contracts.

Halt marks use LAST_EXCHANGE_CLOSE in pre-split units. They are stale economic
marks, not fund NAV or executable quotes. All source prices remain unchanged.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from e16_soft_frozen_base import FIN,TEL
GAPS=['2025-02-06','2025-06-11','2025-06-12','2025-06-13','2025-06-16','2025-06-17','2026-05-28']
HALTS={'0050':pd.date_range('2025-06-11','2025-06-17',freq='B'), '00631L':pd.to_datetime(['2026-03-25','2026-03-26','2026-03-27','2026-03-30'])}
SPLITS={'2025-06-18':{'0050':4},'2026-03-31':{'00631L':22}}

def constant_factor(frame,code,day):
 sub=frame[frame.code.eq(code)].set_index('date').sort_index()
 before=sub.loc[sub.index<day].iloc[-1];after=sub.loc[sub.index>day].iloc[0]
 a=float(before.adj_close/before.close);b=float(after.adj_close/after.close)
 if not np.isclose(a,b,rtol=1e-10,atol=1e-12):raise ValueError('Ambiguous adjustment inside gap: '+code+' '+str(day))
 return a

def raw_response(path):
 obj=json.loads(path.read_text())
 if obj.get('status')!=200:raise ValueError('Provider error: '+str(path))
 frame=pd.DataFrame(obj['data']).rename(columns={'stock_id':'code','max':'high','min':'low','Trading_Volume':'volume'})
 frame.date=pd.to_datetime(frame.date)
 return frame[['date','code','open','high','low','close','volume']]

def repair_equity(original,live,root):
 original=original.copy();original.date=pd.to_datetime(original.date)
 live=live.copy();live.date=pd.to_datetime(live.date)
 original=original[original.date<='2026-09-29'];live=live[live.date<='2026-10-08']
 missing_dates=set(live.date)-set(original.date)
 extra=live[live.date.isin(missing_dates)|(live.date>'2026-09-29')]
 frame=pd.concat([original,extra],ignore_index=True)
 additions=[]
 for code in FIN:
  raw=raw_response(root/f'repro/dd-switch-history-gap-recovery/sources/{code}.json')
  for _,r in raw[raw.date.isin(pd.to_datetime(GAPS))].iterrows():
   row=r.to_dict();row['adj_close']=float(r.close)*constant_factor(frame,code,r.date);additions.append(row)
 for code in TEL+['0050']:
  raw=pd.read_csv(root/f'data/telecom_0050_complete/{code}_2010_latest_ohlcv.csv',dtype={'code':str},parse_dates=['date'])
  adjusted=pd.read_csv(root/('forward/e10s2/e10s2_0050_adjusted.csv' if code=='0050' else 'forward/e9/e9_telecom_adjusted.csv'),dtype={'code':str},parse_dates=['date'])
  if code!='0050':adjusted=adjusted[adjusted.code.eq(code)]
  adjusted=adjusted.set_index('date').adjusted_close
  for _,r in raw[raw.date.isin(pd.to_datetime(GAPS))].iterrows():
   row={c:r[c] for c in ['date','code','open','high','low','close','volume']};row['adj_close']=float(adjusted.loc[r.date]);additions.append(row)
 ix=raw_response(root/'repro/dd-switch-history-gap-recovery/sources/TAIEX.json')
 for _,r in ix[ix.date.isin(pd.to_datetime(GAPS))].iterrows():
  row=r.to_dict();row['adj_close']=r.close;additions.append(row)
 frame=pd.concat([frame,pd.DataFrame(additions)],ignore_index=True)
 if frame.duplicated(['date','code']).any():raise ValueError('Repair overwrote an existing quote')
 frame['tradable']=True;frame['mark_policy']='EXCHANGE_CLOSE';frame['unit_multiplier']=1.
 for day in HALTS['0050']:
  last=frame[frame.code.eq('0050')&(frame.date<day)].sort_values('date').iloc[-1]
  frame=pd.concat([frame,pd.DataFrame([dict(date=day,code='0050',open=np.nan,high=np.nan,low=np.nan,close=last.close,adj_close=last.adj_close,volume=0.,tradable=False,mark_policy='LAST_EXCHANGE_CLOSE',unit_multiplier=1.)])],ignore_index=True)
 frame.loc[frame.code.eq('0050')&(frame.date>='2025-06-18'),'unit_multiplier']=4.
 if frame.duplicated(['date','code']).any():raise ValueError('Duplicate repaired panel')
 return frame.sort_values(['date','code']).reset_index(drop=True)

def attach_off(equity,raw):
 raw=raw.copy();raw.date=pd.to_datetime(raw.date);dates=pd.DatetimeIndex(sorted(equity.date.unique()));first=raw.date.min();raw=raw.set_index('date')
 rows=[]
 for day in dates:
  if day in raw.index:
   row=raw.loc[day].to_dict();row.update(date=day,code='00631L',tradable=True,mark_policy='EXCHANGE_CLOSE')
  elif day<first:
   row=dict(date=day,code='00631L',open=np.nan,high=np.nan,low=np.nan,close=float(raw.iloc[0].close),adj_close=float(raw.iloc[0].adj_close),volume=0.,tradable=False,mark_policy='PRE_LIST_NO_POSITION')
  elif day in HALTS['00631L']:
   last=raw.loc[raw.index<day].iloc[-1];row=dict(date=day,code='00631L',open=np.nan,high=np.nan,low=np.nan,close=last.close,adj_close=last.adj_close,volume=0.,tradable=False,mark_policy='LAST_EXCHANGE_CLOSE')
  else:raise ValueError('Unknown post-list inverse quote gap: '+str(day.date()))
  row['unit_multiplier']=22. if day>=pd.Timestamp('2026-03-31') else 1.;rows.append(row)
 return pd.concat([equity,pd.DataFrame(rows)],ignore_index=True).sort_values(['date','code']),first
