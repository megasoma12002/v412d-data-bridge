#!/usr/bin/env python3
"""Normalize hashed issuer PDF notices; estimated and final fields stay separate."""
import csv, gzip, hashlib, json, re, subprocess, unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit
from lxml import html
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
    compact=re.sub(r'\s+','',unicodedata.normalize('NFKC', text))
    compact=compact.replace('50證券投資信託50證券投資信託', '50證券投資信託')
    title = re.sub(r'\s+', '', meta['title'])
    baolai = meta.get('archive_source') == 'SITCA_LEGACY_BAOLAI_DISCLOSURE_PDF'
    old_yuanta = meta.get('observed_archive_listing_verified', False) and '元大寶來台灣卓越50證券投資信託基金' in compact.split('原名', 1)[0]
    fund_name = '寶來台灣卓越50' if baolai else '元大寶來台灣卓越50' if old_yuanta else '元大台灣卓越50'
    code_heading = compact.split('中華民國', 1)[0]
    code_matches = bool(re.search(r'交易證券代號[交易證券代號名稱:：]{0,40}0050(?!\d)', code_heading))
    # Older issuer PDFs omit the trading code: require the unique legal fund
    # name in the body AND the matching fund name in the captured issuer API index.
    if '交易證券代號' not in code_heading:
        code_matches = bool(re.search(re.escape(fund_name)+r'(?:證券投資信託)?基金', title)) or (meta.get('observed_archive_listing_verified', False) and '台灣卓越50ETF' in title)
    if not code_matches or fund_name + '證券投資信託基金' not in compact:
        raise ValueError('Not an ordinary 0050 notice')
    ex=one_date(compact,'除息交易日');payment=one_date(compact,'收益分配發放日')
    header=re.search(r'中華民國('+DATE+r')',compact.split('主旨',1)[0])
    if not header:raise ValueError('Missing PDF issue date')
    stage='FINAL' if '實際配發金額' in title or (meta.get('observed_archive_listing_verified', False) and '第二階段' in title) else 'ESTIMATE'
    label='實際配發金額' if stage=='FINAL' else '預估配發金額'
    if stage == 'ESTIMATE' and re.search(r'每受益權單位實際配發金額(?:為)?新[臺台]幣[\d.]+元', compact) and not re.search(r'每受益權單位預估配發金額(?:為)?新[臺台]幣[\d.]+元', compact):
        raise ValueError('Discovery stage conflicts with explicit final PDF amount')
    amounts=set(re.findall(r'每受益權單位'+label+r'(?:為)?新[臺台]幣([\d.]+)元',compact))
    if len(amounts)>1 or (stage=='FINAL' and len(amounts)!=1):raise ValueError('Missing or ambiguous '+label)
    pdf_date=iso(header[1]);index_date=meta.get('announcement_date','').replace('/','-')[:10]
    document = re.search(r'元(?:寶)?投信字第([\d-]+)號',compact)
    if baolai and ('寶來證券投資信託股份有限公司' not in compact or not '2010-01-01' <= pdf_date <= '2011-12-31'):
        raise ValueError('Legacy Baolai issuer or historical period mismatch')
    if old_yuanta and not '2012-01-01' <= pdf_date <= '2015-12-31':
        raise ValueError('Historical Yuanta Baolai name outside observed period')
    signatures = ('元大寶來證券投資信託股份有限公司', '元大證券投資信託股份有限公司') if old_yuanta else ('元大證券投資信託股份有限公司',)
    legacy_2012_without_number = old_yuanta and '2012-01-01' <= pdf_date <= '2012-12-31' and '元大寶來證券投資信託股份有限公司' in compact
    if meta.get('archive_source') and not baolai and ((not document and not legacy_2012_without_number) or not any(signature in compact for signature in signatures)):
        raise ValueError('Legacy PDF lacks issuer signature or document number')
    return dict(id=meta['id'],code='0050',title=meta['title'],url=meta['url'],path=meta['path'],
                response_sha256=meta['response_sha256'],retrieved_at=meta['retrieved_at'],
                announcement_date=max(pdf_date,index_date),issuer_index_date=index_date,pdf_issue_date=pdf_date,
                document_number=document[1] if document else '',archive_source=meta.get('archive_source','ISSUER_API_PDF'),
                availability_precision='DATE_ONLY',publication_vintage_certified=False,revision_inventory_complete=False,
                ex_dates=[ex],cash_payment_dates=[payment],stage=stage,
                declared_cash_amount=amounts.pop() if amounts else '',amount_stage='CONDITIONAL_DECLARATION' if stage=='ESTIMATE' else 'FINAL_ISSUER_DECLARATION',
                identity_match='ISSUER_PDF_EX_DATE',evidence_class='ORIGINAL_ISSUER_PDF')

def stage_gaps(versions, events):
    result = []
    for event in events:
        if event['code'] != '0050' or float(event['cash_dividend']) <= 0:
            continue
        ex = event['cash_ex_date']
        linked = [r for r in versions if ex in r['ex_dates']]
        estimates = [r for r in linked if r['stage'] == 'ESTIMATE']
        finals = [r for r in linked if r['stage'] == 'FINAL']
        if len(estimates) != 1 or len(finals) != 1:
            result.append(dict(event_id='0050:cash:' + ex, ex_date=ex,
                               estimate_versions=len(estimates), final_versions=len(finals),
                               missing_stages=','.join(s for s, rows in [('ESTIMATE', estimates), ('FINAL', finals)] if not rows),
                               ambiguous_stages=','.join(s for s, rows in [('ESTIMATE', estimates), ('FINAL', finals)] if len(rows) > 1),
                               publication_vintage_certified=False, revision_inventory_complete=False))
    return result

