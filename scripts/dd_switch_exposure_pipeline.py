#!/usr/bin/env python3
"""Prespecified initial handoff staging, isolated actual-position feedback only.

DD exits and book flips retain full priority. Remaining differences are always
recomputed from latest close target and actual post-open holdings, never queued
as stale share deltas. No executable T0 branch is introduced.
"""
import json,math,os,runpy,sys
from pathlib import Path
import live_path3_t0_weight_engine as engine
ROOT=Path(__file__).resolve().parents[1]
POLICIES={'immediate':1,'two_day':2,'three_day':3}
def stage_delta(delta,remaining,flip=False):
    if flip or remaining<=1:return dict(delta)
    return {c:math.copysign(int(abs(q)//(remaining*1000))*1000,q) for c,q in delta.items() if abs(q)>=remaining*1000}
def main():
    args=sys.argv[1:];policy=os.environ.get('DD_EXPOSURE_RESEARCH_POLICY')
    if policy not in POLICIES or '--state-dir' not in args or '--allow-noncanonical-paths' not in args:
        raise SystemExit('Explicit isolated state and prespecified exposure policy required')
    dest=Path(args[args.index('--state-dir')+1]).resolve()
    if (ROOT/'repro').resolve() not in dest.parents:raise SystemExit('Research state only')
    path=dest/'exposure_stage.json';state=json.loads(path.read_text()) if path.exists() else {'observations':0}
    original=engine.plan_or_none_for_pipeline
    def patched(**kw):
        delta,meta=original(**kw)
        if delta is None:return delta,meta
        if meta.get('weight_engine_mode')!='ledger':raise RuntimeError('Original ledger planner required')
        day=str(kw['asof'])[:10];flip=bool(meta.get('switch',{}).get('flip'))
        remaining=max(1,POLICIES[policy]-state['observations'])
        kept=stage_delta(delta,remaining,flip)
        # Risk gate is applied downstream to the staged plan, preserving exits.
        state.update(observations=state['observations']+1,last_date=day)
        path.write_text(json.dumps(state))
        with (dest/'exposure_audit.jsonl').open('a') as f:
            f.write(json.dumps(dict(date=day,policy=policy,remaining=remaining,flip=flip,
                original_delta=delta,emitted_delta=kept,positions_after_open=kw['pos']))+'\n')
        return kept,{**meta,'delta_shares':kept,'exposure_research_policy':policy}
    engine.plan_or_none_for_pipeline=patched
    sys.argv=[str(ROOT/'scripts/e21_forward_pipeline.py'),*args]
    runpy.run_path(sys.argv[0],run_name='__main__')
if __name__=='__main__':main()
