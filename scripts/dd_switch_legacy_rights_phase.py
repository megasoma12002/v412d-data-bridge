#!/usr/bin/env python3
"""Extract explicit rights stages from two preserved primary Mega notices."""
import csv
import json
import re
from decimal import Decimal, ROUND_FLOOR
from dd_switch_resumed_delivery_review import ROOT, OUT, compact, verified_body


def parse_phase(text, event):
    year = int(event['stock_ex_date'][:4]) - 1911
    if event['code'] != '2886' or '公司代號2886' not in text or f'本公司{year}年增資股票發放及上市日期公告' not in text:
        raise ValueError('Issuer/year mismatch')
    original = re.search(r'原已上市普通股股票:([\d,]+)股', text)
    issued = re.search(r'本次增資上市普通股股票:([\d,]+)股', text)
    ordinary = re.search(r'普通股股票訂於民國(\d+)年(\d+)月(\d+)日.*?正式上市買賣', text)
    rights = re.search(r'原(\d+)年(\d+)月(\d+)日.*?發行之新股權利證書亦同時終止上市', text)
    if not all((original, issued, ordinary, rights)):
        raise ValueError('Explicit stage or allocation clause missing')
    issued_qty = int(issued[1].replace(',', ''))
    expected = int((Decimal(original[1].replace(',', '')) * Decimal(event['stock_dividend']) / 10).to_integral_value(rounding=ROUND_FLOOR))
    if issued_qty != expected:
        raise ValueError('Allocation amount mismatch')
    def day(match):
        return f'{int(match[1])+1911:04d}-{int(match[2]):02d}-{int(match[3]):02d}'
    early, final = day(rights), day(ordinary)
    if not early < final or final[:4] != event['stock_ex_date'][:4]:
        raise ValueError('Stage chronology mismatch')
    return dict(event_id='2886:stock:' + event['stock_ex_date'], rights_issue_date=early,
                ordinary_listing_date=final, rights_termination_date=final,
                issued_shares=issued_qty, allocation_amount_matches=True,
                ledger_payment_date=event['stock_payment_date'],
                primary_explicit_stage_supported=True, general_ordinary_delivery_certified=False,
                gap_closed=False, publication_vintage_certified=False,
                required_to_close='Rights prices, units and holder trade eligibility; explicit general ordinary delivery/conversion proof')


def main():
    ledger = list(csv.DictReader((ROOT / 'data/dividend_events/e22_dividend_events.csv').open()))
    manifest = json.loads((OUT / 'sources/mops_statutory/manifest.json').read_text())
    rows = []
    for ex, source_id in [('2011-08-23', 't59sb09_2886_20110913_20110913_1'),
                          ('2012-08-08', 't59sb09_2886_20120831_20120831_1')]:
        event = next(r for r in ledger if r['code'] == '2886' and r['stock_ex_date'] == ex)
        source = next(r for r in manifest if r['id'] == source_id)
        if source['status'] != 'CAPTURED':
            raise ValueError('Primary original not captured')
        row = parse_phase(compact(verified_body(source)), event)
        row.update(source_id=source_id, source_url=source['url'], response_sha256=source['response_sha256'])
        rows.append(row)
    result = dict(rows=rows, primary_source_hash_pairs_verified=2,
                  new_general_delivery_facts=0, backtest_ready=False, backtest_executed=False)
    (OUT / 'legacy_rights_phase_review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
