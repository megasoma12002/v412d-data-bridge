#!/usr/bin/env python3
"""Capture cached primary filings for the 24 subscription events and one dividend discrepancy."""
import sys,csv,re,json,gzip,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from lxml import html
def main():
    root=Path(__file__).resolve().parents[1]; out=root/'repro/dd-switch-full-history-audit/sources/mops_actions';out.mkdir(exist_ok=True)
    rows=list(csv.DictReader(open(root/'repro/dd-switch-full-history-audit/mops_action_field_check.csv')))
    requests=[dict(code=r['code'],year=int(r['primary_reported_at'][:4]),month=r['primary_reported_at'][5:7]) for r in rows]
    requests.append(dict(code='3045',year=2025,month='06'))
    requests.extend([dict(code='2884',year=2011,month='07'), dict(code='2884',year=2014,month='03')])
    manifest=[]
    cache={entry['id']: entry for entry in json.loads((out/'manifest.json').read_text())} if (out/'manifest.json').exists() else {}
    def fetch(item):
     cached=cache.get(item['id'])
     if cached and cached['status']=='CAPTURED':
      packed=(root/cached['path']).read_bytes();raw=gzip.decompress(packed)
      if hashlib.sha256(raw).hexdigest()!=cached['response_sha256'] or hashlib.sha256(packed).hexdigest()!=cached['compressed_sha256']:
       raise ValueError('Cached action response hash mismatch')
      return cached,raw.decode('utf-8')
     url=item['url'];p=subprocess.run(['curl','-L','--max-time','35','-sS','-w','\n%{http_code}',url],capture_output=True);raw,_,status=p.stdout.rpartition(b'\n');path=out/(item['id']+'.html.gz');path.write_bytes(gzip.compress(raw,mtime=0));entry=dict(**item,path=str(path.relative_to(root)),response_sha256=hashlib.sha256(raw).hexdigest(),compressed_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),retrieved_at=datetime.now(timezone.utc).isoformat(),http_status=status.decode(),status='CAPTURED' if status==b'200' and p.returncode==0 and b'FOR SECURITY' not in raw and '本資料由' in raw.decode('utf-8',errors='replace') else 'UNAVAILABLE');return entry,raw.decode('utf-8',errors='replace')
    items=[]
    for x in requests:
     params=dict(firstin='true',TYPEK='all',co_id=x['code'],year=x['year']-1911,month=x['month'],step=1,isnew='false')
     items.append(dict(**x,id=f"{x['code']}_{x['year']}{x['month']}_index",kind='MONTH_INDEX',url='https://mopsov.twse.com.tw/mops/web/ajax_t05st01?'+urlencode(params)))
    details=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
     for meta,text in pool.map(fetch,items):
      manifest.append(meta)
      if meta['status']!='CAPTURED':raise ValueError('Unavailable month index: '+meta['id'])
      tree=html.fromstring(text)
      for tr in tree.xpath('//tr'):
       pre=tr.xpath('.//pre');buttons=tr.xpath('.//input[@onclick]')
       if not pre or not buttons:continue
       title=''.join(pre[0].itertext()).strip().replace('\n','')
       if meta['code']=='3045':eligible=('除息' in title or '股利' in title) and '子公司' not in title
       else:eligible=('現金增資' in title or '現增' in title) and '子公司' not in title and not title.startswith('代')
       if not eligible:continue
       attrs=dict(re.findall(r"\.([A-Za-z_]+)\.value='([^']*)'",buttons[0].get('onclick')))
       params=dict(firstin='true',step=2,isnew='false',**attrs)
       id=f"{meta['code']}_{attrs['spoke_date']}_{attrs['spoke_time']}_{attrs['seq_no']}"
       details.append(dict(code=meta['code'],year=meta['year'],month=meta['month'],id=id,kind='DETAIL',title=title,url='https://mopsov.twse.com.tw/mops/web/ajax_t05st01?'+urlencode(params)))
      print(meta['id'],meta['status'],flush=True)
      (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=4) as pool:
     for meta,text in pool.map(fetch,details):
      manifest.append(meta); print(meta['id'],meta['status'],meta['title'],flush=True)
      (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('total',len(manifest),'details',len(details))


if __name__ == '__main__':
    main()
