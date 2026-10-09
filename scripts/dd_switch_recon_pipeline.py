#!/usr/bin/env python3
"""Isolated production-feedback Path3 rounding / deadband sensitivities.

Only ordinary same-book nonzero-to-nonzero recon is buffered. Flips, full
liquidations, new names and DD risk exits are never buffered. Skipped deltas
are recomputed against actual holdings next session, not discarded intents.
"""
import json, os, runpy, sys
from pathlib import Path
import live_path3_t0_weight_engine as engine
import path3_comp_sat_daily_share_ssot as ledger

ROOT=Path(__file__).resolve().parents[1]
POLICIES=('audit','epsilon','one_lot','sleeve_5bp','sleeve_20bp')

def stable_board_lots(shares):
    """Correct only float noise within 1e-7 shares of an integer lot."""
    value=max(0.,float(shares)); nearest=round(value/1000)*1000
    if abs(value-nearest)<=1e-7:value=float(nearest)
    return 1000*int(value//1000)

def should_buffer(policy,delta,current,target,price,sleeve,flip):
    if flip or current<=0 or target<=0:return False
    if policy=='one_lot':return abs(delta)<=1000
    bp={'sleeve_5bp':5,'sleeve_20bp':20}.get(policy,0)
    return bool(bp and abs(delta)*price<=sleeve*bp/10000)

def main():
    args=sys.argv[1:];policy=os.environ.get('DD_RECON_RESEARCH_POLICY')
    if policy not in POLICIES or '--state-dir' not in args or '--allow-noncanonical-paths' not in args:
        raise SystemExit('Explicit isolated research state and policy required')
    dest=Path(args[args.index('--state-dir')+1]).resolve()
    if (ROOT/'repro').resolve() not in dest.parents:
        raise SystemExit('Reconciliation sensitivity restricted to repo/repro')
    if policy=='epsilon':ledger.board_lots=stable_board_lots
    original=engine.plan_or_none_for_pipeline
    def patched(**kw):
        delta,meta=original(**kw)
        if delta is None:return delta,meta
        if meta.get('weight_engine_mode')!='ledger':raise RuntimeError('Study requires ledger planner')
        pos=kw['pos'];px=kw['prices'];sw=meta.get('switch',{});flip=bool(sw.get('flip'))
        led=ledger.shares_asof(sw['book'],kw['asof']);kept=dict(delta);rows=[]
        for code,d in delta.items():
            names=ledger.FIN if code in ledger.FIN else ledger.TEL
            sleeve=ledger.sleeve_notional(names,pos,px)
            mix=ledger.dollar_mix(led,px,names)
            raw=sleeve*mix.get(code,0)/px[code] if code in mix else None
            current=float(pos.get(code,0));target=current+d
            blocked=should_buffer(policy,d,current,target,px[code],sleeve,flip)
            if blocked:kept.pop(code)
            rows.append(dict(date=str(kw['asof'])[:10],policy=policy,code=code,book=sw['book'],
                flip=flip,current=current,raw_target=raw,rounded_target=target,delta=d,
                fractional_gap_to_current=None if raw is None else raw-current,
                numerical_one_lot_sell=bool(d==-1000 and raw is not None and abs(raw-current)<=1e-7),
                sleeve_notional=sleeve,trade_notional=abs(d)*px[code],buffered=blocked))
        with (dest/'recon_audit.jsonl').open('a') as f:
            for row in rows:f.write(json.dumps(row)+'\n')
        return kept,{**meta,'recon_research_policy':policy,'research_n_buffered':len(delta)-len(kept)}
    engine.plan_or_none_for_pipeline=patched
    sys.argv=[str(ROOT/'scripts/e21_forward_pipeline.py'),*args]
    runpy.run_path(sys.argv[0],run_name='__main__')

if __name__=='__main__':main()
