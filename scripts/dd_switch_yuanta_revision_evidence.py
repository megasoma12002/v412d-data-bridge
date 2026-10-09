#!/usr/bin/env python3
"""Normalize hashed issuer PDF notices; estimated and final fields stay separate."""
import csv, gzip, hashlib, json, re, subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'repro/dd-switch-full-history-audit'
DATE=r'\d{2,4}年\d{1,2}月\d{1,2}日'

def iso(value):
    y,m,d=map(int,re.findall(r'\d+',value));return date(y+1911 if y<1911 else y,m,d).isoformat()

def one_date(text,label):
    found={iso(m[1]) for m in re.finditer(re.escape(label)+r'[:：]('+DATE+r')',text)}
    if len(found)!=1:raise ValueError('Missing or ambiguous '+label)
    return found.pop()

def parse_notice(text,meta):
    compact=re.sub(r'\s+','',text)
    title = re.sub(r'\s+', '', meta['title'])
    code_heading = compact.split('中華民國', 1)[0]
    code_matches = bool(re.search(r'交易證券代號[交易證券代號名稱:：]{0,40}0050(?!\d)', code_heading))
    # Older issuer PDFs omit the trading code: require the unique legal fund
    # name in the body AND the matching fund name in the captured issuer API index.
    if '交易證券代號' not in code_heading:
        code_matches = bool(re.search(r'元大台灣卓越50(?:證券投資信託)?基金', title))
    if not code_matches or not re.search(r'元大台灣卓越50證券投資信託基金',compact):
        raise ValueError('Not an ordinary 0050 notice')
    ex=one_date(compact,'除息交易日');payment=one_date(compact,'收益分配發放日')
    header=re.search(r'中華民國('+DATE+r')',compact.split('主旨',1)[0])
    if not header:raise ValueError('Missing PDF issue date')
    stage='FINAL' if '實際配發金額' in re.sub(r'\s+','',meta['title']) else 'ESTIMATE'
    label='實際配發金額' if stage=='FINAL' else '預估配發金額'
    amounts=set(re.findall(r'每受益權單位'+label+r'(?:為)?新[臺台]幣([\d.]+)元',compact))
    if len(amounts)>1 or (stage=='FINAL' and len(amounts)!=1):raise ValueError('Missing or ambiguous '+label)
    pdf_date=iso(header[1]);index_date=meta['announcement_date'].replace('/','-')[:10]
    return dict(id=meta['id'],code='0050',title=meta['title'],url=meta['url'],path=meta['path'],
                response_sha256=meta['response_sha256'],retrieved_at=meta['retrieved_at'],
                announcement_date=max(pdf_date,index_date),issuer_index_date=index_date,pdf_issue_date=pdf_date,
                availability_precision='DATE_ONLY',publication_vintage_certified=False,revision_inventory_complete=False,
                ex_dates=[ex],cash_payment_dates=[payment],stage=stage,
                declared_cash_amount=amounts.pop() if amounts else '',amount_stage='CONDITIONAL_DECLARATION' if stage=='ESTIMATE' else 'FINAL_ISSUER_DECLARATION',
                identity_match='ISSUER_PDF_EX_DATE',evidence_class='ORIGINAL_ISSUER_PDF')

def load_notices():
    manifest=OUT/'sources/targeted_issuers/manifest.json'
    if not manifest.exists():return []
    rows = json.loads(manifest.read_text())
    versions=[]; rejected=[]
    index_meta = next((r for r in rows if r['id'] == 'yuanta_fund_announcement_api_valid_device'), None)
    index = {}
    if index_meta:
        packed = (ROOT / index_meta['path']).read_bytes()
        raw = gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest() != index_meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != index_meta['response_sha256']:
            raise ValueError('Issuer index hash mismatch')
        payload = json.loads(raw)
        if payload['ResultCode'] != 0 or payload['Data']['Number'] != len(payload['Data']['Announcement']):
            raise ValueError('Invalid or incomplete current issuer index response')
        index = {r['UId']: r for r in payload['Data']['Announcement']}
    for meta in rows:
        if not meta['id'].startswith('yuanta_0050_notice_'):continue
        if meta['status']!='RESPONSE_SAVED_NEEDS_VALIDATION':
            rejected.append(dict(id=meta['id'],reason=meta['status']));continue
        packed=(ROOT/meta['path']).read_bytes();raw=gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest()!=meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest()!=meta['response_sha256']:raise ValueError('Issuer PDF hash mismatch')
        try:
            entry = index.get(meta['announcement_id'])
            if not entry or entry['ContentsType'] != 'PDF' or entry['Title'] != meta['title'] or entry['OnTime'] != meta['announcement_date'] or unquote(entry['Contents']) != unquote(meta['url']):
                raise ValueError('PDF does not match captured issuer index')
            if not raw.startswith(b'%PDF-'):raise ValueError('Not PDF bytes')
            extracted=subprocess.run(['pdftotext','-layout','-','-'],input=raw,capture_output=True,check=True).stdout.decode('utf8')
            row = parse_notice(extracted,meta)
            row.update(issuer_index_source_id=index_meta['id'], issuer_index_response_sha256=index_meta['response_sha256'])
            versions.append(row)
        except (ValueError,subprocess.CalledProcessError) as error:rejected.append(dict(id=meta['id'],reason=str(error)))
    versions.sort(key=lambda r:(r['announcement_date'],r['id']))
    pairs = defaultdict(list)
    for row in versions:
        pairs[row['ex_dates'][0]].append(row)
    pair_rows = []
    for ex, rows in sorted(pairs.items()):
        estimates = [r for r in rows if r['stage'] == 'ESTIMATE']
        finals = [r for r in rows if r['stage'] == 'FINAL']
        if len(estimates) != 1 or len(finals) != 1:
            continue
        estimated, final = estimates[0], finals[0]
        pair_rows.append(dict(ex_date=ex, estimated_amount=estimated['declared_cash_amount'], final_amount=final['declared_cash_amount'],
                              amount_changed=estimated['declared_cash_amount'] != final['declared_cash_amount'],
                              estimate_announcement_date=estimated['announcement_date'], final_announcement_date=final['announcement_date'],
                              estimate_source_id=estimated['id'], final_source_id=final['id'],
                              estimate_response_sha256=estimated['response_sha256'], final_response_sha256=final['response_sha256'],
                              payment_date=final['cash_payment_dates'][0], publication_vintage_certified=False, revision_inventory_complete=False))
    if pair_rows:
        with (OUT/'yuanta_0050_revision_pair_check.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]), lineterminator='\n')
            writer.writeheader(); writer.writerows(pair_rows)
    (OUT/'yuanta_0050_original_pdf_versions.json').write_text(json.dumps(versions,ensure_ascii=False,indent=2)+'\n')
    (OUT/'yuanta_0050_pdf_validation.json').write_text(json.dumps(dict(valid=len(versions),rejected=rejected,paired_estimate_final_events=len(pair_rows),estimated_amount_revised_events=sum(r['amount_changed'] for r in pair_rows),current_index_records=len(index),current_index_start=min((r['OnTime'] for r in index.values()),default=''),current_index_end=max((r['OnTime'] for r in index.values()),default=''),revision_inventory_complete=False),ensure_ascii=False,indent=2)+'\n')
    return versions
if __name__=='__main__':print(json.dumps({'validated':len(load_notices())}))
