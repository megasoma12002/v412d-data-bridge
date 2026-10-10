#!/usr/bin/env python3
"""Review resumed captures without promoting secondary or partial evidence to facts."""
import csv
import gzip
import hashlib
import json
import re
import unicodedata
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'


def compact(raw):
    tree = html.fromstring(raw.decode('utf-8'))
    for node in tree.xpath('//script | //style'):
        node.drop_tree()
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', tree.text_content()))


def verified_body(meta):
    packed = (ROOT / meta['path']).read_bytes()
    raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest() != meta['compressed_sha256']:
        raise ValueError('Compressed hash mismatch: ' + meta['id'])
    if hashlib.sha256(raw).hexdigest() != meta['response_sha256']:
        raise ValueError('Response hash mismatch: ' + meta['id'])
    return raw


def secondary_hn_schedule(text, event):
    """Identify an allocation-specific lead, never authorize primary gap closure."""
    if event['code'] != '2880' or '華南金:本公司102年增資股票配發暨上市日期公告' not in text:
        return None
    if '提撥' + event['fiscal_year'] + '度盈餘' not in text:
        return None
    original = re.search(r'原已上市股票:普通股([\d,]+)股', text)
    issued = re.search(r'本次增資上市股票:普通股([\d,]+)股', text)
    date = re.search(r'預定增資新股股票發放及上市日期:(\d{3})年(\d{1,2})月(\d{1,2})日', text)
    method = '本次增資股票採無實體發行於股票發放當日直接撥入貴股東之集保帳戶'
    if not all((original, issued, date)) or method not in text or '權利證書' in text[:text.find(method)]:
        return None
    original_shares = int(original[1].replace(',', ''))
    issued_shares = int(issued[1].replace(',', ''))
    expected = int((Decimal(original_shares) * Decimal(event['stock_dividend']) / 10).to_integral_value(rounding=ROUND_FLOOR))
    if issued_shares != expected:
        return None
    date_value = f'{int(date[1]) + 1911:04d}-{int(date[2]):02d}-{int(date[3]):02d}'
    if date_value[:4] != event['stock_ex_date'][:4]:
        return None
    return dict(event_id='2880:stock:' + event['stock_ex_date'], candidate_general_delivery_date=date_value,
                ledger_payment_date=event['stock_payment_date'], ledger_date_matches=date_value == event['stock_payment_date'],
                original_shares=original_shares, issued_shares=issued_shares, allocation_amount_matches=True,
                delivery_date_clause=date[0], delivery_method_clause=method,
                source_scope='SECONDARY_ISSUER_NOTICE_REPRINT', primary_delivery_certified=False,
                gap_closed=False, publication_vintage_certified=False)


def main():
    manifest = json.loads((OUT / 'sources/targeted_issuers/manifest.json').read_text())
    rows = [m for m in manifest if m['id'].startswith('resume_')]
    captures = []
    raw_by_id = {}
    for meta in rows:
        raw = verified_body(meta)
        raw_by_id[meta['id']] = raw
        captures.append(dict(source_id=meta['id'], url=meta['url'], status=meta['status'],
                             response_bytes=len(raw), response_sha256=meta['response_sha256'],
                             compressed_sha256=meta['compressed_sha256'], http_status=meta['http_status'],
                             error=meta.get('error', ''), timeout_seconds=meta.get('timeout_seconds'),
                             transport_complete=meta['status'] == 'RESPONSE_SAVED_NEEDS_VALIDATION'))
    ledger_path = ROOT / 'data/dividend_events/e22_dividend_events.csv'
    ledger = list(csv.DictReader(ledger_path.open()))
    event = next(r for r in ledger if r['code'] == '2880' and r['stock_ex_date'] == '2013-08-15')
    source_id = 'resume_hn_2013_original_notice_reprint'
    source_meta = next(m for m in rows if m['id'] == source_id)
    candidate = None
    if source_meta['status'] == 'RESPONSE_SAVED_NEEDS_VALIDATION':
        candidate = secondary_hn_schedule(compact(raw_by_id[source_id]), event)
    if candidate:
        candidate.update(source_id=source_id, source_url=source_meta['url'], response_sha256=source_meta['response_sha256'])
    comparisons = []
    # Compare the candidate title against saved primary indexes, not search snippets.
    for folder, index_id in [('mops_revisions', '2880_2013_annual'), ('mops_statutory', 't59sb09_2880_2013_index')]:
        primary = json.loads((OUT / 'sources' / folder / 'manifest.json').read_text())
        meta = next(r for r in primary if r['id'] == index_id)
        text = compact(verified_body(meta))
        title = '102年增資股票配發暨上市日期公告'
        comparisons.append(dict(index_id=index_id, status=meta['status'], url=meta['url'],
                                response_sha256=meta['response_sha256'], candidate_title_present=title in text,
                                conclusion='Candidate title absent from this saved index' if title not in text else 'Candidate title found',
                                historical_inventory_certified=False))
    assessments = {
        'resume_esun_official_shareholder_information': 'Official page supports 2023 subscription terms and payment window; no final ordinary conversion delivery notice. 2014/2017 delivery gaps remain.',
        'resume_mega_2013_official_annual': '2013 report execution table concerns 2013 cash dividend; it cannot prove target 2011/2012 ordinary stock delivery.',
        'resume_hn_2013_original_notice_reprint': 'Allocation-specific general book-entry delivery lead supported by reprint; primary original and historical version provenance still required.',
        'resume_hn_2011_official_prospectus_complete_60s': 'Complete prospectus received. Reviewed issuer capital/dividend sections: no target dated general stock delivery. Prospective 2011 subscription terms do not prove final delivery.',
    }
    for capture in captures:
        capture['assessment'] = assessments.get(capture['source_id'], 'Incomplete or failed transfer excluded from delivery evidence')
        capture['gap_closed'] = False
    result = dict(captures=captures, secondary_delivery_leads=[candidate] if candidate else [],
                  primary_index_comparison=comparisons, ledger_sha256=hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
                  capture_count=len(captures), completed_transfers=sum(r['transport_complete'] for r in captures),
                  new_primary_delivery_facts=0, gaps_closed=0, backtest_ready=False,
                  backtest_executed=False, canonical_modified=False,
                  limits=['Transport success is not evidence validation', 'Partial PDFs remain excluded even if text is recoverable',
                          'Secondary reprints cannot close primary-source requirements',
                          'Absence from a current index does not prove the notice never existed',
                          'No rights/ordinary quote or holder subscription evidence was fabricated'])
    (OUT / 'resumed_delivery_review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['capture_count', 'completed_transfers', 'gaps_closed', 'backtest_ready', 'backtest_executed']}))


if __name__ == '__main__':
    main()