def verify_observed_listing(meta, rows):
    index = next((r for r in rows if r['id'] == meta.get('index_source_id')), None)
    if not index or index['status'] != 'RESPONSE_SAVED_NEEDS_VALIDATION':
        raise ValueError('Missing complete observed archive query')
    if iso(meta['listing_date']) != meta['announcement_date']:
        raise ValueError('Observed listing date does not match announcement date')
    expected_company = 'A0013' if meta.get('archive_source') == 'SITCA_LEGACY_BAOLAI_DISCLOSURE_PDF' else 'A0005'
    if index.get('url') != 'https://www.sitca.org.tw/ROC/MemNews/MN2001N.aspx?PGMID=SD0202' or index.get('method') != 'POST' or index.get('company') != expected_company or index.get('period') != 'All' or index.get('form_category') != '02':
        raise ValueError('Unverified public archive query origin or filters')
    packed = (ROOT / index['path']).read_bytes(); raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest() != index['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != meta['index_response_sha256'] or meta['index_response_sha256'] != index['response_sha256'] or b'</html>' not in raw.lower():
        raise ValueError('Observed archive query hash or completeness mismatch')
    tree = html.fromstring(raw)
    for tr in tree.xpath('//table[contains(@id,"GridView1")]/tr[td]'):
        cells = tr.xpath('./td')
        if cells[0].text_content().strip() != meta['title'] or cells[1].text_content().strip() != meta['listing_date']:
            continue
        for button in tr.xpath('.//input[@onclick]'):
            link = re.search(r"window.open\('([^']+)'", button.get('onclick'))
            if link and unquote(link[1]).replace('http:', 'https:', 1) == unquote(meta['url']):
                return True
    raise ValueError('PDF URL, title and date not present in saved archive table')


def load_notices():
    manifest=OUT/'sources/targeted_issuers/manifest.json'
    if not manifest.exists():return []
    rows = json.loads(manifest.read_text())
    versions=[]; rejected=[]; aliases=[]
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
            if meta.get('index_source_id'):
                meta = dict(meta, observed_archive_listing_verified=verify_observed_listing(meta, rows))
            if meta.get('archive_source'):
                host=urlsplit(meta['url']).netloc
                path=unquote(urlsplit(meta['url']).path)
                allowed=(meta['archive_source']=='ISSUER_LEGACY_PDF' and host=='www.yuantafunds.com' and path.startswith('/download/PDF/announces/基金配息公告/')) or (meta['archive_source']=='SITCA_ISSUER_DISCLOSURE_PDF' and host=='www.sitca.org.tw' and path.startswith('/FundNote/A/A0005/02/'))
                allowed = allowed or (meta['archive_source']=='SITCA_LEGACY_BAOLAI_DISCLOSURE_PDF' and host=='www.sitca.org.tw' and (path.startswith('/OPF/A0000/files/FundNote/A/A0013/02/') or (meta.get('observed_archive_listing_verified', False) and path.startswith('/FundNote/A/A0013/02/'))))
                if not allowed or unquote(meta.get('discovery_url','')) != unquote(meta['url']):
                    raise ValueError('Unverified legacy issuer archive origin')
            else:
                entry = index.get(meta['announcement_id'])
                if not entry or entry['ContentsType'] != 'PDF' or entry['Title'] != meta['title'] or entry['OnTime'] != meta['announcement_date'] or unquote(entry['Contents']) != unquote(meta['url']):
                    raise ValueError('PDF does not match captured issuer index')
            if not raw.startswith(b'%PDF-'):raise ValueError('Not PDF bytes')
            extracted=subprocess.run(['pdftotext','-layout','-','-'],input=raw,capture_output=True,check=True).stdout.decode('utf8')
            row = parse_notice(extracted,meta)
            if meta.get('archive_source'):
                row.update(discovery_url=meta['discovery_url'],issuer_index_source_id=meta.get('index_source_id',''),issuer_index_response_sha256=meta.get('index_response_sha256',''),archive_listing_vintage_certified=False)
            else:
                row.update(issuer_index_source_id=index_meta['id'], issuer_index_response_sha256=index_meta['response_sha256'])
            duplicate = next((v for v in versions if v['response_sha256'] == row['response_sha256'] and v['stage'] == row['stage']), None)
            if duplicate:
                aliases.append(dict(id=row['id'], original_id=duplicate['id'], response_sha256=row['response_sha256']))
            else:
                versions.append(row)
        except (ValueError,subprocess.CalledProcessError) as error:rejected.append(dict(id=meta['id'],reason=str(error)))
    versions.sort(key=lambda r:(r['announcement_date'],r['id']))
    with (ROOT/'data/dividend_events/e22_dividend_events.csv').open() as handle:
        gaps = stage_gaps(versions, list(csv.DictReader(handle)))
    with (OUT/'remaining_0050_revision_stage_gaps.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['event_id','ex_date','estimate_versions','final_versions','missing_stages','ambiguous_stages','publication_vintage_certified','revision_inventory_complete'], lineterminator='\n')
        writer.writeheader();writer.writerows(gaps)
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
    (OUT/'yuanta_0050_pdf_validation.json').write_text(json.dumps(dict(valid=len(versions),rejected=rejected,duplicate_source_aliases=aliases,paired_estimate_final_events=len(pair_rows),estimated_amount_revised_events=sum(r['amount_changed'] for r in pair_rows),current_index_records=len(index),current_index_start=min((r['OnTime'] for r in index.values()),default=''),current_index_end=max((r['OnTime'] for r in index.values()),default=''),revision_inventory_complete=False),ensure_ascii=False,indent=2)+'\n')
    return versions
if __name__=='__main__':print(json.dumps({'validated':len(load_notices())}))
