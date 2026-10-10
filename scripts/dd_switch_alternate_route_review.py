#!/usr/bin/env python3
"""Validate alternate source captures and separate public evidence from holder records."""
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
    results = []
    with zipfile.ZipFile(OUT / 'alternate_route_capture.zip') as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read('manifest.json'))
        for entry in manifest:
            packed = archive.read(entry['path'])
            raw = gzip.decompress(packed)
            assert hashlib.sha256(packed).hexdigest() == entry['compressed_sha256']
            assert hashlib.sha256(raw).hexdigest() == entry['response_sha256']
            # Observed ISIN results omit charset and contain Big5 bytes.
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                text = raw.decode('big5')
            row = dict(source_id=entry['id'], url=entry['url'], transport_status=entry['status'])
            if entry['status'] != 'RESPONSE_SAVED_NEEDS_VALIDATION':
                row.update(outcome='UNAVAILABLE', scope='No usable response; no absence inference')
            elif entry['id'] == 'remaining_material_2891_20120409_143826_1':
                flat = re.sub(r'\s+', '', html.unescape(re.sub('<[^>]+>', '', text)))
                assert '715,000仟股' in flat and '16.3元' in flat
                assert '11,654,500仟元' in flat and '業已收足股款' in flat
                assert '101年4月9日為增資基準日' in flat
                row.update(outcome='PRIMARY_ISSUER_FUNDING_TOTAL', event_id='2891:subscription:2012-02-10',
                           issued_shares=715000000, subscription_price_twd=16.3,
                           issuer_collected_total_twd=11654500000, capital_base_date='2012-04-09',
                           scope='Issuer-wide collection completion; no individual election or final ordinary delivery date')
            elif entry['id'].startswith('remaining_material_'):
                code = entry['id'].split('_')[2]
                assert '本資料由' in text and code in text
                titles = [html.unescape(re.sub('<[^>]+>', '', t)).strip()
                          for t in re.findall(r'<pre[^>]*>(.*?)</pre>', text, re.S | re.I)]
                relevant = [t for t in titles if not t.startswith('代') and '子公司' not in t
                            and any(k in t for k in ('增資', '股利', '發放', '股票', '股款'))]
                row.update(outcome='VALID_MONTH_INDEX', titles_reviewed=len(titles),
                           relevant_titles=relevant,
                           scope='Month material-announcement index only; not a complete statutory or issuer archive')
            elif entry['id'].startswith('remaining_isin_all_'):
                code = entry['id'].rsplit('_', 1)[1]
                assert '證券編碼' in text and code in text
                codes = re.findall(r'<td[^>]*>\s*(' + code + r'[A-Z]?)\s*</td>', text, re.I)
                assert code in codes, entry['id']
                row.update(outcome='ORDINARY_CODE_ONLY' if codes == [code] else 'REVIEW_CODES',
                           returned_codes=codes,
                           scope='Current partial-code query; no historical date selector or historical completeness claim')
            elif entry['id'] == 'remaining_mega_agent_exright_form':
                frames = re.findall(r'<iframe[^>]*src="([^"]+)"', text, re.I)
                assert 'https://moneydj.emega.com.tw/z/ze/zec/zeb.djhtm' in frames
                row.update(outcome='VENDOR_IFRAME', frames=frames,
                           scope='Broker-hosted market calendar delegates data to MoneyDJ; not issuer delivery proof')
            else:
                row.update(outcome='DISCOVERY_ONLY', scope='No certified event delivery or rights quote')
            results.append(row)
    inventory = list(csv.DictReader((OUT / 'comprehensive_remaining_gap_inventory.csv').open()))
    categories = ('STOCK_DELIVERY', 'SUBSCRIPTION_DELIVERY', 'RIGHTS_ORDINARY_PHASE')
    checklist = []
    for item in inventory:
        if item['category'] not in categories:
            continue
        subscription = item['category'] == 'SUBSCRIPTION_DELIVERY'
        checklist.append(dict(category=item['category'], event_id=item['event_id'],
                              public_evidence_needed=item['required_to_close'],
                              holder_record_needed='Paid election, quantity, payment date, funding source and account eligibility' if subscription else 'Account eligibility / actual balance for holder-specific execution',
                              public_search_can_prove_holder_record=False,
                              status='OPEN', backtest_permission=False))
    result = dict(captured_sources=manifest, source_reviews=results,
                  verified_source_hash_pairs=len(results), event_checklist=checklist,
                  category_counts={c: sum(r['category'] == c for r in checklist) for c in categories},
                  unique_events=len({r['event_id'] for r in checklist}),
                  new_certified_delivery_dates=0, rights_quotes_recovered=0,
                  gaps_closed=0, backtest_executed=False, canonical_modified=False)
    (OUT / 'alternate_route_review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with (OUT / 'remaining_evidence_responsibility.csv').open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(checklist[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(checklist)
    print(json.dumps({k: v for k, v in result.items() if k not in ('captured_sources', 'source_reviews', 'event_checklist')}))


if __name__ == '__main__':
    main()
