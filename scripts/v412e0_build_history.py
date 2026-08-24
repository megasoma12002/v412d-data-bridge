#!/usr/bin/env python3
"""Build V4.12-E0 raw OHLCV history and point-in-time eligibility metadata."""
import argparse, csv, json, math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

TARGETS={"2880":"R1","2886":"R1","2892":"R1","5880":"R1","2801":"R2","2834":"R2",
         "2884":"R3","2885":"R3","2890":"R3","2891":"R3","2881":"R4","2882":"R4"}
NAMES={"2880":"華南金","2886":"兆豐金","2892":"第一金","5880":"合庫金","2801":"彰銀","2834":"臺企銀",
       "2884":"玉山金","2885":"元大金","2890":"永豐金","2891":"中信金","2881":"富邦金","2882":"國泰金"}

def dt(v):
    for f in ("%Y%m%d","%Y-%m-%d","%Y/%m/%d"):
        try:return datetime.strptime(v.strip(),f).date()
        except ValueError:pass
    raise ValueError(v)
def num(v):
    x=float(v.strip().replace(",",""))
    if not math.isfinite(x):raise ValueError(v)
    return x

def main():
    p=argparse.ArgumentParser();p.add_argument("--input-dir",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True);p.add_argument("--start-year",type=int,default=2004);a=p.parse_args()
    data={s:{} for s in TARGETS}; skipped=defaultdict(int); conflicts=[]; files=0
    for f in sorted(a.input_dir.rglob("*.csv")):
        files+=1
        with f.open(encoding="utf-8-sig",newline="") as h:
            rd=csv.DictReader(h); names={x.strip().lower().lstrip("\ufeff"):x for x in (rd.fieldnames or [])}
            if not {"date","code","open","high","low","close","volume"}<=set(names):continue
            for raw in rd:
                s=str(raw[names["code"]]).strip()
                if s not in TARGETS:continue
                d=dt(str(raw[names["date"]]))
                if d.year<a.start_year:continue
                try:r=(d,num(str(raw[names["open"]])),num(str(raw[names["high"]])),num(str(raw[names["low"]])),num(str(raw[names["close"]])),num(str(raw[names["volume"]])))
                except ValueError:skipped[s]+=1;continue
                if d in data[s] and data[s][d]!=r:conflicts.append(f"{s}:{d}")
                data[s][d]=r
    if conflicts:raise SystemExit("conflicts: "+",".join(conflicts[:20]))
    a.output_dir.mkdir(parents=True,exist_ok=True); summary={"status":"PASS","source_files":files,"requested_start_year":a.start_year,"stocks":{}}
    combined=[]; universe=[]
    for s,router in TARGETS.items():
        rows=sorted(data[s].values()); fn=a.output_dir/f"{s}_history_raw.csv"
        with fn.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h);w.writerow(["date","open","high","low","close","volume"]);w.writerows(rows)
        violations=sum(r[2]<max(r[1],r[3],r[4]) or r[3]>min(r[1],r[2],r[4]) or r[5]<0 for r in rows)
        duplicate=len(rows)-len({r[0] for r in rows}); ok=bool(rows) and violations==0 and duplicate==0 and rows[-1][0].year==2026
        if not ok:summary["status"]="FAIL"
        summary["stocks"][s]={"name":NAMES[s],"router_current_research":router,"first_date":rows[0][0].isoformat() if rows else None,"last_date":rows[-1][0].isoformat() if rows else None,"rows":len(rows),"skipped_missing":skipped[s],"violations":violations,"duplicate_dates":duplicate,"status":"PASS" if ok else "FAIL"}
        for i,r in enumerate(rows):
            combined.append((s,*r[0:]))
            universe.append((r[0],s,NAMES[s],router,1,int(i>=252),rows[0][0],"current-research classification; historical classification not yet verified"))
    combined.sort(key=lambda r:(r[1],r[0])); universe.sort()
    with (a.output_dir/"v412e0_12stocks_history_raw.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h);w.writerow(["code","date","open","high","low","close","volume"]);w.writerows(combined)
    with (a.output_dir/"v412e0_point_in_time_universe.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h);w.writerow(["date","code","name","router","listed_and_trading","indicator_ready_252d","first_observed_date","classification_note"]);w.writerows(universe)
    summary["combined_rows"]=len(combined);(a.output_dir/"v412e0_qc_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2));raise SystemExit(0 if summary["status"]=="PASS" else 1)
if __name__=="__main__":main()
