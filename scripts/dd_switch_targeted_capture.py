#!/usr/bin/env python3
"""Persist bounded serial issuer-page probes; never equate transport success to evidence."""
import argparse,gzip,hashlib,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from dd_switch_monitored_capture import blocked
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'repro/dd-switch-full-history-audit';DEST=OUT/'sources/targeted_issuers'
def now():return datetime.now(timezone.utc).isoformat()
def main():
    p=argparse.ArgumentParser();p.add_argument('queue',type=Path);args=p.parse_args()
    items=json.loads(args.queue.read_text());DEST.mkdir(parents=True,exist_ok=True)
    mp=DEST/'manifest.json';rows=json.loads(mp.read_text()) if mp.exists() else []
    state=dict(status='RUNNING',total=len(items),processed=0,success=0,failed=0,cached=0,started_at=now(),blocked_hosts=[],recent_results=[])
    def save():
        state['updated_at']=now();f=OUT/'issuer_capture_progress.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');tmp.replace(f);mp.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(state),flush=True)
    failures=0
    for item in items:
        host=urlsplit(item['url']).netloc
        if host in state['blocked_hosts']:continue
        old=next((r for r in rows if r['id']==item['id']),None)
        if old and old['status']=='RESPONSE_SAVED_NEEDS_VALIDATION':
            state['processed']+=1;state['cached']+=1;save();continue
        state.update(current_id=item['id'],current_started_at=now());save();time.sleep(2)
        r=subprocess.run(['curl','-L','--max-time','15','-sS','-w','\n%{http_code}',item['url']],capture_output=True)
        raw,_,status=r.stdout.rpartition(b'\n');f=DEST/(item['id']+'.html.gz');f.write_bytes(gzip.compress(raw,mtime=0))
        block=blocked(raw);good=r.returncode==0 and status==b'200' and not block
        meta=dict(item,status='SOURCE_BLOCKED' if block else 'RESPONSE_SAVED_NEEDS_VALIDATION' if good else 'FAILED',path=str(f.relative_to(ROOT)),retrieved_at=now(),http_status=status.decode(),error=r.stderr.decode(errors='replace'),response_sha256=hashlib.sha256(raw).hexdigest(),compressed_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        rows=[v for v in rows if v['id']!=item['id']]+[meta];state['processed']+=1;state['success']+=int(good);state['failed']+=int(not good);state['last_completed_at']=now();state['recent_results']=(state['recent_results']+[dict(id=meta['id'],status=meta['status'])])[-10:]
        if block:state['blocked_hosts'].append(host)
        failures=0 if good else failures+1;save()
        if failures>=3:state.update(status='STOPPED_FAILURE_LIMIT',stop_reason='Three consecutive failures');save();return
    state.update(status='COMPLETE',current_id='');save()
if __name__=='__main__':main()
