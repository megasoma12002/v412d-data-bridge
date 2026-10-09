#!/usr/bin/env python3
"""One-factor research ablation: keep Path3 active; preserve DD T+1 clocks.

This is NOT a refreshed original controller and must never route canonical books.
"""
import runpy
import sys
from pathlib import Path
import live_tipsoft_dd_switch as gate

ROOT=Path(__file__).resolve().parents[1]

def force_active_state(result):
    return {**result,'path3_active':True,'fill':'WITHIN'} if result.get('ok') else result

def main():
    args=sys.argv[1:]
    if '--state-dir' not in args or '--allow-noncanonical-paths' not in args:
        raise SystemExit('Research state-dir and noncanonical flag required')
    dest=Path(args[args.index('--state-dir')+1]).resolve()
    canonical=(ROOT/'forward/e21').resolve()
    if dest==canonical or canonical in dest.parents:
        raise SystemExit('Gap study refuses canonical books')
    original=gate.compute_gate_state
    def force_active(*a,**kw):
        return force_active_state(original(*a,**kw))
    gate.compute_gate_state=force_active
    sys.argv=[str(ROOT/'scripts/e21_forward_pipeline.py'),*args]
    runpy.run_path(sys.argv[0],run_name='__main__')

if __name__=='__main__':main()
