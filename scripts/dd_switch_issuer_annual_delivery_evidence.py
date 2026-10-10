#!/usr/bin/env python3
"""Verify retrospective issuer annual-report delivery evidence, never publication vintage."""
import csv, gzip, hashlib, json, re, unicodedata
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit, urljoin
import fitz
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'repro/dd-switch-full-history-audit'
def compact(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))
def parse_tbb(pages, event, official_index_verified=False):
    text=compact(''.join(pages))
    if event['code']!='2834' or '臺灣中小企業銀行' not in text[:1500] or ('股票代號:2834' not in text[:1500] and not (official_index_verified and 'www.tbb.com.tw' in text[:1500])):
        return None
    declared_code=re.search(r'股票代號:(\d{4})',text[:1500])
    if declared_code and declared_code[1]!='2834':return None
    fiscal=re.fullmatch(r'(\d+)年',event['fiscal_year'])
    if not fiscal:return None
    fiscal=fiscal[1]
    # Completed allocation in the shareholder letter; proposed next-year allocations do not qualify.
    rate=re.search(r'發放(?:'+fiscal+r'|前\('+fiscal+r'\))年度股票股利每股([\d.]+)元',text)
    if not rate or abs(Decimal(rate[1])-Decimal(event['stock_dividend']))>Decimal('0.00000001'):
        return None
    for i,page in enumerate(pages):
        s=compact(page)
        if '為配合'+fiscal+'年度盈餘分配' not in s:continue
        m=re.search(r'於(\d{2,3})年(\d{1,2})月(\d{1,2})日撥交股票予股東及新股上市買賣',s)
        if not m:continue
        date=f'{int(m[1])+1911:04d}-{int(m[2]):02d}-{int(m[3]):02d}'
        # Avoid linking the adjacent year's execution table to this allocation.
        if int(m[1])!=int(fiscal)+1:continue
        return dict(payment_date=date,delivery_page=i+1,delivery_clause=m[0],rate_clause=rate[0],amount_matches=True,
                    retrospective=True,publication_vintage_certified=False,holder_receipt_certified=False)
    return None

def load_annual_delivery_facts():
    manifest=json.loads((OUT/'sources/targeted_issuers/manifest.json').read_text())
    byid={r['id']:r for r in manifest}
    ledger=list(csv.DictReader((ROOT/'data/dividend_events/e22_dividend_events.csv').open()))
    reports=[r for r in manifest if r['id']=='settlement_tbb_2012_annual_report_single_retry' or r['id'].startswith('settlement_tbb_') and r['id'].endswith('_observed_annual')]
    facts=[];review=[]
    for r in reports:
        if r['status']!='RESPONSE_SAVED_NEEDS_VALIDATION':
            review.append(dict(source_id=r['id'],status=r['status']));continue
        packed=(ROOT/r['path']).read_bytes();raw=gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest()==r['compressed_sha256'],r['id']
        assert hashlib.sha256(raw).hexdigest()==r['response_sha256'],r['id']
        assert urlsplit(r['url']).netloc=='ir.tbb.com.tw',r['id']
        if r.get('index_id'):
            index=byid[r['index_id']]; ip=(ROOT/index['path']).read_bytes(); ir=gzip.decompress(ip)
            assert index['status']=='RESPONSE_SAVED_NEEDS_VALIDATION'
            assert urlsplit(index['url']).netloc=='ir.tbb.com.tw'
            assert urlsplit(index['url']).path=='/financial/annual-reports'
            assert hashlib.sha256(ip).hexdigest()==index['compressed_sha256']
            assert hashlib.sha256(ir).hexdigest()==r['index_sha256']==index['response_sha256']
            d=html.fromstring(ir.decode('utf-8'))
            label=str(r['report_year'])+'年報'
            links=[urljoin(index['url'],a) for e in d.xpath('//p') if e.text==label for a in e.getparent().xpath('.//a/@href')]
            assert r['url'] in links,r['id']
        else:
            assert urlsplit(r['url']).path.endswith('/2012公司年報.pdf') or '2012%E5%85%AC%E5%8F%B8%E5%B9%B4%E5%A0%B1.pdf' in r['url']
        if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-1024:]:
            review.append(dict(source_id=r['id'],status='NOT_PDF'));continue
        try:
            doc=fitz.open(stream=raw,filetype='pdf');pages=[p.get_text() for p in doc]
        except Exception as e:
            review.append(dict(source_id=r['id'],status='PDF_PARSE_FAILED',error=str(e)));continue
        found=[]
        for event in ledger:
            if event['code']!='2834' or Decimal(event['stock_dividend'])<=0:continue
            fact=parse_tbb(pages,event,official_index_verified=bool(r.get('index_id')))
            if fact:
                fact.update(code=event['code'],leg='stock',ex_date=event['stock_ex_date'],fiscal_year=event['fiscal_year'],
                    source_id=r['id'],url=r['url'],response_sha256=r['response_sha256'],ledger_payment_date=event['stock_payment_date'],
                    ledger_sha256=hashlib.sha256((ROOT/'data/dividend_events/e22_dividend_events.csv').read_bytes()).hexdigest(),
                    index_id=r.get('index_id',''),index_sha256=r.get('index_sha256',''))
                facts.append(fact);found.append(event['stock_ex_date'])
        review.append(dict(source_id=r['id'],status='RETROSPECTIVE_GENERAL_DELIVERY_SUPPORTED' if found else 'NO_QUALIFYING_GENERAL_DELIVERY',matched_ex_dates=found,pages=len(pages)))
    (OUT/'issuer_annual_delivery_facts.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    (OUT/'issuer_annual_delivery_validation.json').write_text(json.dumps(dict(reports=review,facts=len(facts),publication_vintage_certified=False,backtest_permission=False),ensure_ascii=False,indent=2)+'\n')
    return facts
if __name__=='__main__':
    print(json.dumps(load_annual_delivery_facts(),ensure_ascii=False,indent=2))
