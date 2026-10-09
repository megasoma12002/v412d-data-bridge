#!/usr/bin/env python3
"""Bounded serial retries with a persisted progress checkpoint and a source-block gate."""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import dd_switch_revision_sources as major
import dd_switch_statutory_sources as statutory

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'repro/dd-switch-full-history-audit'
PROGRESS=OUT/'monitored_capture_progress.json'

def now():return datetime.now(timezone.utc).isoformat()

def blocked(raw):
    return bool(re.search(r'overrun|too\s*many\s*query|查詢過於頻繁|for\s*security',raw.decode('utf-8',errors='replace'),re.I))

def save(state):
    temp=PROGRESS.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(PROGRESS)
    line=f"{state['status']} | {state['processed']}/{state['total']} | success={state['success']} failed={state['failed']} | last={state.get('last_completed_at','-')} | {state.get('current_id','')}"
    print(line,flush=True)
    summary=os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as h:h.write(line+'\n\n')

def advance(state,meta,raw):
    state['processed']+=1
    state['attempted_ids'].append(meta['id'])
    good=meta['status'] in ('CAPTURED','VALID_EMPTY')
    state['success']+=int(good);state['failed']+=int(not good)
    state['consecutive_failures']=0 if good else state['consecutive_failures']+1
    state['last_completed_at']=now();state['last_result']=meta['status']
    state['recent_results']=(state.get('recent_results',[])+[dict(id=meta['id'],status=meta['status'],at=state['last_completed_at'],error='' if good else meta.get('error',''))])[-10:]
    if blocked(raw):state.update(status='STOPPED_SOURCE_BLOCK',stop_reason='Official source returned Overrun/security response')
    elif state['consecutive_failures']>=3:state.update(status='STOPPED_FAILURE_LIMIT',stop_reason='Three consecutive unsuccessful requests')
    return state

def main():
    p=argparse.ArgumentParser();p.add_argument('--probe',action='store_true');p.add_argument('--batch-size',type=int,default=10);args=p.parse_args()
    caches={};modules={'mops_revisions':major,'mops_statutory':statutory}
    for name in modules:
        path=OUT/'sources'/name/'manifest.json';caches[name]={r['id']:r for r in json.loads(path.read_text())}
    pending=[dict(source=name,**r) for name,cache in caches.items() for r in cache.values() if r['status']=='UNAVAILABLE' and r['kind'] in ('DETAIL','STATUTORY_DETAIL')]
    if args.probe or not PROGRESS.exists():
        state=dict(started_at=now(),status='PROBE',total=len(pending),processed=0,success=0,failed=0,consecutive_failures=0,attempted_ids=[],probe_passed=False,queue=[dict(source=r['source'],id=r['id']) for r in pending])
    else:state=json.loads(PROGRESS.read_text())
    if state['status'].startswith('STOPPED'):save(state);return 42
    queue=[r for r in state['queue'] if r['id'] not in state['attempted_ids']]
    limit=5 if args.probe else args.batch_size
    for item in queue[:limit]:
        name=item['source'];old=caches[name][item['id']]
        state.update(status='PROBE' if args.probe else 'FETCHING',current_id=old['id'],current_started_at=now());save(state)
        meta,raw=modules[name].fetch(old,caches[name],15)
        if meta['status'] in ('CAPTURED','VALID_EMPTY'):meta.pop('error',None)
        caches[name][meta['id']]=meta
        path=OUT/'sources'/name/'manifest.json';path.write_text(json.dumps(sorted(caches[name].values(),key=lambda r:r['id']),indent=2)+'\n')
        advance(state,meta,raw);save(state)
        if state['status'].startswith('STOPPED'):return 42
    if args.probe:
        state['probe_passed']=state['failed']==0
        if not state['probe_passed']:state.update(status='STOPPED_PROBE_FAILED',stop_reason='All five probe responses must validate before batch capture');save(state);return 42
    state.update(status='COMPLETE' if state['processed']==state['total'] else 'CHECKPOINT',current_id='');save(state)
    return 0

if __name__=='__main__':sys.exit(main())
