#!/usr/bin/env python3
"""Archive exact gap and adjacent raw quotes without modifying live inputs."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from threading import Event
import urllib.error
import urllib.parse
import urllib.request
from dd_switch_full_history_sources import ROOT, CODES

OUT=ROOT/'repro/dd-switch-full-history-audit'

def main():
    stop=Event()
    private=['2801','2834','2881','2882','2884','2885','2890','2891']
    jobs=[(c,'2023-05-24','2023-05-26') for c in CODES]
    jobs += [(c,s,e) for c in private for s,e in [('2025-02-05','2025-02-07'),('2026-05-27','2026-05-29')]]
    def fetch(job):
        code,start,end=job
        path=OUT/'sources'/f'gap_{code}_{start}_{end}.json'
        url='https://api.finmindtrade.com/api/v4/data?'+urllib.parse.urlencode(dict(dataset='TaiwanStockPrice',data_id=code,start_date=start,end_date=end))
        rec=dict(code=code,start=start,end=end,url=url,path=str(path.relative_to(ROOT)),source_class='SECONDARY_FINMIND_RAW_CURRENT_VINTAGE',fetched_at=datetime.now(timezone.utc).isoformat())
        try:
            if path.exists():raw=path.read_bytes()
            else:
                if stop.is_set():return dict(rec,status='NOT_REQUESTED_QUOTA_STOP')
                with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'dd-switch-gap-audit/1.0'}),timeout=25) as r:raw=r.read()
            obj=json.loads(raw)
            if obj.get('status')!=200 or not isinstance(obj.get('data'),list):raise ValueError(str(obj.get('msg')))
            path.write_bytes(raw)
            rec.update(status='FETCHED',rows=len(obj['data']),sha256=hashlib.sha256(raw).hexdigest())
        except urllib.error.HTTPError as e:
            if e.code in (402,429):stop.set()
            rec.update(status='UNAVAILABLE',error=str(e))
        except Exception as e:rec.update(status='UNAVAILABLE',error=str(e))
        return rec
    records=[]
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        for r in pool.map(fetch,jobs):
            records.append(r)
            print(r['code'],r['start'],r['status'],r.get('rows',''),flush=True)
    (OUT/'gap_source_manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print('GAP_SOURCES_FINISHED',sum(r['status']=='FETCHED' for r in records),len(records),flush=True)

if __name__=='__main__':main()
