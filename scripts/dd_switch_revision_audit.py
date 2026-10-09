#!/usr/bin/env python3
"""Reconcile event-level public filing versions and settlement schedules; fail closed on gaps."""
import csv
import gzip
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from lxml import html
from dd_switch_mops_evidence import day, number

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
ASOF = '2026-10-08'
DATE = r'(?<!\d)(\d{2,4})[年/.-](\d{1,2})[月/.-](\d{1,2})(?:日)?(?!\d)'


def dates(text):
    values = []
    for y, m, d in re.findall(DATE, text):
        try:
            value = day(f'{y}/{m}/{d}')
            if '2000-01-01' <= value <= '2030-12-31':
                values.append(value)
        except ValueError:
            pass
    return values


def numbered_fields(text):
    body = text.split('說明', 1)[-1].split('以上資料', 1)[0]
    marks = list(re.finditer(r'(?m)^\s*(\d{1,2})[.．、](?!\d)([^:\n：]{1,100})[:：]', body))
    # Ignore numbered sub-items inside a field (e.g. 16. has nested 1./2.).
    outer = []
    previous = 0
    for mark in marks:
        if int(mark[1]) > previous:
            outer.append(mark)
            previous = int(mark[1])
    marks = outer
    result = {}
    for i, mark in enumerate(marks):
        label = re.sub(r'\s+', '', mark[2])
        value = body[mark.end():marks[i+1].start() if i+1 < len(marks) else len(body)]
        result[label] = re.sub(r'\s+', '', value)
    return result


def field(fields, labels):
    return [(key, value) for key, value in fields.items() if any(label in key for label in labels)]


def date_field(fields, labels):
    values = [d for key, value in field(fields, labels) for d in dates(value)]
    return sorted(set(values))


def declared_amounts(fields):
    structured = ''.join(v for k,v in fields.items() if '股東配發內容' in k)
    values = {}
    for leg,labels in [('cash',['盈餘分配之現金股利','法定盈餘公積、資本公積發放之現金']),
                       ('stock',['盈餘轉增資配股','法定盈餘公積、資本公積轉增資配股'])]:
        components=[]
        for label in labels:
            found=re.search(re.escape(label)+r'\(元/股\)[:：]([\d.]+)',structured)
            if found:components.append(number(found[1]))
        values[leg]=str(sum(components)) if len(components)==2 else ''
    text=''.join(v for k,v in fields.items() if '發放股利種類及金額' in k)
    if not values['cash'] and '現金' in text:
        matches=re.findall(r'每股(?:發放|可配發|配發|分配)?(?:現金(?:股利)?(?:為)?)?(?:新台幣|新臺幣)?([\d.]+)元',text)
        if len(set(matches))==1:
            values['cash']=matches[0]
    return values


def cash_schedule_dates(other):
    values=[]
    # Accept an explicit adjacent date; never scan forward into transfer deadlines.
    cash_labels = r'現金股利(?:預計|預訂|訂|將)?(?:發放(?:日期|日)?|支付(?:日期|日)?|於)'
    for match in re.finditer(cash_labels + r'(?:於|為|:|：)?(' + DATE + r')', other):
        values.extend(dates(match[1]))
    for match in re.finditer(r'現金股利.{0,80}?(?:發放日|支付日)(?:為|:|：)?(' + DATE + r')', other):
        values.extend(dates(match[1]))
    for match in re.finditer('(' + DATE + r')(?:為|係|是)?現金股利(?:發放日|支付日)', other):
        values.extend(dates(match[1]))
    return sorted(set(values))


