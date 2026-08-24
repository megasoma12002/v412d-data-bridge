#!/usr/bin/env python3
"""Build a separate corporate-action-adjusted layer; raw OHLCV remains canonical."""
import csv, json, urllib.parse, urllib.request
from pathlib import Path

STOCKS="2880 2886 2892 5880 2801 2834 2884 2885 2890 2891 2881 2882".split()
BASE="https://api.finmindtrade.com/api/v4/data"

def get(dataset,sid=None):
    q={"dataset":dataset,"start_date":"2004-01-01","end_date":"2026-08-24"}
    if sid:q["data_id"]=sid
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(q),headers={"User-Agent":"v412e0-research/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:obj=json.load(r)
    if obj.get("status")!=200:raise RuntimeError(f"{dataset} {sid}: {obj}")
    return obj.get("data",[])

def main():
    out=Path("artifact");raw=out/"v412e0_12stocks_history_raw.csv"
    events={s:[] for s in STOCKS};actions=[]
    for sid in STOCKS:
        for r in get("TaiwanStockDividendResult",sid):
            before=float(r["before_price"]);after=float(r["after_price"])
            if before>0 and after>0:
                events[sid].append((r["date"],after/before,"dividend_or_rights"));actions.append([sid,r["date"],"dividend_or_rights",before,after,after/before,r.get("stock_and_cache_dividend"),r.get("stock_or_cache_dividend")])
        for r in get("TaiwanStockCapitalReductionReferencePrice",sid):
            before=float(r["ClosingPriceonTheLastTradingDay"]);after=float(r["OpeningReferencePrice"])
            if before>0 and after>0:
                events[sid].append((r["date"],after/before,"capital_reduction"));actions.append([sid,r["date"],"capital_reduction",before,after,after/before,"",r.get("ReasonforCapitalReduction")])
    for r in get("TaiwanStockSplitPrice"):
        sid=str(r.get("stock_id"))
        if sid not in events:continue
        before=float(r["before_price"]);after=float(r["after_price"])
        if before>0 and after>0:
            events[sid].append((r["date"],after/before,"split_or_par_change"));actions.append([sid,r["date"],"split_or_par_change",before,after,after/before,"",r.get("type")])
    for sid in events:events[sid].sort()
    adjusted=[]
    with raw.open(encoding="utf-8") as h:
        for r in csv.DictReader(h):
            sid=r["code"];factor=1.0
            for event_date,event_factor,_ in events[sid]:
                if event_date>r["date"]:factor*=event_factor
            adjusted.append([sid,r["date"],*[float(r[c])*factor for c in ("open","high","low","close")],r["volume"],factor])
    adjusted.sort(key=lambda x:(x[1],x[0]));actions.sort(key=lambda x:(x[1],x[0]))
    with (out/"v412e0_12stocks_corporate_action_adjusted.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.writer(h);w.writerow("code date adjusted_open adjusted_high adjusted_low adjusted_close volume backward_adjustment_factor".split());w.writerows(adjusted)
    with (out/"v412e0_corporate_actions.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.writer(h);w.writerow("code date action_type before_price after_price factor distribution detail".split());w.writerows(actions)
    summary={"status":"PASS","method":"raw price multiplied by future after_price/before_price event factors; event day remains raw","execution_use":"NEVER; use raw OHLCV","rows":len(adjusted),"events":len(actions),"event_count_by_stock":{s:len(events[s]) for s in STOCKS},"limitations":["research-grade reconstructed adjusted layer, not an exchange total-return index","historical router classification remains unverified"]}
    (out/"v412e0_adjusted_qc.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
