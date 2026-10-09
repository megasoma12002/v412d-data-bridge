#!/usr/bin/env python3
"""Capture the public statutory dividend and securities-delivery announcement registers."""
import argparse
import os
import time
import csv
import gzip
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from lxml import html
from dd_switch_mops_evidence import day

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'repro/dd-switch-full-history-audit'
DEST=OUT/'sources/mops_statutory'
ENDPOINTS={'t59sb09':'發行新股、公司債暨有價證券交付或發放股利前辦理之公告',
           't108sb19':'決定分配股息及紅利或其他利益之基準日公告'}


def text_tree(raw):
    tree=html.fromstring(raw.decode('utf-8'))
    for e in tree.xpath('//script|//style'):e.drop_tree()
    return tree,re.sub(r'\s+','',tree.text_content())


def fetch(item,cache,timeout):
    old=cache.get(item['id'])
    if old and old['status'] in ('CAPTURED','VALID_EMPTY'):
        packed=(ROOT/old['path']).read_bytes();raw=gzip.decompress(packed)
        if hashlib.sha256(raw).hexdigest()!=old['response_sha256'] or hashlib.sha256(packed).hexdigest()!=old['compressed_sha256']:raise ValueError('Statutory cache hash mismatch')
        return old,raw
    time.sleep(float(os.environ.get('MOPS_REQUEST_INTERVAL_SECONDS','0')))
    r=subprocess.run(['curl','-L','--max-time',str(timeout),'-sS','-w','\n%{http_code}',item['url']],capture_output=True)
    raw,_,status=r.stdout.rpartition(b'\n');f=DEST/(item['id']+'.html.gz');f.write_bytes(gzip.compress(raw,mtime=0))
    meta=dict(item,path=str(f.relative_to(ROOT)),response_sha256=hashlib.sha256(raw).hexdigest(),compressed_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),http_status=status.decode(),retrieved_at=datetime.now(timezone.utc).isoformat(),status='UNAVAILABLE')
    try:
        if r.returncode or status!=b'200':raise ValueError('curl/HTTP error: '+r.stderr.decode(errors='replace')[:200])
        tree,text=text_tree(raw)
        if 'FORSECURITY' in text or '公開資訊觀測站' not in text:raise ValueError('Unrelated/security response')
        if item['kind']=='STATUTORY_INDEX':
            if '查無所需資料' in text and not tree.xpath('//input[@onclick]'):meta['status']='VALID_EMPTY'
            elif ENDPOINTS[item['endpoint']] in text and tree.xpath('//input[@onclick]'):meta['status']='CAPTURED'
            elif '查無所需資料' in text and ENDPOINTS[item['endpoint']] in text:meta['status']='VALID_EMPTY'
            else:raise ValueError('Unvalidated statutory index')
        elif item['code'] in text and '公司代號' in text and '主旨' in text and ('公告內容' in text or '公告事項' in text):
            meta['status']='CAPTURED'
        elif '公告' in text and ('公司負其全責' in text or '公告事項' in text):meta['status']='CAPTURED'
        else:raise ValueError('Unvalidated statutory detail')
    except Exception as error:meta['error']=str(error)
    return meta,raw


def indexes(codes):
    for endpoint in ENDPOINTS:
        for code in sorted(codes):
            for year in range(2010,2027):
                params=dict(firstin='true',TYPEK='sii',co_id=code,year=year-1911,step=1)
                yield dict(id=f'{endpoint}_{code}_{year}_index',endpoint=endpoint,code=code,year=year,kind='STATUTORY_INDEX',url='https://mopsov.twse.com.tw/mops/web/ajax_'+endpoint+'?'+urlencode(params))


def details(meta,raw):
    if meta['status']!='CAPTURED':return []
    tree,_=text_tree(raw);result=[]
    for form in tree.xpath('//form'):
        defaults={e.get('name'):e.get('value') or '' for e in form.xpath('.//input[@type="hidden"]')}
        for tr in form.xpath('.//tr'):
            buttons=tr.xpath('.//input[@onclick]')
            if not buttons:continue
            inputs=dict(re.findall(r'\.([A-Za-z_0-9]+)\.value="([^"]*)"',buttons[0].get('onclick')))
            if 'DATE1' not in inputs:continue
            cells=[re.sub(r'\s+','',e.text_content()) for e in tr.xpath('./td')]
            if not cells:continue
            announcement_day=day(cells[0])
            title=cells[1] if meta['endpoint']=='t59sb09' else cells[2]
            params=dict(defaults,**inputs)
            target=form.get('action')
            seq=inputs.get('SKEY',inputs.get('SEQ_NO',''))
            identity=f"{meta['endpoint']}_{meta['code']}_{announcement_day.replace('-','')}_{inputs['DATE1']}_{seq}"
            result.append(dict(id=identity,endpoint=meta['endpoint'],code=meta['code'],year=meta['year'],kind='STATUTORY_DETAIL',title=title,
                               announcement_date=announcement_day,request_record_date=inputs['DATE1'],availability_precision='DATE_ONLY',
                               index_url=meta['url'],index_path=meta['path'],
                               amended_cash_payment_date=cells[-1] if meta['endpoint']=='t108sb19' else '',
                               url='https://mopsov.twse.com.tw'+target+'?'+urlencode(params)))
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=8);parser.add_argument('--timeout',type=int,default=40);args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True);path=DEST/'manifest.json'
    cache={r['id']:r for r in json.loads(path.read_text())} if path.exists() else {}
    with (ROOT/'data/dividend_events/e22_dividend_events.csv').open() as f:codes={r['code'] for r in csv.DictReader(f)}-{'0050'}
    entries=[];next_items=[]
    def save():
        merged=dict(cache);merged.update({r['id']:r for r in entries})
        path.write_text(json.dumps(sorted(merged.values(),key=lambda r:r['id']),indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i,(meta,raw) in enumerate(pool.map(lambda x:fetch(x,cache,args.timeout),indexes(codes)),1):
            entries.append(meta);next_items.extend(details(meta,raw));save();print('INDEX',i,meta['id'],meta['status'],flush=True)
    unique={r['id']:r for r in next_items}
    print('INDEXES_COMPLETE',len(entries),'DETAILS',len(unique),flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i,(meta,raw) in enumerate(pool.map(lambda x:fetch(x,cache,args.timeout),unique.values()),1):
            entries.append(meta);save();print('DETAIL',i,meta['id'],meta['status'],meta['title'],flush=True)
    print('COMPLETE',len(entries),flush=True)


if __name__=='__main__':main()
