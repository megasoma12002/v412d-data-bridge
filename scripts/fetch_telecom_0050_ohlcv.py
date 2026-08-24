#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import yfinance as yf

TICKERS={"2412":"2412.TW","3045":"3045.TW","4904":"4904.TW","0050":"0050.TW"}
out=Path("out_telecom_0050"); out.mkdir(exist_ok=True)
all_rows=[]; qc={}
for code,ticker in TICKERS.items():
    d=yf.download(ticker,start="2010-01-01",auto_adjust=False,actions=True,progress=False,threads=False)
    if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
    d=d.reset_index().rename(columns={"Date":"date","Open":"open","High":"high","Low":"low","Close":"close","Adj Close":"adjusted_close","Volume":"volume","Dividends":"dividends","Stock Splits":"stock_splits"})
    d["date"]=pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d"); d["code"]=code; d["source"]="Yahoo Finance"; d["source_symbol"]=ticker
    cols=["date","code","open","high","low","close","adjusted_close","volume","dividends","stock_splits","source","source_symbol"]
    for c in cols:
        if c not in d: d[c]=0
    d=d[cols].sort_values("date").drop_duplicates("date",keep="last")
    req=["open","high","low","close","adjusted_close","volume"]
    nulls=int(d[req].isna().sum().sum()); dup=int(d.date.duplicated().sum())
    ohlc=bool((d.high>=d[["open","close","low"]].max(axis=1)).all() and (d.low<=d[["open","close","high"]].min(axis=1)).all())
    valid=bool(len(d)>3000 and d.date.min()<="2010-01-10" and d.date.max()>="2026-01-01" and nulls==0 and dup==0 and ohlc and (d.volume>=0).all())
    qc[code]={"rows":len(d),"first_date":d.date.min(),"last_date":d.date.max(),"nulls":nulls,"duplicates":dup,"ohlc_valid":ohlc,"volume_valid":bool((d.volume>=0).all()),"pass":valid}
    d.to_csv(out/f"{code}_2010_latest_ohlcv.csv",index=False); all_rows.append(d)
combined=pd.concat(all_rows).sort_values(["date","code"])
combined.to_csv(out/"telecom_0050_2010_latest_ohlcv.csv",index=False)
common=set.intersection(*[set(x.date) for x in all_rows])
qc["combined"]={"rows":len(combined),"common_dates":len(common),"common_first":min(common),"common_last":max(common),"pass":len(common)>3000}
qc["overall_pass"]=all(v["pass"] for k,v in qc.items() if k!="overall_pass")
(out/"qc_summary.json").write_text(json.dumps(qc,indent=2)+"\n")
(out/"README.txt").write_text("Raw/unadjusted OHLCV is in open/high/low/close/volume. adjusted_close is separate. Source: Yahoo Finance.\n")
print(json.dumps(qc,indent=2))
if not qc["overall_pass"]: raise SystemExit(1)
