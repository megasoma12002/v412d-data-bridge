#!/usr/bin/env python3
"""Bounded read-only queries of the observed SITCA public disclosure form."""
import argparse
import re
import gzip
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from lxml import html
from dd_switch_targeted_capture import source_blocked

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
DEST = OUT / 'sources/targeted_issuers'
URL = 'https://www.sitca.org.tw/ROC/MemNews/MN2001N.aspx?PGMID=SD0202'
PREFIX = 'ctl00$ctl00$ContentPlaceHolder1$ContentPlaceHolder1$'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--company', choices=['A0005', 'A0013'], action='append')
    parser.add_argument('--suffix', default='')
    parser.add_argument('--timeout-seconds', type=int, choices=[15, 30], default=15)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9_]*', args.suffix):
        parser.error('suffix must contain lowercase letters, digits or underscores')
    batch = 'sitca_observed_archive_query' + ('_' + args.suffix if args.suffix else '')
    if (OUT / (batch + '_progress.json')).exists():
        raise ValueError('Existing batch monitor must be preserved; choose a new suffix')
    manifest = DEST / 'manifest.json'
    rows = json.loads(manifest.read_text())
    index = next(r for r in rows if r['id'] == 'historical_catalog_index_single_retry')
    packed = (ROOT / index['path']).read_bytes()
    raw = gzip.decompress(packed)
    assert digest(packed) == index['compressed_sha256'] and digest(raw) == index['response_sha256']
    assert index['status'] == 'RESPONSE_SAVED_NEEDS_VALIDATION' and b'</html>' in raw.lower()
    tree = html.fromstring(raw.decode('utf-8'))
    form = tree.xpath('//form')[0]
    assert form.get('action') == './MN2001N.aspx?PGMID=SD0202'
    defaults = {}
    for e in form.xpath('.//input[@type="hidden"]|.//input[@type="text"]|.//select'):
        if e.tag == 'select':
            options = e.xpath('./option[@selected]') or e.xpath('./option')[:1]
            defaults[e.get('name')] = options[0].get('value', '')
        else:
            defaults[e.get('name')] = e.get('value', '')
    # Only public company/class/period/title filters; no state-changing endpoint.
    selections = dict(ddl_Form='02', RadioButtonList1='All', TextBox1='卓越', DropDownList1='')
    queue = []
    for company in (args.company or ['A0005', 'A0013']):
        fields = dict(defaults)
        fields.update({PREFIX + k: v for k, v in dict(selections, ddl_Comid=company).items()})
        fields[PREFIX + 'btnQuery'] = '查詢'
        for k, v in dict(selections, ddl_Comid=company).items():
            controls = form.xpath('.//*[@name=$name]', name=PREFIX + k)
            assert controls, k
            if controls[0].tag == 'select':
                assert v in [o.get('value', '') for o in controls[0].xpath('./option')], (k, v)
        body = urlencode(fields).encode()
        identity = batch + '_' + company
        if any(r['id'] == identity for r in rows):
            raise ValueError('Existing snapshot must be preserved; choose a new suffix')
        request_path = DEST / (identity + '.request.gz')
        request_path.write_bytes(gzip.compress(body, mtime=0))
        queue.append(dict(id=identity, url=URL, method='POST', kind='PUBLIC_READ_ONLY_DISCLOSURE_QUERY',
                          company=company, period='All', keyword='卓越', form_category='02', timeout_seconds=args.timeout_seconds,
                          request_path=str(request_path.relative_to(ROOT)), request_sha256=digest(body),
                          request_compressed_sha256=digest(request_path.read_bytes()),
                          observed_form_source_id=index['id']))
    (OUT / (batch + '_queue.json')).write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n')
    state = dict(status='RUNNING', total=len(queue), processed=0, success=0, failed=0, started_at=now(), recent_results=[])

    def save():
        state['updated_at'] = now()
        (OUT / (batch + '_progress.json')).write_text(json.dumps(state, indent=2) + '\n')
        manifest.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(state), flush=True)

    for item in queue:
        state['current_id'] = item['id']; save(); time.sleep(2)
        temp = ROOT / 'tmp/sitca_public_query_body.txt'
        temp.write_bytes(gzip.decompress((ROOT / item['request_path']).read_bytes()))
        result = subprocess.run(['curl', '-L', '--compressed', '--max-time', str(args.timeout_seconds), '-sS',
                                 '--data-binary', '@' + str(temp), '-w', '\n%{http_code}', URL], capture_output=True)
        response, _, status = result.stdout.rpartition(b'\n')
        temp.unlink()
        blocked = source_blocked(response, URL, status)
        good = result.returncode == 0 and status == b'200' and not blocked
        path = DEST / (item['id'] + '.html.gz'); path.write_bytes(gzip.compress(response, mtime=0))
        meta = dict(item, status='SOURCE_BLOCKED' if blocked else 'RESPONSE_SAVED_NEEDS_VALIDATION' if good else 'FAILED',
                    path=str(path.relative_to(ROOT)), response_sha256=digest(response), compressed_sha256=digest(path.read_bytes()),
                    http_status=status.decode(), retrieved_at=now(), error=result.stderr.decode(errors='replace'))
        rows[:] = [r for r in rows if r['id'] != item['id']] + [meta]
        state['processed'] += 1; state['success'] += int(good); state['failed'] += int(not good)
        state['last_completed_at'] = now(); state['recent_results'].append(dict(id=item['id'], status=meta['status']))
        if blocked:
            state.update(status='STOPPED_SOURCE_BLOCK', skipped=state['total']-state['processed'], current_id=''); save(); return
        save()
    state.update(status='COMPLETE', current_id='', skipped=0); save()


if __name__ == '__main__':
    main()
