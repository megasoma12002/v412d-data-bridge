#!/usr/bin/env python3
"""Independent full-book/funding reconciliation of isolated pipeline replays."""
import argparse,hashlib,json,shutil
from pathlib import Path
import pandas as pd
from dd_switch_full_live_books import load_prices,reconstruct,metrics
from e22_dividend_accounting import load_dividend_events
from live_dd_funding import GROUPS
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--probe',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if (ROOT/'repro').resolve() not in a.out.resolve().parents:raise ValueError('Isolated output only')
 a.out.mkdir(exist_ok=True);panel,cal=load_prices();events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True);report={}
 for source,label in [(a.baseline,'baseline'),(a.probe,'synthetic_probe')]:
  nav,positions,audit,b,snap,ver,r=reconstruct(source,panel,cal,events);dest=a.out/label;dest.mkdir(exist_ok=True)
  nav.to_csv(dest/'complete_nav.csv',index=False);audit.to_csv(dest/'book_residuals.csv',index=False)
  rows=[]
  for day,pos in snap.items():
   px=panel.loc[day,'close'].to_dict();rows.append(dict(date=day,core_notional=sum(pos.get(c,0)*px[c] for codes in GROUPS.values() for c in codes),core_shares=sum(pos.get(c,0) for codes in GROUPS.values() for c in codes)))
  pd.DataFrame(rows).to_csv(dest/'core_exposure.csv',index=False)
  for file in ['summary.json','fills.csv','orders.csv','order_events.csv','nav.csv','signals.csv','portfolio_state.json','dd_funding_events.csv','qc_status.json','pipeline_t1_audit.json','audit_chain.jsonl']:
   if (source/file).exists():shutil.copyfile(source/file,dest/file)
  report[label]={**r,**metrics(nav,500000000.)}
  if label=='baseline':
   old=pd.read_csv(ROOT/'repro/dd-switch-original-live-t1/fills.csv',dtype={'code':str});new=pd.read_csv(source/'fills.csv',dtype={'code':str});pd.testing.assert_frame_equal(old,new,check_dtype=False);report[label]['fills_identical_to_previous']=True
  else:
   f=pd.read_csv(source/'fills.csv',dtype={'code':str});new=f[(f.fill_date>='2026-10-01')&f.code.isin(sum(GROUPS.values(),[]))]
   report[label].update(first_core_reentry_fill=str(new[new.side=='BUY'].fill_date.min()),exit_core_fills=int((new.fill_date.eq('2026-10-01')&new.side.eq('SELL')).sum()),first_reentry_core_buys=int((new.fill_date.eq('2026-10-05')&new.side.eq('BUY')).sum()),delayed_core_buys_next_day=int((new.fill_date.eq('2026-10-06')&new.side.eq('BUY')).sum()))
   state=json.loads((source/'portfolio_state.json').read_text());journal=pd.read_csv(source/'dd_funding_events.csv');balances=state['dd_switch_funding']['balances'];residual=max(abs(journal[journal.sleeve.eq(g)].amount.sum()-v) for g,v in balances.items());assert residual<1e-5
   report[label].update(funding_balance_by_sleeve=balances,funding_residual=residual)
 report['limits']=['Synthetic OFF/ON probe verifies lifecycle, not DD strategy performance','Paper Exact T+1 only; no broker or real liquidity certification','Ownership follows actual DD exit fills and paid core dividends; residual cash stays reserved','Legacy exits without funding provenance fail before fills; separate reconstruction required','No live history rewrite, runtime publication, merge or deployment']
 report['program_sha256']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['scripts/live_dd_funding.py','scripts/live_day_overlays.py','scripts/e21_forward_pipeline.py','scripts/live_day_commit.py','scripts/live_ledger.py']}
 (a.out/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
