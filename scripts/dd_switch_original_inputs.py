"""Append current observations to locked original inputs without rewriting history."""
from pathlib import Path
import pandas as pd
from e16_soft_frozen_base import FIN,TEL
CUTOFF=pd.Timestamp('2026-09-29')

def append_market(original,tip,asof):
    original=original[original.date<=CUTOFF]
    tip=tip[(tip.date>CUTOFF)&(tip.date<=pd.Timestamp(asof))]
    joined=pd.concat([original,tip],ignore_index=True).sort_values(['date','code'])
    if joined.duplicated(['date','code']).any():raise ValueError('Duplicate append-only market rows')
    return joined

def append_dividends(snapshot,current,out,asof):
    original=pd.read_csv(snapshot,dtype={'code':str})
    new=pd.read_csv(current,dtype={'code':str})
    announced=pd.to_datetime(new.announcement_date,errors='coerce')
    core=set(FIN+TEL+['0050','00631L'])
    new=new[(announced>CUTOFF)&(announced<=pd.Timestamp(asof))&new.code.isin(core)].copy()
    columns=list(original.columns)
    identical=set(map(tuple,original[columns].fillna('').astype(str).to_numpy()))
    keep=pd.Series([tuple(row) not in identical for row in new[columns].fillna('').astype(str).to_numpy()],index=new.index,dtype=bool)
    new=new.loc[keep]
    for column in ['cash_ex_date','stock_ex_date']:
        dates=pd.to_datetime(new[column],errors='coerce')
        if (dates.notna()&(dates<=CUTOFF)).any():
            raise ValueError('Post-cutoff dividend announcement revises frozen ex-date history')
    # Keep original rows, including known future events. Revised future-event
    # records need an explicit versioning decision instead of duplicate rights.
    keys=['code','fiscal_year','cash_ex_date','stock_ex_date']
    prior=set(map(tuple,original[keys].fillna('').astype(str).to_numpy()))
    if any(tuple(r) in prior for r in new[keys].fillna('').astype(str).to_numpy()):
        raise ValueError('Future dividend revision requires versioned original-input review')
    pd.concat([original,new],ignore_index=True).to_csv(out,index=False)
    return Path(out)
