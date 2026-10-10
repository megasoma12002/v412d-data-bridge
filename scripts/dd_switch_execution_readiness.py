#!/usr/bin/env python3
"""Inventory actual evidence; date-level eligibility is not fill-clock proof."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def audit_book(path, calendar):
    fills=pd.read_csv(path/'fills.csv',dtype={'code':str})
    nav=pd.read_csv(path/'nav.csv')
    signal=pd.to_datetime(fills.signal_date,errors='coerce')
    filled=pd.to_datetime(fills.fill_date,errors='coerce')
    missing_clock=[c for c in ('signal_at','fill_at','quote_at') if c not in fills]
    return dict(book=str(path.relative_to(ROOT)),fills=len(fills),
                date_before_signal=int((filled<signal).sum()),
                same_date=int((filled==signal).sum()),
                later_date=int((filled>signal).sum()),
                invalid_dates=int((filled.isna()|signal.isna()).sum()),
                missing_clock_columns=missing_clock,
                fill_clock_verdict='DATE_ONLY_UNVERIFIED' if missing_clock else 'NEEDS_TIMESTAMP_AUDIT',
                missing_nav_sessions=sorted(set(calendar[(calendar>=nav.date.min())&(calendar<=nav.date.max())])-set(nav.date)),
                fee_total=float(fills.fees_tax.sum()))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-execution-readiness')
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    calendar=pd.read_csv(ROOT/'forward/e21/live_market.csv',usecols=['date']).date.drop_duplicates()
    books=[ROOT/'forward/e21',ROOT/'repro/dd-switch-live-t1-r1']
    evidence=[]
    for base in ('data','forward','repro'):
        for file in (ROOT/base).rglob('*.csv'):
            cols=set(pd.read_csv(file,nrows=0).columns)
            if {'timestamp','available_at','bid','ask','bid_size','ask_size'}<=cols:
                evidence.append(str(file.relative_to(ROOT)))
    result=dict(status='BLOCKED_INTRADAY_EVIDENCE' if not evidence else 'CANDIDATES_REQUIRE_VALIDATION',
                quote_depth_candidates=evidence,books=[audit_book(b,calendar) for b in books],
                required_inputs=['timestamped parent NAV snapshots, full-account contemporaneous target allocations',
                                 'timestamped bid/ask depth with availability timestamps and immutable hashes',
                                 'complete session/EOD parent NAV history for historical peaks',
                                 'explicit corporate action inventory; dividend windows currently unsupported'],
                research_runner='scripts/dd_switch_intraday_replay.py',
                execution_scope='Paper quote model; no broker acknowledgements or live routing',
                source_sha256={str((b/'fills.csv').relative_to(ROOT)):hashlib.sha256((b/'fills.csv').read_bytes()).hexdigest() for b in books})
    (a.out/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
