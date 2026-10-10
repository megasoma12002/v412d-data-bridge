#!/usr/bin/env python3
"""Persist bounded serial issuer-page probes; never equate transport success to evidence."""
import argparse,gzip,hashlib,json,subprocess,time,fcntl
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from dd_switch_monitored_capture import blocked
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'repro/dd-switch-full-history-audit';DEST=OUT/'sources/targeted_issuers'
def now():return datetime.now(timezone.utc).isoformat()
def source_blocked(raw, url, http_status=None):
    # Bundled JavaScript contains library error strings (e.g. DecoderBuffer overrun).
    # Only recognize a bundle by its observed webpack wrapper; HTML/plain blocks still stop.
    head=raw.lstrip()[:400]
    if http_status == b'403' and head.startswith(b'<') and b'403 forbidden' in head.lower():
        return True
    if urlsplit(url).path.endswith('.js') and b'webpackJsonp' in head and not head.startswith(b'<'):
        return False
    return blocked(raw)

@contextmanager
def exclusive_capture_lock(directory=DEST):
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'capture.lock').open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def main():
    p=argparse.ArgumentParser();p.add_argument('queue',type=Path);p.add_argument('--progress',default='issuer_capture_progress.json');p.add_argument('--timeout-seconds',type=int,choices=[15,30],default=15);args=p.parse_args()
    items=json.loads(args.queue.read_text());DEST.mkdir(parents=True,exist_ok=True)
    mp=DEST/'manifest.json';rows=json.loads(mp.read_text()) if mp.exists() else []
    state=dict(status='RUNNING',total=len(items),processed=0,success=0,failed=0,cached=0,started_at=now(),blocked_hosts=[],recent_results=[])
    def save():
        state['updated_at']=now();f=OUT/args.progress;tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(f);mp.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(state),flush=True)
    failures=0
    for item in items:
        host=urlsplit(item['url']).netloc
        if host in state['blocked_hosts']:continue
        old=next((r for r in rows if r['id']==item['id']),None)
        if old and old['status']=='RESPONSE_SAVED_NEEDS_VALIDATION':
            state['processed']+=1;state['cached']+=1;save();continue
        state.update(current_id=item['id'],current_started_at=now());save();time.sleep(2)
        r=subprocess.run(['curl','-L','--compressed','--max-time',str(args.timeout_seconds),'-sS','-w','\n%{http_code}',item['url']],capture_output=True)
        raw,_,status=r.stdout.rpartition(b'\n');f=DEST/(item['id']+'.html.gz');f.write_bytes(gzip.compress(raw,mtime=0))
        block=source_blocked(raw,item['url'],status);good=r.returncode==0 and status==b'200' and not block
        meta=dict(item,timeout_seconds=args.timeout_seconds,status='SOURCE_BLOCKED' if block else 'RESPONSE_SAVED_NEEDS_VALIDATION' if good else 'FAILED',path=str(f.relative_to(ROOT)),retrieved_at=now(),http_status=status.decode(),error=r.stderr.decode(errors='replace'),response_sha256=hashlib.sha256(raw).hexdigest(),compressed_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        rows=[v for v in rows if v['id']!=item['id']]+[meta];state['processed']+=1;state['success']+=int(good);state['failed']+=int(not good);state['last_completed_at']=now();state['recent_results']=(state['recent_results']+[dict(id=meta['id'],status=meta['status'])])[-10:]
        if block:state['blocked_hosts'].append(host)
        failures=0 if good else failures+1;save()
        if failures>=3:state.update(status='STOPPED_FAILURE_LIMIT',current_id='',skipped=len(items)-state['processed'],stop_reason='Three consecutive failures');save();return
    state.update(status='STOPPED_SOURCE_BLOCK' if state['blocked_hosts'] else 'COMPLETE',current_id='',skipped=len(items)-state['processed']);save()
if __name__=='__main__':
    with exclusive_capture_lock():main()
