#!/usr/bin/env python3
"""Review preserved historical rules without certifying event delivery or fills."""
import csv
import gzip
import hashlib
import html
import json
import re
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'repro/dd-switch-full-history-audit'


def main():
    archive = OUT / 'rights_rule_followup_capture.zip'
    texts = {}
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest = json.loads(z.read('manifest.json'))
        for r in manifest:
            compressed = z.read(r['path'])
            raw = gzip.decompress(compressed)
            assert hashlib.sha256(compressed).hexdigest() == r['compressed_sha256'], r['id']
            assert hashlib.sha256(raw).hexdigest() == r['response_sha256'], r['id']
            texts[r['id']] = re.sub(r'\s+', '', html.unescape(re.sub('<[^>]+>', '', raw.decode(errors='replace'))))
    historical = texts['rights_tdcc_conversion_rule_20060327']
    current = texts['rights_tdcc_conversion_rule_current']
    trading = texts['rights_trading_rule_20110112']
    assert '民國95年03月27日' in historical
    assert '新股上市(櫃)日' in historical and '向發行公司辦理換發' in historical
    assert '是否有符合交割條件之餘額' in historical
    assert '向發行人辦理換發' in current
    assert '民國100年01月12日' in trading
    assert '前三個營業日停止申報買賣' in trading
    assert '英文字母L-Z' in texts['rights_security_code_rule_20091112']
    # A general rule supplies a conditional schedule, never proof that a holder
    # received or paid for shares or that a particular conversion completed.
    leads = {r['event_id']: r for r in json.loads((OUT / 'github_lead_followup_review.json').read_text())['secondary_listing_leads']}
    ctbc = json.loads((OUT / 'ctbc_2013_final_lead_review.json').read_text())
    leads['2891:subscription:2013-02-19'] = dict(candidate_ordinary_listing_date=ctbc['candidate_ordinary_listing_date'], source_id='ctbc_2013_final_mobile_reprint')
    rows = []
    for r in csv.DictReader((OUT / 'remaining_subscription_delivery_gaps.csv').open()):
        event = r['code'] + ':subscription:' + r['ex_date']
        lead = leads.get(event, {})
        date = r['new_share_listing_date'] or lead.get('candidate_ordinary_listing_date')
        primary = bool(r['new_share_listing_date'])
        rows.append(dict(event_id=event, voucher_date=r['subscription_voucher_delivery_date'],
                         rule_scheduled_conversion_date=date,
                         date_basis='PRIMARY_LISTING' if primary else 'SECONDARY_LISTING_LEAD',
                         listing_source_id=r['listing_source_id'] or lead.get('source_id'),
                         rule_source_id='rights_tdcc_conversion_rule_20060327' if date < '2017-12-21' else 'rights_tdcc_conversion_rule_current',
                         actual_conversion_certified=False, holder_payment_certified=False,
                         gap_closed=False, status='CONDITIONAL_RULE_SCHEDULE_ONLY'))
    for r in json.loads((OUT / 'legacy_rights_phase_review.json').read_text())['rows']:
        rows.append(dict(event_id=r['event_id'], rights_date=r['rights_issue_date'],
                         rule_scheduled_conversion_date=r['ordinary_listing_date'],
                         date_basis='PRIMARY_LISTING', listing_source_id=r['source_id'],
                         rule_source_id='rights_tdcc_conversion_rule_20060327',
                         actual_conversion_certified=False, gap_closed=False,
                         status='CONDITIONAL_RULE_SCHEDULE_ONLY'))
    for r in rows:
        if r['date_basis'] == 'PRIMARY_LISTING':
            year, month, day = map(int, r['rule_scheduled_conversion_date'].split('-'))
            date_text = f'{year - 1911}年{month}月{day}日'
            assert date_text in texts[r['listing_source_id']], r['event_id']
    result = dict(rows=rows, captured_sources=manifest, verified_source_hash_pairs=len(manifest),
                  rule_supported_schedules=len(rows), primary_listing_schedules=sum(r['date_basis']=='PRIMARY_LISTING' for r in rows),
                  secondary_listing_schedules=sum(r['date_basis']=='SECONDARY_LISTING_LEAD' for r in rows),
                  quotes_recovered=0, new_certified_event_delivery_dates=0,
                  backtest_ready=False, backtest_executed=False, canonical_modified=False,
                  limitations=['General conversion rules do not certify event completion, holder payment or vintage.',
                               'No rights code is assigned from the L-Z rule alone.',
                               'Ordinary OHLCV is not substituted for temporary rights prices.',
                               'Historical trading rule applies to 2011/2012; current rule alone is not backdated.',
                               'Three remaining TWSE market requests were skipped after the first source block.'])
    (OUT / 'rights_rule_followup_review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','captured_sources','limitations')}))


if __name__ == '__main__':
    main()
