#!/usr/bin/env python3
"""Read-only alternate evidence: Yahoo history and official latest TWSE prices."""
import argparse
import concurrent.futures
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from dd_switch_full_history_sources import CODES, ROOT

def download(out,code):
    symbol='^TWII' if code=='TAIEX' else code+'.TW'
    start=int(datetime(2010,1,1,tzinfo=timezone.utc).timestamp())
    end=int(datetime(2026,10,9,tzinfo=ZoneInfo('Asia/Taipei')).timestamp())
    url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol,safe='')+'?'+urllib.parse.urlencode(dict(period1=start,period2=end,interval='1d',events='div,splits',includeAdjustedClose='true'))
    path=out/'sources'/('yahoo_'+code+'.json');record=dict(code=code,url=url,source_class='SECONDARY_YAHOO_CURRENT_HISTORY_NOT_VINTAGE',fetched_at=datetime.now(timezone.utc).isoformat())
    try:
        if path.exists():raw=path.read_bytes()
        else:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40) as response:raw=response.read()
            obj=json.loads(raw)
            if obj['chart'].get('error') or not obj['chart'].get('result'):raise ValueError('Yahoo response error')
            path.write_bytes(raw)
        obj=json.loads(raw);result=obj['chart']['result'][0]
        record.update(status='FETCHED',path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),rows=len(result.get('timestamp',[])))
    except Exception as error:record.update(status='UNAVAILABLE',error=str(error))
    return record

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-full-history-audit');parser.add_argument('--workers',type=int,default=3);args=parser.parse_args();out=args.out.resolve()
    if (ROOT/'repro').resolve() not in out.parents:raise ValueError('Research only')
    (out/'sources').mkdir(exist_ok=True,parents=True)
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        for record in executor.map(lambda c:download(out,c),CODES):
            records.append(record);(out/'alternate_source_manifest.json').write_text(json.dumps(records,indent=2));print(record['code'],record['status'],record.get('rows'),flush=True)
    url='https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL';path=out/'sources/twse_latest_stock_day_all.json'
    record=dict(url=url,source_class='PRIMARY_TWSE_LATEST_ONLY',fetched_at=datetime.now(timezone.utc).isoformat())
    try:
        with urllib.request.urlopen(url,timeout=30) as response:raw=response.read()
        obj=json.loads(raw);path.write_bytes(raw);record.update(status='FETCHED',rows=len(obj),sha256=hashlib.sha256(raw).hexdigest(),path=str(path.relative_to(ROOT)))
    except Exception as error:record.update(status='UNAVAILABLE',error=str(error))
    records.append(record);(out/'alternate_source_manifest.json').write_text(json.dumps(records,indent=2));print('ALTERNATE_SOURCES_COMPLETE',flush=True)

if __name__=='__main__':main()
