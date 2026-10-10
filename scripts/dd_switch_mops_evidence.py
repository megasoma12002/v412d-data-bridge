#!/usr/bin/env python3
"""Capture and reconcile current official historical filings, without certifying vintage."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from io import StringIO
from pathlib import Path

import pandas as pd
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
SOURCES = OUT / 'sources/mops_annual'
LEDGER = ROOT / 'data/dividend_events/e22_dividend_events.csv'


def day(value):
    value = str(value).strip()
    if not value:
        return ''
    parts = re.fullmatch(r'(\d{2,4})/(\d{1,2})/(\d{1,2})', value)
    if not parts:
        raise ValueError(f'Unknown MOPS date: {value!r}')
    y, m, d = map(int, parts.groups())
    return datetime(y + 1911 if y < 1911 else y, m, d).date().isoformat()


def number(value):
    value = str(value).strip().replace(',', '')
    return Decimal(value) if value else Decimal(0)


def parse_report(raw, metadata):
    text = raw.decode('utf-8')
    if '公司股利分派公告資料彙總表' not in text:
        raise ValueError('Not a MOPS dividend table (possibly a security error page)')
    tables = pd.read_html(StringIO(text), keep_default_na=False, converters={0: str})
    output = []
    for table in tables:
        if not isinstance(table.columns, pd.MultiIndex):
            continue
        names = [column[-1] for column in table.columns]
        if len(set(names)) != len(names):
            raise ValueError('Ambiguous MOPS column names')
        required = {'公司代號', '權利分派基準日', '公告日期', '公告時間',
                    '除權交易日', '除息交易日', '盈餘轉增資配股(元/股)',
                    '法定盈餘公積、資本公積轉增資配股(元/股)',
                    '盈餘分配之股東現金股利(元/股)',
                    '法定盈餘公積、資本公積發放之現金(元/股)',
                    '現金增資總股數(股)', '現金增資認股比率(%)', '現金增資認購價(元/股)'}
        if not required.issubset(names):
            raise ValueError(f'Missing MOPS columns: {required - set(names)}')
        table.columns = names
        fiscal_field = '股利所屬年度' if '股利所屬年度' in names else '股利所屬期間'
        for row in table.to_dict('records'):
            code = str(row['公司代號'])
            if not re.fullmatch(r'\d{4}', code):
                continue  # Repeated HTML header, never a data row.
            reported_day = day(row['公告日期'])
            clock = str(row['公告時間']).strip()
            reported = datetime.fromisoformat(f'{reported_day}T{clock}+08:00')
            if reported.year != metadata['year']:
                raise ValueError('Returned announcement year differs from request')
            result = dict(code=code, fiscal_year=str(row[fiscal_field]),
                          record_date=day(row['權利分派基準日']),
                          reported_at=reported.isoformat(),
                          cash_ex_date=day(row['除息交易日']),
                          stock_ex_date=day(row['除權交易日']),
                          cash_payment_date=day(row.get('現金股利發放日', '')),
                          cash_dividend=str(number(row['盈餘分配之股東現金股利(元/股)']) +
                                            number(row['法定盈餘公積、資本公積發放之現金(元/股)'])),
                          stock_dividend=str(number(row['盈餘轉增資配股(元/股)']) +
                                             number(row['法定盈餘公積、資本公積轉增資配股(元/股)'])),
                          subscription_shares=str(number(row['現金增資總股數(股)'])),
                          subscription_ratio_percent=str(number(row['現金增資認股比率(%)'])),
                          subscription_price=str(number(row['現金增資認購價(元/股)'])),
                          source_url=metadata['url'], source_path=metadata['path'],
                          response_sha256=metadata['response_sha256'],
                          retrieved_at=metadata['retrieved_at'],
                          publication_vintage_certified=False,
                          revision_inventory_complete=False)
            output.append(result)
    if not output:
        raise ValueError('No validated MOPS rows')
    return output


def fetch_year(year):
    url = ('https://mopsov.twse.com.tw/mops/web/ajax_t108sb27?firstin=true&TYPEK=sii'
           f'&co_id_1=2412&co_id_2=5880&year={year - 1911}&step=1')
    response = subprocess.run(['curl', '-L', '--max-time', '35', '-sS', '-w', '\n%{http_code}', url],
                              capture_output=True)
    raw, _, status = response.stdout.rpartition(b'\n')
    path = SOURCES / f't108sb27_{year}.html.gz'
    path.write_bytes(gzip.compress(raw, mtime=0))
    entry = dict(year=year, url=url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                 http_status=status.decode(), path=str(path.relative_to(ROOT)),
                 response_sha256=hashlib.sha256(raw).hexdigest(),
                 compressed_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=len(raw))
    try:
        if response.returncode or status != b'200':
            raise ValueError(f'HTTP {status.decode()}, curl {response.returncode}')
        rows = parse_report(raw, entry)
        entry.update(status='TABLE_CAPTURED', validated_rows=len(rows))
    except Exception as error:
        entry.update(status='UNAVAILABLE', error=str(error))
    return entry


def load_reports():
    rows = []
    manifest = json.loads((SOURCES / 'manifest.json').read_text())
    for entry in manifest:
        if entry['status'] != 'TABLE_CAPTURED':
            continue
        path = ROOT / entry['path']
        raw = gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != entry['response_sha256']:
            raise ValueError('Original retrieved response hash mismatch')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['compressed_sha256']:
            raise ValueError('Compressed source hash mismatch')
        rows.extend(parse_report(raw, entry))
    return rows


def reconcile(ledger, sources):
    checks = []
    for event in ledger:
        for leg in ('cash', 'stock'):
            if number(event[leg + '_dividend']) <= 0 or event['code'] == '0050':
                continue
            matched = [r for r in sources if r['code'] == event['code'] and
                       r[leg + '_ex_date'] == event[leg + '_ex_date'] and
                       r['record_date'] == event['record_date']]
            errors = []
            if len(matched) != 1:
                errors.append('NO_UNIQUE_PRIMARY_MATCH')
            source = matched[0] if len(matched) == 1 else {}
            if source:
                if abs(number(source[leg + '_dividend']) - number(event[leg + '_dividend'])) > Decimal('0.00000001'):
                    errors.append('AMOUNT')
                own_clock = event['announcement_date'] + 'T' + event['announcement_time'] + '+08:00'
                if datetime.fromisoformat(source['reported_at']) != datetime.fromisoformat(own_clock):
                    errors.append('REPORTED_CLOCK')
                if source['reported_at'][:10] > event[leg + '_ex_date']:
                    errors.append('REPORTED_AFTER_EX')
                if leg == 'cash' and source['cash_payment_date'] and source['cash_payment_date'] != event['cash_payment_date']:
                    errors.append('CASH_PAYMENT_DATE')
            checks.append(dict(code=event['code'], leg=leg, ex_date=event[leg + '_ex_date'],
                               primary_reported_at=source.get('reported_at', ''),
                               primary_amount=source.get(leg + '_dividend', ''),
                               ledger_amount=event[leg + '_dividend'],
                               primary_payment_date=source.get(leg + '_payment_date', ''),
                               payment_date_primary_supported=bool(source.get(leg + '_payment_date')),
                               primary_reported_time_supported=not errors,
                               mismatch_fields='|'.join(errors), source_url=source.get('source_url', ''),
                               source_path=source.get('source_path', ''),
                               response_sha256=source.get('response_sha256', ''),
                               publication_vintage_certified=False,
                               status='PRIMARY_REPORTED_FIELDS_MATCH' if not errors else 'PRIMARY_EVIDENCE_INCOMPLETE_OR_MISMATCH'))
    return checks


def reconcile_actions(ledger, sources):
    results = []
    for event in ledger:
        if not event['stock_ex_date'] or number(event['stock_dividend']) != 0:
            continue
        matched = [r for r in sources if r['code'] == event['code'] and
                   r['stock_ex_date'] == event['stock_ex_date'] and
                   r['record_date'] == event['record_date']]
        source = matched[0] if len(matched) == 1 else {}
        supported = bool(source and number(source['subscription_shares']) > 0 and
                         number(source['subscription_ratio_percent']) > 0 and number(source['subscription_price']) > 0)
        ratio = number(source.get('subscription_ratio_percent', '')) / 100
        results.append(dict(code=event['code'], ex_date=event['stock_ex_date'],
                            record_date=event['record_date'], primary_reported_at=source.get('reported_at', ''),
                            classification='PAID_SUBSCRIPTION_RIGHT' if supported else 'ACTION_PROOF_MISSING',
                            issued_security_class='UNRESOLVED', share_ratio=str(ratio) if supported else '',
                            shares_per_1000=str(ratio * 1000) if supported else '',
                            subscription_price=source.get('subscription_price', ''),
                            subscription_shares=source.get('subscription_shares', ''),
                            primary_subscription_terms_supported=supported,
                            primary_verified=False, free_stock_dividend=False,
                            source_url=source.get('source_url', ''), source_path=source.get('source_path', ''),
                            response_sha256=source.get('response_sha256', ''),
                            publication_vintage_certified=False,
                            status='SUBSCRIPTION_TERMS_MATCH_CLASS_AND_SETTLEMENT_PENDING' if supported else 'ACTION_PROOF_MISSING'))
    return results


def action_class_evidence(actions):
    """Link security class to an actual filing of the same subscription event."""
    manifest_path = OUT / 'sources/mops_actions/manifest.json'
    if not manifest_path.exists():
        return actions
    details = []
    for meta in json.loads(manifest_path.read_text()):
        if meta['kind'] != 'DETAIL' or meta['status'] != 'CAPTURED':
            continue
        path = ROOT / meta['path']
        raw = gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest() != meta['response_sha256']:
            raise ValueError('Action filing response hash mismatch')
        tree = html.fromstring(raw.decode('utf-8', errors='strict'))
        for element in tree.xpath('//script | //style'):
            element.drop_tree()
        text = re.sub(r'\s+', '', tree.text_content())
        if '本資料由' not in text or '主旨' not in text or '說明' not in text:
            raise ValueError('Not a validated official announcement detail')
        details.append((meta, text))
    for action in actions:
        action.update(class_source_url='', class_source_path='', class_response_sha256='',
                      class_filing_reported_at='', event_identity_evidence='', settlement_certified=False)
        matching = []
        for meta, text in details:
            if meta['code'] != action['code']:
                continue
            date_values = set()
            for y, m, d in re.findall(r'(\d{2,3})[年/](\d{1,2})[月/](\d{1,2})', text):
                try:
                    date_values.add(day(f'{y}/{m}/{d}'))
                except ValueError:
                    pass
            # Ratios are per 1,000 shares in the filing, percent in the aggregate.
            ratio_matches = [v for v in re.findall(r'(?:每仟股|每千股).*?(\d+\.\d+)股', text)]
            ratio_match = any(abs(number(v) - number(action['shares_per_1000'])) < Decimal('0.0000001') for v in ratio_matches)
            if action['record_date'] not in date_values and not ratio_match:
                continue
            title = re.sub(r'\s+', '', meta['title'])
            preferred = re.search(r'(甲|乙|丙|丁|戊)種特別股', title)
            if preferred:
                security_class = 'PREFERRED_' + dict(甲='A', 乙='B', 丙='C', 丁='D', 戊='E')[preferred[1]]
            else:
                # Opening issue description, not a later comparison to old shares.
                opening = text.split('說明', 1)[1][:650]
                issue = re.search(r'發行(?:股數[:：])?(?:新股)?(?:為)?(?:之)?(普通股|特別股)', opening)
                if not issue:
                    issue = re.search(r'(普通股|特別股)[\d,.億萬仟千]+股', opening)
                if not issue or issue[1] != '普通股':
                    continue
                security_class = 'ORDINARY'
            matching.append((meta, security_class, 'RECORD_DATE_AND_RATIO' if ratio_match and action['record_date'] in date_values else 'RECORD_DATE' if action['record_date'] in date_values else 'SUBSCRIPTION_RATIO'))
        if not matching:
            continue
        classes = {v[1] for v in matching}
        if len(classes) != 1:
            raise ValueError('Conflicting issued share classes for one subscription event')
        meta, security_class, identity = matching[-1]
        _, date_value, clock, _ = meta['id'].split('_')
        reported = datetime.strptime(date_value + clock, '%Y%m%d%H%M%S').isoformat() + '+08:00'
        if reported[:10] > action['ex_date']:
            raise ValueError('Class evidence was reported after ex-date')
        action.update(issued_security_class=security_class,
                      classification='PAID_ORDINARY_SUBSCRIPTION_RIGHT' if security_class == 'ORDINARY' else 'PAID_PREFERRED_SUBSCRIPTION_RIGHT',
                      primary_verified=action['primary_subscription_terms_supported'],
                      class_source_url=meta['url'], class_source_path=meta['path'],
                      class_response_sha256=meta['response_sha256'], class_filing_reported_at=reported,
                      event_identity_evidence=identity,
                      status='PRIMARY_SUBSCRIPTION_AND_CLASS_EVIDENCE_MATCH_SETTLEMENT_PENDING')
    return actions


def write_csv(path, rows):
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    SOURCES.mkdir(exist_ok=True)
    if args.fetch:
        entries = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            for entry in pool.map(fetch_year, range(2010, 2027)):
                entries.append(entry)
                (SOURCES / 'manifest.json').write_text(json.dumps(entries, indent=2) + '\n')
                print(entry['year'], entry['status'], flush=True)
    sources = load_reports()
    ledger = list(csv.DictReader(LEDGER.open()))
    codes = {r['code'] for r in ledger}
    selected = [r for r in sources if r['code'] in codes]
    checks = reconcile(ledger, selected)
    actions = action_class_evidence(reconcile_actions(ledger, selected))
    write_csv(OUT / 'mops_dividend_field_check.csv', checks)
    write_csv(OUT / 'mops_action_field_check.csv', actions)
    (OUT / 'mops_official_reported_facts.json').write_text(json.dumps(selected, indent=2) + '\n')
    summary = dict(positive_dividend_legs=len(checks),
                   primary_reported_time_supported_legs=sum(r['primary_reported_time_supported'] for r in checks),
                   remaining_legs=sum(not r['primary_reported_time_supported'] for r in checks),
                   payment_date_primary_supported_legs=sum(r['payment_date_primary_supported'] for r in checks),
                   action_candidates=len(actions),
                   primary_subscription_terms_supported=sum(r['primary_subscription_terms_supported'] for r in actions),
                   issued_security_class_pending=sum(r['issued_security_class'] == 'UNRESOLVED' for r in actions),
                   primary_classified_actions=sum(r['primary_verified'] for r in actions),
                   ledger_sha256=hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
                   canonical_modified=False, backtest_ready=False, backtest_executed=False,
                   publication_vintage_certified_legs=0,
                   limits=['Current primary historical table is not an original historical HTTP capture',
                           'Reported timestamps do not certify first publication or complete amendment history',
                           'Stock payment dates are not present in this aggregate table',
                           'Subscription right does not create free ordinary shares or automatic cash payment'])
    (OUT / 'mops_evidence_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
