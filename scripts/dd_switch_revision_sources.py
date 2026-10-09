#!/usr/bin/env python3
"""Capture complete returned annual indexes and candidate event filings, without certifying historical HTTP vintage."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
DEST = OUT / 'sources/mops_revisions'
KEYWORDS = re.compile(r'股利|除權|除息|盈餘分|資本公積|現金增資|現增|新股|催繳|配股|配息|配發|股東.{0,8}(?:重要|決議)|董事會.{0,8}(?:重要|決議事項)|董事會決議$')


def document(raw):
    tree = html.fromstring(raw.decode('utf-8'))
    for e in tree.xpath('//script | //style'):
        e.drop_tree()
    return tree, re.sub(r'\s+', '', tree.text_content())


def load_raw(meta):
    packed = (ROOT / meta['path']).read_bytes()
    raw = gzip.decompress(packed)
    if hashlib.sha256(packed).hexdigest() != meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest() != meta['response_sha256']:
        raise ValueError('Response hash mismatch: ' + meta['id'])
    return raw


def fetch(item, cache, timeout):
    old = cache.get(item['id'])
    if old and old['status'] in ('CAPTURED', 'VALID_EMPTY'):
        return old, load_raw(old)
    response = subprocess.run(['curl', '-L', '--max-time', str(timeout), '-sS', '-w', '\n%{http_code}', item['url']], capture_output=True)
    raw, _, status = response.stdout.rpartition(b'\n')
    path = DEST / (item['id'] + '.html.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    meta = dict(item, path=str(path.relative_to(ROOT)), retrieved_at=datetime.now(timezone.utc).isoformat(),
                http_status=status.decode(), response_sha256=hashlib.sha256(raw).hexdigest(),
                compressed_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), status='UNAVAILABLE')
    try:
        if response.returncode or status != b'200':
            raise ValueError('curl/HTTP error: '+response.stderr.decode(errors='replace')[:200])
        _, text = document(raw)
        if 'FORSECURITY' in text or '公開資訊觀測站' not in text:
            raise ValueError('Security or unrelated response')
        if item['kind'] == 'ANNUAL_INDEX':
            if '查無資料' in text or '資料庫中查無需求資料' in text:
                meta['status'] = 'VALID_EMPTY'
            elif '本資料由' in text and '發言日期' in text and '主旨' in text:
                meta['status'] = 'CAPTURED'
            else:
                raise ValueError('Unvalidated annual index')
        elif '本資料由' in text and '發言日期' in text and '說明' in text:
            meta['status'] = 'CAPTURED'
        else:
            raise ValueError('Unvalidated filing detail')
    except Exception as error:
        meta['error'] = str(error)
    return meta, raw


def index_items(codes):
    for code in sorted(codes):
        for year in range(2010, 2027):
            params = dict(firstin='true', TYPEK='all', co_id=code, year=year - 1911, month='', step=1, isnew='false')
            yield dict(id=f'{code}_{year}_annual', code=code, year=year, kind='ANNUAL_INDEX',
                       url='https://mopsov.twse.com.tw/mops/web/ajax_t05st01?' + urlencode(params))


def candidates(meta, raw):
    if meta['status'] != 'CAPTURED':
        return [], []
    tree, text = document(raw)
    if re.search(r'下一頁|nextPage', text, re.I):
        raise ValueError('Potential pagination must be resolved')
    all_rows, details = [], []
    for tr in tree.xpath('//tr'):
        pre, buttons = tr.xpath('.//pre'), tr.xpath('.//input[@onclick]')
        if not pre or not buttons:
            continue
        title = re.sub(r'\s+', '', ''.join(pre[0].itertext()))
        attrs = dict(re.findall(r"\.([A-Za-z_]+)\.value='([^']*)'", buttons[0].get('onclick')))
        required = {'spoke_date', 'spoke_time', 'seq_no', 'co_id', 'TYPEK'}
        if not required.issubset(attrs) or attrs['co_id'] != meta['code'] or not attrs['spoke_date'].startswith(str(meta['year'])):
            raise ValueError('Annual index identity/year mismatch')
        eligible = bool(KEYWORDS.search(title)) and '子公司' not in title and not re.search(r'代(?!號|表|理|收)',title)
        row = dict(code=meta['code'], year=meta['year'], title=title, **attrs, candidate=eligible, index_path=meta['path'])
        all_rows.append(row)
        if eligible:
            params = dict(firstin='true', step=2, isnew='false', **attrs)
            details.append(dict(id=f"{meta['code']}_{attrs['spoke_date']}_{attrs['spoke_time']}_{attrs['seq_no']}",
                                kind='DETAIL', code=meta['code'], year=meta['year'], title=title,
                                url='https://mopsov.twse.com.tw/mops/web/ajax_t05st01?' + urlencode(params)))
    if not all_rows:
        raise ValueError('No parsed filing rows in nonempty index')
    return all_rows, details


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--timeout', type=int, default=35)
    parser.add_argument('--indexes-only', action='store_true')
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    cache = {e['id']: e for e in manifest}
    old_path = OUT / 'sources/mops_actions/manifest.json'
    if old_path.exists():
        cache.update({e['id']: e for e in json.loads(old_path.read_text()) if e['id'] not in cache})
    with (ROOT / 'data/dividend_events/e22_dividend_events.csv').open() as f:
        codes = {r['code'] for r in csv.DictReader(f)} - {'0050'}
    entries, inventory, details = [], [], []
    def save():
        merged=dict(cache);merged.update({e['id']:e for e in entries})
        manifest_path.write_text(json.dumps(sorted(merged.values(), key=lambda e: e['id']), indent=2) + '\n')
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, (meta, raw) in enumerate(pool.map(lambda item: fetch(item, cache, args.timeout), index_items(codes)), 1):
            entries.append(meta)
            rows, next_items = candidates(meta, raw)
            inventory.extend(rows); details.extend(next_items)
            save()
            print('INDEX', i, meta['id'], meta['status'], 'candidates', len(next_items), flush=True)
    (OUT / 'mops_revision_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print('INDEXES_COMPLETE', len(entries), 'DETAILS', len(details), flush=True)
    if not args.indexes_only:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for i, (meta, raw) in enumerate(pool.map(lambda item: fetch(item, cache, args.timeout), details), 1):
                entries.append(meta); save()
                print('DETAIL', i, meta['id'], meta['status'], meta['title'], flush=True)
    print('COMPLETE', len(entries), flush=True)


if __name__ == '__main__':
    main()
