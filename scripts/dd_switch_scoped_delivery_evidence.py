#!/usr/bin/env python3
"""Keep public recipient and late-call credit evidence scoped to the named recipients."""
import csv
import gzip
import hashlib
import json
import re
import subprocess
import unicodedata
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
from urllib.parse import urlsplit
from dd_switch_revision_audit import dates, load_statutory, statutory_subscription_identity

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'


def public_holder_row(text, meta, ledger):
    compact = re.sub(r'\s+', '', unicodedata.normalize('NFKC', text))
    if '學產基金' not in compact or '教育部' not in compact or '決算' not in compact:
        raise ValueError('Not the public fund final account')
    year = re.search(r'中華民國(\d{3})年度', compact)
    if not year:
        raise ValueError('Missing report year')
    year = int(year[1]) + 1911
    pages = [re.sub(r'\s+', '', unicodedata.normalize('NFKC', page)) for page in text.split('\f')]
    pages = [(i + 1, p) for i, p in enumerate(pages) if '華南' in p and '資金轉投資' in p]
    if len(pages) != 1:
        raise ValueError('Missing or ambiguous investment table')
    page_number, table = pages[0]
    segment = table.split('華南', 1)[1].split('臺新', 1)[0]
    original = re.search(r'原有股數([\d,]+)股', segment)
    receipt = re.search(r'(\d{3}年\d{1,2}月\d{1,2}日)發放股票股利([\d,]+)股', segment)
    cash = re.search(r'現金股利每股([\d.]+)元', segment)
    if not original or not receipt or not cash:
        raise ValueError('Missing explicit distribution and holdings')
    held = int(original[1].replace(',', ''))
    credited = int(receipt[2].replace(',', ''))
    date = dates(receipt[1])[0]
    if date[:4] != str(year):
        raise ValueError('Distribution is outside report year')
    # Join by issuer, annual period and BOTH cash/share allocations, never receipt date.
    matches = [r for r in ledger if r['code'] == '2880' and r['stock_ex_date'][:4] == str(year)
               and Decimal(r['cash_dividend']) == Decimal(cash[1])
               and int((Decimal(held) * Decimal(r['stock_dividend']) / 10).to_integral_value(rounding=ROUND_FLOOR)) == credited]
    if len(matches) != 1:
        raise ValueError('Public recipient allocation does not uniquely identify the event')
    event = matches[0]
    return dict(event_id='2880:stock:' + event['stock_ex_date'], code='2880', report_year=year,
                holder_scope='MOE_SCHOOL_ASSET_FUND', pdf_page=page_number, original_shares=held,
                reported_distribution_shares=credited, reported_distribution_date=date,
                ledger_payment_date=event['stock_payment_date'], ledger_date_corroborated=date == event['stock_payment_date'],
                evidence_status='PUBLIC_HOLDER_REPORTED_DISTRIBUTION', issuer_general_schedule_certified=False,
                model_holder_credit_certified=False, publication_vintage_certified=False,
                source_id=meta['id'], source_url=meta['url'], response_sha256=meta['response_sha256'], path=meta['path'])


def late_call_dates(text):
    match = re.search(r'另於催繳期間繳款之股東[^。]{0,100}?於(\d{2,4}年\d{1,2}月\d{1,2}日)將所認購之股數[，,]?撥入指定之集保帳戶', text)
    return dates(match[1]) if match else []


def main():
    with (ROOT / 'data/dividend_events/e22_dividend_events.csv').open() as handle:
        ledger = list(csv.DictReader(handle))
    manifest = json.loads((OUT / 'sources/targeted_issuers/manifest.json').read_text())
    public = []
    rejected = []
    for meta in manifest:
        if not re.fullmatch(r'moe_201[23]_financial_credit_evidence', meta['id']):
            continue
        packed = (ROOT / meta['path']).read_bytes()
        raw = gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest() != meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != meta['response_sha256']:
            raise ValueError('Public holder source hash mismatch')
        try:
            if meta['status'] != 'RESPONSE_SAVED_NEEDS_VALIDATION' or urlsplit(meta['url']).netloc != 'ws.moe.edu.tw' or not raw.startswith(b'%PDF-'):
                raise ValueError('Unvalidated public final account source')
            text = subprocess.run(['pdftotext', '-layout', '-', '-'], input=raw, capture_output=True, check=True).stdout.decode('utf8')
            public.append(public_holder_row(text, meta, ledger))
        except (ValueError, subprocess.CalledProcessError) as error:
            rejected.append(dict(id=meta['id'], reason=str(error)))
    with (OUT / 'mops_action_field_check.csv').open() as handle:
        actions = list(csv.DictReader(handle))
    limited = []
    for filing in load_statutory():
        for date in late_call_dates(filing['compact_text']):
            for action in actions:
                if statutory_subscription_identity(action, filing):
                    limited.append(dict(event_id=action['code'] + ':subscription:' + action['ex_date'],
                                        recipient_scope='PAID_DURING_LATE_CALL_WINDOW', scheduled_credit_date=date,
                                        general_delivery_certified=False, holder_subscription_assumed=False,
                                        source_id=filing['id'], source_url=filing['url'], response_sha256=filing['response_sha256']))
    result = dict(public_holder_distribution_rows=public, scoped_late_call_delivery_rows=limited, rejected=rejected,
                  general_gap_closure=False, backtest_ready=False,
                  limits=['Public final accounts describe the named public holder, not every shareholder',
                          'Late-call dates apply only to shareholders who paid during the stated late-call window',
                          'Retrospective reports do not certify the original announcement availability'])
    (OUT / 'scoped_delivery_evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(public_holder_rows=len(public), scoped_late_call_rows=len(limited), rejected=len(rejected))))


if __name__ == '__main__':
    main()
