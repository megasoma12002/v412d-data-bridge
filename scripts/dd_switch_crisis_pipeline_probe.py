#!/usr/bin/env python3
"""Research-only synthetic OFF/ON probe through actual production pipeline.

Original gates remain the strategy reference; this fault injection verifies
state/cash transitions and cannot be presented as DD strategy performance.
"""
import os,runpy,sys
from pathlib import Path
import pandas as pd
import live_tipsoft_dd_switch as gate
ROOT=Path(__file__).resolve().parents[1]
def main():
    args=sys.argv[1:]
    if os.environ.get('DD_CRISIS_LIFECYCLE_PROBE')!='OFF_0930_1001_ON_FROM_1002' or '--state-dir' not in args or '--allow-noncanonical-paths' not in args:
        raise SystemExit('Explicit isolated fault-injection state required')
    dest=Path(args[args.index('--state-dir')+1]).resolve()
    if (ROOT/'repro').resolve() not in dest.parents:raise SystemExit('Research state only')
    original=gate.compute_gate_state
    def injected(asof=None,**kw):
        result=original(asof,**kw)
        if not result.get('ok'):return result
        day=str(pd.Timestamp(asof).date());active=day>='2026-10-02'
        return {**result,'path3_active':active,'want_trail':not active,'trail42_on':active,
                'fill':'WITHIN' if active else 'FT_TO_CASH','research_fault_injection':True}
    gate.compute_gate_state=injected
    sys.argv=[str(ROOT/'scripts/e21_forward_pipeline.py'),*args]
    runpy.run_path(sys.argv[0],run_name='__main__')
if __name__=='__main__':main()