def normalize(meta, raw):
    tree = html.fromstring(raw.decode('utf-8'))
    for e in tree.xpath('//script | //style'):
        e.drop_tree()
    plain = tree.text_content()
    compact = re.sub(r'\s+', '', plain)
    if not all(k in compact for k in ('本資料由', '發言日期', '發言時間', '說明')):
        raise ValueError('Unvalidated filing')
    _, date, clock, _ = meta['id'].split('_')
    reported = datetime.strptime(date + clock, '%Y%m%d%H%M%S').isoformat() + '+08:00'
    fields = numbered_fields(plain)
    record = date_field(fields, ['除權（息）基準日', '除權(息)基準日', '除權息基準日', '現金增資認股基準日', '認股基準日'])
    ex = date_field(fields, ['除權（息）交易日', '除權(息)交易日', '除權息交易日', '除息交易日', '除權交易日'])
    cash_payment = date_field(fields, ['現金股利發放日'])
    stock_payment = date_field(fields, ['新股發放日', '股票股利發放日', '增資股票發放日'])
    listing = date_field(fields, ['新股上市日', '新股上市交易日', '新股上櫃日'])
    subscription = field(fields, ['股款繳納期間', '繳款期間'])
    subscription_text = subscription[0][1] if subscription else ''
    # Original-holder window is first, specific-placee/call windows stay separate.
    pay_dates = dates(subscription_text)
    pay_window = pay_dates[:2] if len(pay_dates) >= 2 else []
    # Terms in an 'other matters' field retain exact date context and uncertainty.
    other = ' '.join(value for key, value in field(fields, ['其他應敘明', '因應措施', '發生緣由']))
    cash_payment.extend(cash_schedule_dates(other))
    for label, target in [('新股發放', stock_payment), ('新股上市', listing), ('股票股利發放', stock_payment)]:
        for hit in re.finditer(label + r'(?:日期|日)?[為於訂:：]*(.{0,45})', other):
            target.extend(dates(hit[1])[:1])
    ratios = []
    for key, value in field(fields, ['原股東認購比率']):
        ratios.extend(re.findall(r'(?:每仟股|每千股).*?(\d+\.\d+)股', value))
    amounts = declared_amounts(fields)
    units=re.findall(r'(?<!\d)(\d[\d,]*(?:\.\d+)?)(仟|千|萬|億)?股',compact)
    issued_shares=[str(number(v)*dict(仟=1000,千=1000,萬=10000,億=100000000).get(unit,1)) for v,unit in units]
    source = {k: meta[k] for k in ('id', 'code', 'title', 'url', 'path', 'response_sha256', 'retrieved_at')}
    issuer_subject = not bool(re.search(r'代(?!號|表|理|收)',meta['title'])) and not any('子公司' in v or '孫公司' in v for k,v in fields.items() if '與公司關係' in k)
    source.update(issuer_subject=issuer_subject, issued_share_count_candidates=issued_shares, reported_at=reported, fields=fields, declared_cash_amount=amounts['cash'], declared_stock_amount=amounts['stock'],
                  amount_stage='PROPOSAL' if re.search('擬議|擬配|提報.*股東',compact) else 'CONDITIONAL_DECLARATION' if re.search('暫定|實際.*(?:配發|股数|股數)',compact) else 'DECLARATION_UNCERTIFIED', record_dates=record, ex_dates=ex,
                  cash_payment_dates=sorted(set(cash_payment)), stock_payment_dates=sorted(set(stock_payment)),
                  new_share_listing_dates=sorted(set(listing)), subscription_window=pay_window,
                  subscription_window_text=subscription_text, ratios_per_1000=ratios,
                  completion_statement=bool(re.search(r'(?:已|業已)收足股款|募集完成', compact)),
                  conditional=bool(re.search(r'暫定|依.*(?:股數|基準日).*計算|另行公告|俟.*公告|預計', compact)),
                  publication_vintage_certified=False)
    return source


def load_filings():
    by_id = {}
    for name in ('mops_actions', 'mops_revisions'):
        path = OUT / 'sources' / name / 'manifest.json'
        if not path.exists():
            continue
        for meta in json.loads(path.read_text()):
            if meta['kind'] != 'DETAIL' or meta['status'] != 'CAPTURED':
                continue
            packed = (ROOT / meta['path']).read_bytes()
            raw = gzip.decompress(packed)
            if hashlib.sha256(packed).hexdigest() != meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != meta['response_sha256']:
                raise ValueError('Filing source hash mismatch')
            if meta['id'] in by_id and by_id[meta['id']]['response_sha256'] != meta['response_sha256']:
                raise ValueError('Conflicting captured version under one filing identity')
            by_id[meta['id']] = normalize(meta, raw)
    return sorted(by_id.values(), key=lambda r: (r['reported_at'], r['id']))


