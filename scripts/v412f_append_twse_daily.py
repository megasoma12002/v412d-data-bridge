#!/usr/bin/env python3
"""Append recent official TWSE daily OHLCV to the canonical raw history."""
import argparse,csv,json,time,urllib.parse,urllib.request
from datetime import date,timedelta
from pathlib import Path

TARGETS=set("2880 2886 2892 5880 2801 2834 2884 2885 2890 2891 2881 2882".split())
URL="https://www.twse.com.tw/exchangeReport/MI_INDEX"

def number(x):
    s=str(x).replace(",","").replace("X","").strip()
    if s in ("","--","---"): return None
    return float(s)

def fetch(day):
    q=urllib.parse.urlencode({"response":"json","date":day.strftime('%Y%m%d'),"type":"ALLBUT0999"})
    req=urllib.request.Request(URL+"?"+q,headers={"User-Agent":"v412f-forward-paper/1.0"})
    with urllib.request.urlopen(req,timeout=60) as r: obj=json.load(r)
    datasets=[]
    if isinstance(obj.get("tables"),list):
        datasets.extend((t.get("fields",[]),t.get("data",[])) for t in obj["tables"])
    for k,v in obj.items():
        if k.startswith("fields") and isinstance(v,list): datasets.append((v,obj.get(k.replace("fields","data"),[])))
    for field_values,data in datasets:
        fields=[str(x).strip() for x in field_values]
        if "證券代號" not in fields or "開盤價" not in fields: continue
        ix={name:fields.index(name) for name in ("證券代號","成交股數","開盤價","最高價","最低價","收盤價")}
        out=[]
        for row in data:
            sid=str(row[ix["證券代號"]]).strip()
            if sid not in TARGETS: continue
            vals=[number(row[ix[x]]) for x in ("開盤價","最高價","最低價","收盤價","成交股數")]
            if any(x is None for x in vals): continue
            o,h,l,c,v=vals
            if h<max(o,l,c) or l>min(o,h,c) or v<0: raise RuntimeError(f"invalid TWSE row {day} {sid}")
            out.append((sid,day.isoformat(),o,h,l,c,v))
        return out
    return []

def main():
    p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); p.add_argument('--lookback-days',type=int,default=14); a=p.parse_args(); path=Path(a.raw)
    with path.open(encoding='utf-8') as f: existing={(r['code'],r['date']):(r['code'],r['date'],float(r['open']),float(r['high']),float(r['low']),float(r['close']),float(r['volume'])) for r in csv.DictReader(f)}
    added=0; errors=[]
    for n in range(a.lookback_days,-1,-1):
        day=date.today()-timedelta(days=n)
        if day.weekday()>=5: continue
        try:
            for row in fetch(day):
                key=row[:2]; added += int(key not in existing or existing[key]!=row); existing[key]=row
            time.sleep(.15)
        except Exception as ex: errors.append(f"{day}:{type(ex).__name__}:{ex}")
    rows=sorted(existing.values(),key=lambda x:(x[1],x[0]))
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f); w.writerow(['code','date','open','high','low','close','volume']); w.writerows(rows)
    latest=max(r[1] for r in rows); summary={'status':'PASS','rows':len(rows),'changed_rows':added,'latest_date':latest,'nonfatal_fetch_errors':errors}
    Path(path.parent/'v412f_twse_append_qc.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__': main()
