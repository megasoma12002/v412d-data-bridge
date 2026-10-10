#!/usr/bin/env python3
"""Verify saved GitHub followups; preserve secondary leads without closing gaps."""
import gzip
import hashlib
import json
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'repro/dd-switch-full-history-audit'


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def verified(z, row, path, raw_key):
    packed = z.read(path)
    if hashlib.sha256(packed).hexdigest() != row['compressed_sha256']:
        raise ValueError('Compressed hash mismatch: ' + path)
    raw = gzip.decompress(packed)
    if hashlib.sha256(raw).hexdigest() != row[raw_key]:
        raise ValueError('Response hash mismatch: ' + path)
    return raw


def main():
    archive = OUT / 'github_lead_followup_capture.zip'
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('Archive CRC mismatch')
        targets = json.loads(z.read('targeted_manifest.json'))
        news = json.loads(z.read('github_news_manifest.json'))['captures']
        captures, bodies = [], {}
        for row in targets:
            raw = verified(z, row, row['path'], 'response_sha256')
            parser = VisibleText()
            parser.feed(raw.decode('utf-8', errors='replace'))
            body = re.sub(r'\s+', '', ''.join(parser.parts))
            bodies[row['id']] = body
            item = {k: row[k] for k in ('id', 'url', 'status', 'path', 'retrieved_at',
                                       'response_sha256', 'compressed_sha256')}
            item['bytes'] = len(raw)
            item['gap_closed'] = False
            if row['status'] != 'RESPONSE_SAVED_NEEDS_VALIDATION':
                item['assessment'] = 'Failed/incomplete transport; excluded as evidence.'
            elif '_t59sb09_' in row['id']:
                if '公告內容' in body:
                    raise ValueError('Unexpected populated primary response requires new review')
                item['assessment'] = 'HTTP 200 empty MOPS shell; no issuer announcement body. Not proof of absence.'
            else:
                item['assessment'] = 'Secondary reprint, not independently certified primary/vintage evidence.'
            captures.append(item)
        for row in news:
            raw = verified(z, row, row['saved_path'], 'sha256')
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if row['status'] != 'VERIFIED_MIRROR' or blob != row['git_blob_sha']:
                raise ValueError('GitHub mirror blob mismatch')

        # Require the precise event quantities and both distinct stage dates.
        specs = [
            ('github_lead_ctbc_2012_final_reprint', '2891:subscription:2012-02-10',
             '中信金', '715,000,000', '101年4月30日', '101年4月12日',
             '2012-04-30', '2012-04-12', 't59sb09_2891_20120409_20120409_1'),
            ('github_lead_hn_2011_final_mobile_reprint', '2880:subscription:2011-11-07',
             '華南金', '1,200,000,000', '101年2月7日', '100年12月29日',
             '2012-02-07', '2011-12-29', 't59sb09_2880_20111226_20111223_1'),
        ]
        leads = []
        source = {r['id']: r for r in targets}
        for ident, event, issuer, qty, listing, voucher, listing_iso, voucher_iso, primary in specs:
            body = bodies[ident]
            if source[ident]['status'] != 'RESPONSE_SAVED_NEEDS_VALIDATION' or not all(
                    t in body for t in (issuer, qty, listing, voucher, '普通股上市暨股款繳納憑證終止上市')):
                raise ValueError('Secondary event identity or stage mismatch: ' + ident)
            leads.append(dict(event_id=event, source_id=ident, source_url=source[ident]['url'],
                              response_sha256=source[ident]['response_sha256'],
                              candidate_ordinary_listing_date=listing_iso,
                              earlier_book_entry_date=voucher_iso,
                              earlier_stage='SUBSCRIPTION_VOUCHER_PER_PRIOR_PRIMARY_NOTICE',
                              corroborating_primary_voucher_id=primary,
                              general_ordinary_delivery_date=None,
                              source_class='SECONDARY_REPRINT_NOT_PROMOTED',
                              primary_original_required=True, gap_closed=False))
        body = bodies['github_lead_ctbc_2013_registration_reprint']
        if not all(t in body for t in ('1,333,400,000', '102年4月17日', '股款繳納憑證', '另行公告')):
            raise ValueError('CTBC 2013 registration reprint identity mismatch')
    report = dict(captures=captures, github_news_captures=news,
                  secondary_listing_leads=leads, new_primary_delivery_facts=0,
                  verified_source_hash_pairs=len(targets) + len(news),
                  archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                  review_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  backtest_ready=False, backtest_executed=False,
                  canonical_modified=False, background_capture_jobs=0,
                  limitations=['Four selected mirror files are not a complete news archive.',
                               'Empty MOPS shells and no matching mirror rows do not prove historical absence.'])
    (OUT / 'github_lead_followup_review.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('verified_source_hash_pairs',
          'new_primary_delivery_facts', 'background_capture_jobs')}))


if __name__ == '__main__':
    main()
