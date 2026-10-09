#!/usr/bin/env python3
"""Archive independent historical observations for a read-only research audit.

Never writes canonical inputs. FinMind is secondary evidence, not an official
exchange calendar or a publication-vintage archive. HTTP failures stay explicit.
"""
import argparse
import concurrent.futures
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODES = ['TAIEX','0050','2412','2880','2886','2892','3045','4904','5880','00631L',
         '2801','2834','2881','2882','2884','2885','2890','2891']

def fetch_one(out, code, year, quota_stop=None):
    path = out / 'sources' / f'{code}_{year}.json'
    start = f'{year}-01-01'
    end = '2026-10-08' if year == 2026 else f'{year}-12-31'
    url = 'https://api.finmindtrade.com/api/v4/data?' + urllib.parse.urlencode(
        dict(dataset='TaiwanStockPrice', data_id=code, start_date=start, end_date=end))
    record = dict(code=code, year=year, url=url, fetched_at=datetime.now(timezone.utc).isoformat(),
                  source_class='SECONDARY_FINMIND_REDOWNLOAD_NOT_VINTAGE', path=str(path.relative_to(ROOT)))
    try:
        if path.exists():
            raw = path.read_bytes()
            record['cached'] = True
        else:
            if quota_stop is not None and quota_stop.is_set():
                return {**record, 'status':'NOT_REQUESTED_QUOTA_STOP'}
            req = urllib.request.Request(url, headers={'User-Agent':'dd-switch-historical-audit/1.0'})
            with urllib.request.urlopen(req, timeout=35) as response:
                raw = response.read()
            payload = json.loads(raw)
            if payload.get('status') != 200:
                raise ValueError('Provider status: ' + str(payload.get('msg')))
            path.write_bytes(raw)
        payload = json.loads(raw)
        if payload.get('status') != 200:
            raise ValueError('Invalid cached provider response')
        record.update(status='FETCHED', sha256=hashlib.sha256(raw).hexdigest(), rows=len(payload.get('data',[])))
    except urllib.error.HTTPError as error:
        record.update(status='UNAVAILABLE', http_status=error.code, error=error.read().decode(errors='replace')[:500])
        if quota_stop is not None and error.code in (402,429):
            quota_stop.set()
    except Exception as error:
        record.update(status='UNAVAILABLE', error=str(error))
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'repro/dd-switch-full-history-audit')
    parser.add_argument('--codes', nargs='+', default=CODES)
    parser.add_argument('--years', type=int, nargs='+', default=list(range(2011,2027)), help='Explicit historical years; default preserves the original audit range')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--offline', action='store_true', help='Only archive existing responses and retain access failures')
    args = parser.parse_args()
    out = args.out.resolve()
    if (ROOT/'repro').resolve() not in out.parents:
        raise ValueError('Research output only')
    (out/'sources').mkdir(parents=True, exist_ok=True)
    jobs = [(code,year) for code in args.codes for year in args.years
            if not (code=='00631L' and year<2014)]
    records = []
    previous = {}
    if (out/'source_manifest.json').exists():
        previous = {(r['code'],r['year']):r for r in json.loads((out/'source_manifest.json').read_text())}
    if args.offline:
        for code,year in jobs:
            if (out/'sources'/f'{code}_{year}.json').exists():
                record=fetch_one(out,code,year)
            else:
                record=previous.get((code,year),dict(code=code,year=year,status='NOT_REQUESTED_QUOTA_STOP'))
            records.append(record)
        (out/'source_manifest.json').write_text(json.dumps(sorted(records,key=lambda r:(r['code'],r['year'])),indent=2))
        print('OFFLINE_SOURCE_INVENTORY',len(records),flush=True)
        return
    quota_stop = threading.Event()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_one,out,code,year,quota_stop) for code,year in jobs]
        for future in concurrent.futures.as_completed(futures):
            record = future.result()
            records.append(record)
            (out/'source_manifest.json').write_text(json.dumps(sorted(records,key=lambda r:(r['code'],r['year'])),indent=2))
            print(record['code'],record['year'],record['status'],record.get('rows',record.get('http_status')),flush=True)
    print('SOURCE_AUDIT_COMPLETE',len(records),'unavailable',sum(r['status']!='FETCHED' for r in records),flush=True)

if __name__ == '__main__':
    main()