def subscription_identity(action, filing):
    if not filing.get('issuer_subject', True) or filing['code'] != action['code']:
        return False
    if action['record_date'] in filing['record_dates']:
        return True
    # Ratio alone is evidence only inside the same issuance-year, not across cycles.
    if filing['reported_at'][:4] != action['ex_date'][:4]:
        return False
    if any(abs(number(v)-number(action['shares_per_1000']))<Decimal('0.0000001') for v in filing['ratios_per_1000']):return True
    if not re.search(r'現金增資|現增',filing['title']):return False
    count_match=number(action['subscription_shares']) in [number(v) for v in filing.get('issued_share_count_candidates',[])]
    return count_match and 0<=(datetime.fromisoformat(filing['reported_at'][:10])-datetime.fromisoformat(action['ex_date'])).days<=180


def dividend_identity(event, leg, filing):
    return (filing.get('issuer_subject', True) and filing['code'] == event['code'] and
            (event[leg + '_ex_date'] in filing['ex_dates'] or event['record_date'] in filing['record_dates']) and
            ('現金增資' not in filing['title'] and '現增' not in filing['title']))


def revision_snapshot(versions, cutoff):
    """Research-only field prefix; date-only filings enter on the following local day."""
    from datetime import timedelta, timezone
    boundary=datetime.fromisoformat(cutoff)
    if boundary.tzinfo is None:raise ValueError('Timezone-aware cutoff required')
    candidates=[]
    for r in versions:
        if r.get('reported_at'):
            available=datetime.fromisoformat(r['reported_at'])
        elif r.get('announcement_date'):
            available=datetime.fromisoformat(r['announcement_date']+'T00:00:00+08:00')+timedelta(days=1)
        else:continue
        if available<=boundary:candidates.append((available,r))
    result={}
    for available,r in sorted(candidates,key=lambda x:(x[0],x[1]['id'])):
        event=r['event_id'];parts=event.split(':');leg=parts[1]
        row=result.setdefault(event,dict(event_id=event,publication_vintage_certified=False))
        for field_key,out_key in [('ex_dates','ex_date'),(leg+'_payment_dates','payment_date')]:
            ds=r.get(field_key,[])
            if len(ds)==1:row[out_key]=ds[0]
        amount=r.get('declared_'+leg+'_amount','')
        if amount:
            if r.get('amount_stage') in ('PROPOSAL','CONDITIONAL_DECLARATION'):
                row['estimated_amount']=amount
                row.pop('amount',None)
            else:
                row['amount']=amount
                row.pop('estimated_amount',None)
        row['last_visible_source_id']=r['id']
    return list(result.values())


def explicit_date_after(text, labels):
    values=[]
    for label in labels:
        for m in re.finditer(re.escape(label)+r'(?:為|於|訂於|預訂於|預計於|:|：|中華民國|民國)*(' + DATE + r')',text):
            values.extend(dates(m[1]))
    return sorted(set(values))


