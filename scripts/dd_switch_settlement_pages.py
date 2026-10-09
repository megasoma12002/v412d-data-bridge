#!/usr/bin/env python3
"""Extract public dividend payment schedules from authenticated issuer/agent tables."""
import argparse
import csv
import gzip
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import pandas as pd
from dd_switch_mops_evidence import day, number

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
DEST = OUT / 'sources/settlement_pages'
URLS = dict(mega_history='https://www.megaholdings.com.tw/tc/stock.aspx',
            esun_history='https://www.esunfhc.com/zh-tw/investor-relations/shareholders/shareholder-Information',
            tcfhc_dividend='https://www.tcfhc.com.tw/investors-relations/shareholder-service/dividend',
            hnfhc_agent='https://www.entrust.com.tw/entrust/agent/comIn.do?cpcmpno=1A&type=2',
            first_history='https://ir.firstholding.com.tw/c/ir_dividend.php',
            ctbc_agent='https://ecorp.ctbcbank.com/cts/static/ag_dividend.jsp',
            twm_history='https://corp.taiwanmobile.com/investor-relations/shareholder-information-2.html')


def date(value):
    value = re.sub(r'\s+', '', str(value))
    if value in ('', '-', 'nan', 'None'):
        return ''
    value = value.replace('年', '/').replace('月', '/').replace('日', '').replace('.', '/')
    return day(value)


def fetch(item):
    name, url = item
    r = subprocess.run(['curl', '-L', '--max-time', '40', '-sS', '-w', '\n%{http_code}', url], capture_output=True)
    raw, _, status = r.stdout.rpartition(b'\n')
    f = DEST / (name + '.html.gz'); f.write_bytes(gzip.compress(raw, mtime=0))
    return dict(id=name, url=url, path=str(f.relative_to(ROOT)), response_sha256=hashlib.sha256(raw).hexdigest(),
                compressed_sha256=hashlib.sha256(f.read_bytes()).hexdigest(), http_status=status.decode(),
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                status='HTTP_CAPTURED_NEEDS_SCHEMA_VALIDATION' if r.returncode == 0 and status == b'200' else 'UNAVAILABLE')


def extract(meta, raw, ledger):
    if meta['status'] == 'UNAVAILABLE':
        return []
    name = meta['id']
    # Pages without a historical payment table are retained as access evidence only.
    if name not in ('mega_history', 'esun_history', 'hnfhc_agent', 'ctbc_agent'):
        return []
    tables = pd.read_html(StringIO(raw.decode('utf-8')), keep_default_na=False)
    output = []
    def add(code, leg, ex, record, payment, amount):
        if not payment or number(str(amount)) <= 0:
            return
        matches = [r for r in ledger if r['code'] == code and number(r[leg + '_dividend']) > 0 and
                   (r[leg + '_ex_date'] == ex if ex else r['record_date'] == record)]
        if len(matches) != 1:
            return
        event = matches[0]
        output.append(dict(code=code, leg=leg, ex_date=event[leg + '_ex_date'], record_date=record,
                           payment_date=payment, amount=str(amount), identity_match='EX_DATE' if ex else 'RECORD_DATE',
                           amount_matches=abs(number(str(amount))-number(event[leg+'_dividend'])) <= number('0.00000001'),
                           url=meta['url'], path=meta['path'], response_sha256=meta['response_sha256'],
                           retrieved_at=meta['retrieved_at'], source_id=meta['id'], publication_vintage_certified=False))
    for table in tables:
        columns = [tuple(re.sub(r'\s+', '', str(v)) for v in c) if isinstance(c, tuple) else re.sub(r'\s+', '', str(c)) for c in table.columns]
        table.columns = columns
        if name == 'mega_history':
            required = [('除權息交易日','除權息交易日'), ('現金股利發放日','現金股利發放日'), ('股票股利發放日','股票股利發放日')]
            if not all(c in columns for c in required):
                continue
            for row in table.to_dict('records'):
                ex = date(row[required[0]])
                add('2886','cash',ex,'',date(row[required[1]]), row[('現金股利','現金股利')])
                stock = number(str(row[('股票股利','盈餘配股')]).replace('-','')) + number(str(row[('股票股利','公積配股')]).replace('-',''))
                add('2886','stock',ex,'',date(row[required[2]]),stock)
        elif name == 'esun_history':
            if ('現金股利','除息基準日') not in columns or ('股票股利','發放日') not in columns:
                continue
            for row in table.to_dict('records'):
                for leg, label, record_label in [('cash','現金股利','除息基準日'), ('stock','股票股利','除權基準日')]:
                    amount = row[(label,'每股新臺幣(元)')]
                    if str(amount) in ('','-'):
                        continue
                    add('2884',leg,'',date(row[(label,record_label)]),date(row[(label,'發放日')]),amount)
        elif name == 'hnfhc_agent':
            if '每股現金股利(元)' not in columns or '發放日' not in columns:
                continue
            for row in table.to_dict('records'):
                if not re.fullmatch(r'\d+(?:\.\d+)?',str(row['每股現金股利(元)'])) or not re.fullmatch(r'\d{2,4}年\d{1,2}月\d{1,2}日',str(row['除息交易日'])):
                    continue  # Nested expanded detail rows, not payment table records.
                add('2880','cash',date(row['除息交易日']),'',date(row['發放日']),row['每股現金股利(元)'])
        elif name == 'ctbc_agent':
            if '證券代號' not in columns or '每股現金股利（元）' not in columns or '發放日' not in columns:
                continue
            for row in table.to_dict('records'):
                add(str(row['證券代號']),'cash',date(row['除息交易日']),'',date(row['發放日']),row['每股現金股利（元）'])
    return list({(r['code'],r['leg'],r['ex_date'],r['payment_date'],r['amount']):r for r in output}.values())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fetch',action='store_true');args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    if args.fetch:
        manifest=[]
        with ThreadPoolExecutor(max_workers=3) as pool:
            for entry in pool.map(fetch,URLS.items()):
                manifest.append(entry);(DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (ROOT/'data/dividend_events/e22_dividend_events.csv').open() as f:ledger=list(csv.DictReader(f))
    rows=[]
    for meta in json.loads((DEST/'manifest.json').read_text()):
        packed=(ROOT/meta['path']).read_bytes();raw=gzip.decompress(packed)
        if hashlib.sha256(packed).hexdigest()!=meta['compressed_sha256'] or hashlib.sha256(raw).hexdigest()!=meta['response_sha256']:
            raise ValueError('Issuer page hash mismatch')
        rows.extend(extract(meta,raw,ledger))
    (OUT/'issuer_payment_schedule_facts.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('issuer payment facts',len(rows),'amount conflicts',sum(not r['amount_matches'] for r in rows))


if __name__=='__main__':main()
