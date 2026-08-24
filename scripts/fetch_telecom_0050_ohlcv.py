#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd
import requests
import yfinance as yf

TICKERS={"2412":"2412.TW","3045":"3045.TW","4904":"4904.TW","0050":"0050.TW"}
OUT=Path("out_telecom_0050"); OUT.mkdir(exist_ok=True)
all_rows=[]; qc={}; diagnostics={}

def finmind(code):
    url="https://api.finmindtrade.com/api/v4/data"
    r=requests.get(url,params={"dataset":"TaiwanStockPrice","data_id":code,"start_date":"2010-01-01"},timeout=90)
    r.raise_for_status()
    payload=r.json()
    rows=payload.get("data") or []
    if not rows:
        raise RuntimeError(f"FinMind empty: status={payload.get('status')} msg={payload.get('msg')}")
    d=pd.DataFrame(rows).rename(columns={"max":"high","min":"low","Trading_Volume":"volume"})
    return d[["date","open","high","low","close","volume"]].copy()

def yahoo(ticker):
    d=yf.download(ticker,start="2010-01-01",auto_adjust=False,progress=False,threads=False,timeout=60)
    if d.empty: raise RuntimeError("Yahoo returned empty dataframe")
    if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
    return d.reset_index().rename(columns={"Date":"date","Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})[["date","open","high","low","close","volume"]]

for code,ticker in TICKERS.items():
    errors=[]
    try:
        d=finmind(code); source="FinMind TaiwanStockPrice"
    except Exception as e:
        errors.append("FinMind: "+repr(e))
        try:
            d=yahoo(ticker); source="Yahoo Finance fallback"
        except Exception as e2:
            errors.append("Yahoo: "+repr(e2))
            diagnostics[code]={"errors":errors}
            continue
    d["date"]=pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    for c in ["open","high","low","close","volume"]:
        d[c]=pd.to_numeric(d[c],errors="coerce")
    d["code"]=code; d["adjusted_close"]=d["close"]; d["dividends"]=0.0
    d["stock_splits"]=0.0; d["source"]=source; d["source_symbol"]=ticker
    cols=["date","code","open","high","low","close","adjusted_close","volume","dividends","stock_splits","source","source_symbol"]
    d=d[cols].sort_values("date").drop_duplicates("date",keep="last")
    req=["open","high","low","close","volume"]
    nulls=int(d[req].isna().sum().sum()); dup=int(d.date.duplicated().sum())
    ohlc=bool((d.high>=d[["open","close","low"]].max(axis=1)).all() and (d.low<=d[["open","close","high"]].min(axis=1)).all())
    valid=bool(len(d)>3000 and d.date.min()<="2010-01-10" and d.date.max()>="2026-01-01" and nulls==0 and dup==0 and ohlc and (d.volume>=0).all())
    qc[code]={"rows":len(d),"first_date":d.date.min(),"last_date":d.date.max(),"nulls":nulls,"duplicates":dup,"ohlc_valid":ohlc,"volume_valid":bool((d.volume>=0).all()),"source":source,"pass":valid}
    diagnostics[code]={"errors":errors,"selected_source":source}
    d.to_csv(OUT/f"{code}_2010_latest_ohlcv.csv",index=False); all_rows.append(d)

if all_rows:
    combined=pd.concat(all_rows).sort_values(["date","code"])
    combined.to_csv(OUT/"telecom_0050_2010_latest_ohlcv.csv",index=False)
    common=set.intersection(*[set(x.date) for x in all_rows]) if len(all_rows)==4 else set()
    qc["combined"]={"rows":len(combined),"codes":sorted(combined.code.unique().tolist()),"common_dates":len(common),"common_first":min(common) if common else None,"common_last":max(common) if common else None,"pass":len(all_rows)==4 and len(common)>3000}
else:
    qc["combined"]={"rows":0,"codes":[],"common_dates":0,"pass":False}
qc["overall_pass"]=all(code in qc and qc[code]["pass"] for code in TICKERS) and qc["combined"]["pass"]
(OUT/"qc_summary.json").write_text(json.dumps(qc,indent=2,ensure_ascii=False)+"\n")
(OUT/"diagnostics.json").write_text(json.dumps(diagnostics,indent=2,ensure_ascii=False)+"\n")
(OUT/"README.txt").write_text("Canonical raw/unadjusted OHLCV: open/high/low/close/volume. FinMind TaiwanStockPrice primary; Yahoo fallback. adjusted_close equals close for FinMind and is not used as canonical raw price.\n")
print(json.dumps(qc,indent=2,ensure_ascii=False))