def load_statutory():
    path=OUT/'sources/mops_statutory/manifest.json'
    if not path.exists():return []
    rows=[]
    for meta in json.loads(path.read_text()):
        if meta['kind']!='STATUTORY_DETAIL' or meta['status']!='CAPTURED':continue
        packed=(ROOT/meta['path']).read_bytes();raw=gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest()!=meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest()!=meta['response_sha256']:raise ValueError('Statutory response hash mismatch')
        tree=html.fromstring(raw.decode('utf-8'))
        for e in tree.xpath('//script|//style'):e.drop_tree()
        text=re.sub(r'\s+','',tree.text_content())
        if '公告' not in text or meta['code'] not in text:raise ValueError('Statutory issuer identity mismatch')
        def after(labels):
            return explicit_date_after(text,labels)
        record=after(['權利分派基準日','除權息基準日','除息基準日','認股基準日'])
        ex=after(['除權/除息交易日','除權息交易日','除權交易日','除息交易日'])
        cash=after(['現金股利發放日','現金股利預訂於','現金股利預計於','現金股利訂於'])
        stock=after(['新股發放日期','新股發放日','增資新股發放上市日期','股票股利發放日','新股交付日期','增資股發放日期'])
        listing=after(['新股上市日期','新股上市日','新股上市交易日'])
        # Delivery notices often put the date before the delivery/listing verb.
        for m in re.finditer(r'(?:增資新股|本次新股|本次增資股票|增資股票)(?:權利證書)?(?:預訂|訂|將)?於(' + DATE + r'.{0,40})',text):
            ds=dates(m[1])
            if ds and re.search('交付|發放|撥入|劃撥',m[1]):stock.append(ds[0])
            if ds and re.search('上市',m[1]):listing.append(ds[0])
        voucher_delivery=[];voucher_listing=[]
        for m in re.finditer(r'本次現金增資股款繳納憑證[，,]?訂於(' + DATE + r'.{0,90})',text):
            ds=dates(m[1])
            if ds and '劃撥至' in m[1]:voucher_delivery.append(ds[0])
            if ds and '上市買賣' in m[1]:voucher_listing.append(ds[-1] if len(ds)>1 else ds[0])
        amendments=meta.get('amended_cash_payment_date','')
        original_cash=sorted(set(cash))
        amended_cash=dates(amendments) if amendments else []
        if amended_cash:
            cash=amended_cash
        units=re.findall(r'(?<!\d)(\d[\d,]*(?:\.\d+)?)(仟|千|萬|億)?股',text)
        issued_shares=[str(number(v)*dict(仟=1000,千=1000,萬=10000,億=100000000).get(unit,1)) for v,unit in units]
        rows.append(dict(id=meta['id'],code=meta['code'],title=meta['title'],url=meta['url'],path=meta['path'],response_sha256=meta['response_sha256'],retrieved_at=meta['retrieved_at'],
                         announcement_date=meta['announcement_date'], availability_precision='DATE_ONLY', original_cash_payment_dates=original_cash, amended_cash_payment_dates=amended_cash,
                         request_record_date=meta['request_record_date'],record_dates=record,ex_dates=ex,cash_payment_dates=sorted(set(cash)),
                         stock_payment_dates=sorted(set(stock)),new_share_listing_dates=sorted(set(listing)), voucher_delivery_dates=sorted(set(voucher_delivery)), voucher_listing_dates=sorted(set(voucher_listing)),issued_share_count_candidates=issued_shares,
                         registration_completed=bool(re.search('核准變更登記|完成資本額變更登記',text)),
                         completion_statement=bool(re.search('已收足股款|業已收足股款|募集完成',text)),
                         fiscal_years=re.findall(r'(?<!\d)(\d{2,3})(?:年度|年盈餘)',text),
                         compact_text=text,publication_vintage_certified=False))
    return sorted(rows,key=lambda r:(r['announcement_date'],r['id']))


def statutory_dividend_identity(event, leg, filing):
    if filing['code']!=event['code']:return False
    # Ledger securities are ordinary shares; do not attach preferred-share dividends.
    if re.search(r'[甲乙丙丁戊]種特別股|特別股股息',filing['title']):return False
    if event[leg+'_ex_date'] in filing['ex_dates'] or event['record_date'] in filing['record_dates']:return True
    fiscal=re.match(r'^(\d{2,3})年$',event['fiscal_year'])
    return bool(fiscal and fiscal[1] in filing['fiscal_years'] and
                abs((datetime.fromisoformat(filing['announcement_date'])-datetime.fromisoformat(event[leg+'_ex_date'])).days)<=180 and
                re.search(r'股利|股息|分派|盈餘.{0,40}轉增資|無償配發',filing['compact_text']))


