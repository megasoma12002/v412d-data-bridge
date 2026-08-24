#!/usr/bin/env python3
"""Fetch a separate adjusted-price layer from FinMind; never used as execution OHLCV."""
import csv, json, time, urllib.parse, urllib.request
from pathlib import Path

STOCKS="2880 2886 2892 5880 2801 2834 2884 2885 2890 2891 2881 2882".split()
BASE="https://api.finmindtrade.com/api/v4/data"

def get(dataset,sid):
    q=urllib.parse.urlencode({"dataset":dataset,"data_id":sid,"start_date":"2004-01-01","end_date":"2026-12-31"})
    with urllib.request.urlopen(BASE+"?"+q,timeout=90) as r: obj=json.load(r)
    if obj.get("status")!=200: raise RuntimeError(f"{dataset} {sid}: {obj}")
    return obj.get("data",[])

def main():
    out=Path("artifact");out.mkdir(exist_ok=True); all_adj=[]; all_div=[]; summary={"status":"PASS","stocks":{}}
    for sid in STOCKS:
        adj=get("TaiwanStockPriceAdj",sid);time.sleep(.25)
        div=get("TaiwanStockDividendResult",sid);time.sleep(.25)
        for r in adj: all_adj.append([sid,r.get("date"),r.get("open"),r.get("max"),r.get("min"),r.get("close"),r.get("Trading_Volume")])
        for r in div: all_div.append([sid,r.get("date"),r.get("before_price"),r.get("after_price"),r.get("stock_and_cache_dividend"),r.get("stock_or_cache_dividend"),r.get("reference_price")])
        summary["stocks"][sid]={"adjusted_rows":len(adj),"corporate_action_rows":len(div),"adjusted_first":adj[0]["date"] if adj else None,"adjusted_last":adj[-1]["date"] if adj else None}
        if not adj:summary["status"]="FAIL"
    all_adj.sort(key=lambda x:(x[1],x[0]));all_div.sort(key=lambda x:(x[1] or "",x[0]))
    with (out/"v412e0_12stocks_adjusted_prices.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.writer(h);w.writerow("code date adjusted_open adjusted_high adjusted_low adjusted_close volume".split());w.writerows(all_adj)
    with (out/"v412e0_corporate_actions.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.writer(h);w.writerow("code date before_price after_price stock_and_cash_dividend action_type reference_price".split());w.writerows(all_div)
    (out/"v412e0_adjusted_qc.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2));raise SystemExit(0 if summary["status"]=="PASS" else 1)
if __name__=="__main__":main()
