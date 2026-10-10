#!/usr/bin/env python3
"""Review bounded transfer-agent/prospectus followups without closing evidence gaps."""
import hashlib
import json
import re
import unicodedata

import fitz
from lxml import html
from dd_switch_resumed_delivery_review import OUT, verified_body
from pathlib import Path


def main():
    rows = [r for r in json.loads((OUT / 'sources/targeted_issuers/manifest.json').read_text())
            if r['id'].startswith('followup_')]
    expected = {'followup_hn_transfer_agent_news', 'followup_hn_transfer_agent_weekly',
                'followup_hn_transfer_agent_companies', 'followup_hn_transfer_agent_company',
                'followup_ctbc_2013_official_prospectus'}
    if {r['id'] for r in rows} != expected or len(rows) != len(expected):
        raise ValueError('Unexpected followup batch; each source needs explicit review')
    captures = []
    for row in rows:
        raw = verified_body(row)
        item = {k: row[k] for k in ('id', 'url', 'status', 'retrieved_at',
                                   'response_sha256', 'compressed_sha256')}
        item.update(response_bytes=len(raw), gap_closed=False)
        if row['status'] != 'RESPONSE_SAVED_NEEDS_VALIDATION':
            item['assessment'] = 'Incomplete transport cannot certify delivery.'
        elif raw.startswith(b'%PDF'):
            if not raw.rstrip().endswith(b'%%EOF'):
                raise ValueError('Missing PDF EOF')
            doc = fitz.open(stream=raw, filetype='pdf')
            pages = [re.sub(r'\s+', '', unicodedata.normalize('NFKC', p.get_text())) for p in doc]
            if len(doc) != 848 or '中國信託金融控股股份有限公司' not in pages[0] or '102年2月1日' not in pages[2]:
                raise ValueError('Prospectus identity, vintage or page count mismatch')
            terms = ['股票發放', '股票交付', '股款繳納憑證', '上市日期']
            item.update(pdf_pages=len(doc), pdf_eof_verified=True,
                        text_hits=[dict(pdf_page=i + 1, term=term,
                                        context=s[max(0, s.find(term)-80):s.find(term)+180])
                                   for i, s in enumerate(pages) for term in terms if term in s],
                        assessment='2013-02-01 prospectus: capital history records 2012-04 issuance; '
                        'the listing-date hit concerns the company original listing, not new-share delivery. '
                        'No target ordinary delivery clause found in extracted text; gap remains open. '
                        'Text search is not proof of historical notice absence.')
        else:
            tree = html.fromstring(raw.decode('utf-8'))
            for node in tree.xpath('//script | //style'):
                node.drop_tree()
            text = re.sub(r'\s+', '', unicodedata.normalize('NFKC', tree.text_content()))
            item.update(target_year_tokens_present=[t for t in ['99年', '100年', '101年', '102年'] if t in text],
                        assessment='Current transfer-agent snapshot does not supply the target 2010–2013 '
                        'general stock or subscription ordinary delivery clause. No historical absence inference.')
            if row['id'] == 'followup_hn_transfer_agent_company':
                if not all(t in text for t in ['2880', '華南金融控股股份有限公司', '70826764']):
                    raise ValueError('Transfer-agent issuer identity mismatch')
                item['issuer_identity_verified'] = True
                item['assessment'] += ' Visible history is 114/115; cash payment 115/8/28 is not stock delivery proof.'
        captures.append(item)
    report = dict(captures=captures, verified_source_hash_pairs=len(captures),
                  completed_transports=sum(r['status'] == 'RESPONSE_SAVED_NEEDS_VALIDATION' for r in rows),
                  new_primary_delivery_facts=0, backtest_ready=False, backtest_executed=False,
                  background_capture_jobs=0,
                  review_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT / 'followup_delivery_review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'captures'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