def statutory_subscription_identity(action, filing):
    if filing['code']!=action['code']:return False
    if action['record_date'] in filing['record_dates'] or action['ex_date'] in filing['ex_dates']:return True
    if not 0<=(datetime.fromisoformat(filing['announcement_date'])-datetime.fromisoformat(action['ex_date'])).days<=180:return False
    # Exact issuance count, share class and narrow period are necessary for fallback linking.
    text=filing['compact_text']
    if action['issued_security_class']=='ORDINARY':
        if '●特別股' in text or re.search(r'(?:發行|發放).{0,10}[甲乙丙丁戊]種特別股',text):return False
    else:
        label={'PREFERRED_A':'甲','PREFERRED_B':'乙','PREFERRED_C':'丙','PREFERRED_D':'丁','PREFERRED_E':'戊'}[action['issued_security_class']]
        if label+'種特別股' not in text:return False
    return number(action['subscription_shares']) in [number(v) for v in filing['issued_share_count_candidates']]


def write_csv(path, rows):
    with path.open('w', newline='') as handle:
        w = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)


def main():
    with (ROOT / 'data/dividend_events/e22_dividend_events.csv').open() as f:
        ledger = list(csv.DictReader(f))
    with (OUT / 'mops_action_field_check.csv').open() as f:
        actions = list(csv.DictReader(f))
    filings = load_filings()
    statutory = load_statutory()
    payment_facts = defaultdict(list)
    with (OUT / 'mops_dividend_field_check.csv').open() as handle:
        for row in csv.DictReader(handle):
            if row['primary_payment_date']:
                payment_facts[(row['code'],row['leg'],row['ex_date'])].append(dict(
                    date=row['primary_payment_date'], id='MOPS_AGGREGATE', url=row['source_url'],
                    sha=row['response_sha256'], amount_matches=abs(number(row['primary_amount']) - number(row['ledger_amount'])) <= Decimal('0.00000001')))
    page_path = OUT / 'issuer_payment_schedule_facts.json'
    if page_path.exists():
        for row in json.loads(page_path.read_text()):
            payment_facts[(row['code'],row['leg'],row['ex_date'])].append(dict(
                date=row['payment_date'], id=row['source_id'], url=row['url'], sha=row['response_sha256'],
                amount_matches=row['amount_matches']))
    # ETF fact evidence remains normalized-only and distinct from raw-body captures.
    for fact_path in sorted((OUT/'sources').glob('announcement_facts_*.json')):
        for row in json.loads(fact_path.read_text()):
            if row.get('code') == '0050' and row.get('payment_date') and row.get('stage') == 'FINAL':
                payment_facts[('0050','cash',row['ex_date'])].append(dict(date=row['payment_date'],
                    id='ETF_NORMALIZED_FACT',url=row['source_url'],sha='',amount_matches=True))
    checks, versions, settlements = [], [], []
    for event in ledger:
        for leg in ('cash', 'stock'):
            if number(event[leg + '_dividend']) <= 0:
                continue
            identity = f"{event['code']}:{leg}:{event[leg + '_ex_date']}"
            matches = [r for r in filings if dividend_identity(event, leg, r)]
            before_ex = [r for r in matches if r['reported_at'][:10] <= event[leg + '_ex_date']]
            stat_matches=[r for r in statutory if statutory_dividend_identity(event,leg,r)]
            payments = [(r, d) for r in matches for d in r[leg + '_payment_dates']]
            for r in stat_matches:
                for d in r[leg+'_payment_dates']:
                    payment_facts[(event['code'],leg,event[leg+'_ex_date'])].append(dict(date=d,id=r['id'],url=r['url'],sha=r['response_sha256'],amount_matches=True,source_date=r['announcement_date']))
                versions.append(dict(event_id=identity,identity_match='STATUTORY_EX_RECORD_OR_FISCAL_YEAR',**r))
            latest = payments[-1] if payments else None
            known = list(payment_facts[(event['code'],leg,event[leg+'_ex_date'])])
            if latest:
                known.append(dict(date=latest[1],id=latest[0]['id'],url=latest[0]['url'],sha=latest[0]['response_sha256'],amount_matches=True,source_date=latest[0]['reported_at'][:10]))
            dated=[r for r in known if r.get('source_date')]
            primary=max(dated,key=lambda r:(r['source_date'],r['id'])) if dated else known[-1] if known else None
            supported = bool(primary and primary['date'] == event[leg + '_payment_date'] and primary['amount_matches'])
            checks.append(dict(event_id=identity, code=event['code'], leg=leg, ex_date=event[leg + '_ex_date'],
                               linked_filings=len(matches), statutory_linked_filings=len(stat_matches), first_linked_schedule_reported_at=before_ex[0]['reported_at'] if before_ex else '',
                               ledger_reported_at=event['announcement_date'] + 'T' + event['announcement_time'] + '+08:00',
                               earlier_schedule_found=bool(before_ex and before_ex[0]['reported_at'][:10] < event['announcement_date']),
                               explicit_amendment_filings=sum(bool(re.search(r'更正|補充|調整|變更|修正', r['title'])) for r in matches),
                               revision_inventory_complete=False, publication_vintage_certified=False,
                               status='LINKED_CURRENT_PRIMARY_FILINGS' if matches or stat_matches else 'SCHEDULE_CHAIN_PROOF_MISSING'))
            settlements.append(dict(event_id=identity, code=event['code'], leg=leg, ex_date=event[leg + '_ex_date'],
                                    ledger_payment_date=event[leg + '_payment_date'],
                                    latest_primary_payment_date=primary['date'] if primary else '',
                                    primary_payment_schedule_match=supported,
                                    source_id=primary['id'] if primary else '',
                                    source_url=primary['url'] if primary else '',
                                    response_sha256=primary['sha'] if primary else '',
                                    payment_date_conflict=bool(primary and primary['date'] != event[leg + '_payment_date']),
                                    contradictory_primary_dates=len({r['date'] for r in known}) > 1,
                                    primary_date_evidence=json.dumps(known,sort_keys=True),
                                    explicit_payment_amendment_supported=any(r.get('amended_cash_payment_dates') for r in stat_matches) if leg=='cash' else False,
                                    actual_holder_credit_certified=False, publication_vintage_certified=False,
                                    status='PRIMARY_PAYMENT_SCHEDULE_MATCH' if supported else 'PRIMARY_PAYMENT_DATE_CONFLICT' if primary else 'PRIMARY_PAYMENT_SCHEDULE_MISSING'))
            for r in matches:
                versions.append(dict(event_id=identity, identity_match='EX_OR_RECORD_DATE', **r))
    action_checks = []
    for action in actions:
        matches = [r for r in filings if subscription_identity(action, r)]
        stat_matches=[r for r in statutory if statutory_subscription_identity(action,r)]
        for r in stat_matches:versions.append(dict(event_id=f"{action['code']}:subscription:{action['ex_date']}",identity_match='STATUTORY_RECORD_OR_ISSUANCE_COUNT',**r))
        windows = [r for r in matches if r['subscription_window']]
        window = windows[-1] if windows else None
        # A completion filing must link the same event; a generic same-company claim is not enough.
        completions = [r for r in matches if r['completion_statement']]
        stock = [(r, d) for r in matches + stat_matches for d in r['stock_payment_dates']]
        listing = [(r, d) for r in matches + stat_matches for d in r['new_share_listing_dates']]
        voucher=[(r,d) for r in stat_matches for d in r.get('voucher_delivery_dates',[])]
        future = bool(window and window['subscription_window'][0] > ASOF)
        action_checks.append(dict(code=action['code'], ex_date=action['ex_date'], issued_security_class=action['issued_security_class'],
                                  linked_filings=len(matches), statutory_linked_filings=len(stat_matches), subscription_start=window['subscription_window'][0] if window else '',
                                  subscription_end=window['subscription_window'][1] if window else '',
                                  payment_window_source_id=window['id'] if window else '',
                                  payment_window_source_url=window['url'] if window else '',
                                  new_share_delivery_date=stock[-1][1] if stock else '',
                                  delivery_source_id=stock[-1][0]['id'] if stock else '',
                                  delivery_source_url=stock[-1][0]['url'] if stock else '',
                                  delivery_response_sha256=stock[-1][0]['response_sha256'] if stock else '',
                                  new_share_listing_date=listing[-1][1] if listing else '',
                                  listing_source_id=listing[-1][0]['id'] if listing else '',
                                  listing_source_url=listing[-1][0]['url'] if listing else '',
                                  listing_response_sha256=listing[-1][0]['response_sha256'] if listing else '',
                                  subscription_voucher_delivery_date=voucher[-1][1] if voucher else '',
                                  voucher_source_id=voucher[-1][0]['id'] if voucher else '',
                                  voucher_source_url=voucher[-1][0]['url'] if voucher else '',
                                  voucher_response_sha256=voucher[-1][0]['response_sha256'] if voucher else '',
                                  completion_filing_supported=bool(completions) or any(r['completion_statement'] for r in stat_matches),
                                  not_yet_due_asof=future, holder_subscription_assumed=False,
                                  ordinary_free_shares=0, settlement_certified=False,
                                  status='FUTURE_SUBSCRIPTION_NOT_YET_DUE' if future else 'PUBLIC_SETTLEMENT_CHAIN_INCOMPLETE'))
        for r in matches:
            versions.append(dict(event_id=f"{action['code']}:subscription:{action['ex_date']}", identity_match='RECORD_DATE_OR_SAME_YEAR_RATIO', **r))
    write_csv(OUT / 'revision_chain_check.csv', checks)
    write_csv(OUT / 'dividend_settlement_check.csv', settlements)
    write_csv(OUT / 'subscription_settlement_check.csv', action_checks)
    (OUT / 'mops_linked_revision_versions.json').write_text(json.dumps(versions, indent=2) + '\n')
    (OUT / 'statutory_normalized_filings.json').write_text(json.dumps(statutory,indent=2)+'\n')
    (OUT / 'mops_revision_normalized_filings.json').write_text(json.dumps(filings, indent=2) + '\n')
    summary = dict(asof=ASOF, captured_candidate_filings=len(filings), captured_statutory_filings=len(statutory), positive_dividend_legs=len(checks),
                   dividend_legs_with_linked_schedule_chain=sum(r['linked_filings'] > 0 or r['statutory_linked_filings'] > 0 for r in checks),
                   dividend_legs_with_earlier_schedule=sum(r['earlier_schedule_found'] for r in checks),
                   primary_payment_schedule_matches=sum(r['primary_payment_schedule_match'] for r in settlements),
                   payment_schedule_conflicts=sum(r['payment_date_conflict'] for r in settlements),
                   contradictory_primary_payment_dates=sum(r['contradictory_primary_dates'] for r in settlements),
                   subscription_events=len(action_checks), subscription_windows_supported=sum(bool(r['subscription_start']) for r in action_checks),
                   subscription_future_not_due=sum(r['not_yet_due_asof'] for r in action_checks),
                   subscription_delivery_dates_supported=sum(bool(r['new_share_delivery_date']) for r in action_checks),
                   subscription_voucher_dates_supported=sum(bool(r['subscription_voucher_delivery_date']) for r in action_checks),
                   subscription_listing_dates_supported=sum(bool(r['new_share_listing_date']) for r in action_checks),
                   revision_inventory_complete=False, publication_vintage_certified_legs=0,
                   backtest_ready=False, backtest_executed=False, canonical_modified=False,
                   limits=['Full annual indexes are current responses; keyword triage is not proof of complete revision history',
                           'Public scheduled payment dates do not prove a particular holder was credited',
                           'Subscription requires an explicit paid election; no automatic ordinary shares',
                           'Future scheduled settlement is not a missing past payment'])
    (OUT / 'revision_settlement_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
