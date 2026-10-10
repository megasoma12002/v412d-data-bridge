#!/usr/bin/env python3
"""Recover raw core quotes and reconstruct missing TRAIL controls in isolation.

Inputs are archived provider responses and certified snapshots. Never publishes
or changes the original mother: corrected controls intentionally differ after
2026-08-03. Seven absent parent/base sessions remain explicitly unresolved.
"""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import pandas as pd
from dd_switch_live_replay import verify_runtime_generation
from dd_switch_original_reproduction import normalize_signal
from path3_comp_sat_daily_share_ssot import shares_panel_from_long
import tipsoft_ip3_fill_lock_stagea as fl
from dd_switch_crisis_audit import features
ROOT=Path(__file__).resolve().parents[1]
DAYS=['2025-02-06','2025-06-11','2025-06-12','2025-06-13','2025-06-16','2025-06-17','2026-05-28']
TRAIL_DAYS=pd.date_range('2026-08-03','2026-08-07')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sources',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out=a.out.resolve()
 if (ROOT/'repro').resolve() not in a.out.parents:raise ValueError('Isolated research only')
 a.out.mkdir(parents=True,exist_ok=False);sources={}
 def read(path,**kw):
  if not path.exists() and 'source_snapshot' in path.parts:
   parts=path.parts;start=parts.index('source_snapshot');ref=parts[start+1];rel='/'.join(parts[start+2:])
   target=a.out/'inputs'/ref/rel;target.parent.mkdir(parents=True,exist_ok=True)
   target.write_bytes(subprocess.check_output(['git','show',ref+':'+rel],cwd=ROOT));path=target
  sources[str(path.resolve().relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();return pd.read_csv(path,**kw)
 rows=[]
 for code in list(fl.FIN)+['TAIEX']:
  path=a.sources/(code+'.json');sources[str(path.resolve().relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest();obj=json.loads(path.read_text())
  if obj.get('status')!=200:raise ValueError('Provider error: '+code)
  frame=pd.DataFrame(obj['data']);part=frame[frame.date.isin(DAYS)]
  if set(part.date)!=set(DAYS):raise ValueError('Provider missing quote: '+code)
  for _,r in part.iterrows():rows.append(dict(date=r.date,code=code,open=float(r.open),close=float(r.close),source='FinMind TaiwanStockPrice archived JSON'))
 for code in fl.TEL:
  path=ROOT/f'data/telecom_0050_complete/{code}_2010_latest_ohlcv.csv';frame=read(path)
  for _,r in frame[frame.date.isin(DAYS)].iterrows():rows.append(dict(date=r.date,code=code,open=float(r.open),close=float(r.close),source=str(path.relative_to(ROOT))))
 raw=pd.DataFrame(rows).sort_values(['date','code']);expected={(d,c) for d in DAYS for c in list(fl.FIN)+list(fl.TEL)+['TAIEX']}
 if set(zip(raw.date,raw.code))!=expected or raw.duplicated(['date','code']).any():raise ValueError('Incomplete recovered raw core panel')
 if (raw[['open','close']]<=0).any().any():raise ValueError('Invalid raw quote')
 raw.to_csv(a.out/'recovered_core_prices.csv',index=False)
 runtime=ROOT/'repro/dd-switch-live-repair-runtime-certified';meta=json.loads((runtime/'current.json').read_text());g=verify_runtime_generation(runtime,meta)
 frames={k:read(g/meta['files'][k],parse_dates=['date']) for k in ['base','l4','trail']}
 snap=ROOT/'repro/dd-switch-live-repair-refresh-final/lineage/source_snapshot/97933be85192e8d0ef89695be0c292342bba694d'
 market=read(snap/'forward/e21/live_market.csv',dtype={'code':str},parse_dates=['date'])
 live=read(ROOT/'forward/e21/live_market.csv',dtype={'code':str},parse_dates=['date'])
 restored=live[live.date.isin(TRAIL_DAYS)]
 if len(restored)!=len(TRAIL_DAYS)*9:raise ValueError('Missing actual TRAIL reconstruction prices')
 market=pd.concat([market[market.date<='2026-09-29'],restored,live[live.date>'2026-09-29']],ignore_index=True).sort_values(['date','code'])
 if market.duplicated(['date','code']).any():raise ValueError('Duplicate control prices')
 market.to_csv(a.out/'trail_reconstruction_market.csv',index=False)
 px=market.pivot(index='date',columns='code',values='close')[fl.SOFT_CORE]
 ledgers={}
 for book in [fl.BOOK_COMP,fl.BOOK_SAT]:
  orig=read(snap/f'repro/fin-sat-path3-daily-share-ssot-stagea/outputs/daily_shares_{book}.csv',dtype={'code':str},parse_dates=['date'])
  tip=read(g/meta['files']['shares_'+book],dtype={'code':str},parse_dates=['date'])
  ledgers[book]=shares_panel_from_long(pd.concat([orig,tip[tip.date>'2026-09-29']]))
 signal=normalize_signal(read(g/meta['files']['signal'],parse_dates=['date']))
 rbase=frames['base'].set_index('date').nav.pct_change().fillna(0.);rl4=frames['l4'].set_index('date').nav.pct_change().fillna(0.)
 prem=pd.concat({'base':rbase,'l4':rl4},axis=1).dropna();gate=(fl._trail_sum(prem.l4-prem.base,42).fillna(0)>=-.01).astype(float)
 weights={b:fl._book_soft_weights(s,px) for b,s in ledgers.items()}
 on,_=fl.simulate_fill(fill='ALWAYS_WITHIN',weights_by_book=weights,px=px,signal=signal,i3_on=gate)
 cash,_=fl.simulate_fill(fill='FT_TO_CASH',weights_by_book=weights,px=px,signal=signal,i3_on=gate)
 on.to_csv(a.out/'nav_SC_WITHIN_corrected.csv',index=False);cash.to_csv(a.out/'nav_SC_CASH_corrected.csv',index=False)
 pair=pd.concat({'l4':rl4,'on':on.set_index('date').nav.pct_change().fillna(0.),'cash':cash.set_index('date').nav.pct_change().fillna(0.)},axis=1).dropna()
 trail=pd.DataFrame({'date':pair.index,'nav':(1+pair.l4+pair.cash-pair.on).cumprod().values})
 old=frames['trail'].set_index('date').nav;new=trail.set_index('date').nav
 before=old.index[old.index<'2026-08-03'];err=float((new.loc[before]/old.loc[before]-1).abs().max())
 if err>1e-10:raise ValueError('TRAIL reconstruction changed pre-gap reference: '+str(err))
 corrected={**frames,'trail':trail};old_features=features(frames);new_features=features(corrected);idx=old_features.index.intersection(new_features.index)
 comparison=old_features.loc[idx].add_prefix('old_').join(new_features.loc[idx].add_prefix('new_'));comparison.to_csv(a.out/'control_difference.csv')
 dest=a.out/'runtime';gen=dest/'generations/repaired-research';gen.mkdir(parents=True)
 for name in meta['files'].values():shutil.copyfile(g/name,gen/name)
 trail.to_csv(gen/meta['files']['trail'],index=False)
 paired=pd.concat({'l4':rl4,'trail':new.pct_change().fillna(0.)},axis=1).dropna();curve=(1+paired).cumprod();dd=curve/curve.cummax()-1;want=dd.trail>=dd.l4
 pd.DataFrame({'date':paired.index,'nav':(1+paired.trail.where(want,paired.l4)).cumprod().values}).to_csv(gen/meta['files']['dd'],index=False)
 revised={**meta,'version':'DD_SWITCH_HISTORICAL_GAP_REPAIR_RESEARCH_V1','generation':'generations/repaired-research','prefix_certified':False,'original_research_preserved':False,'publication_allowed':False,'hashes':{k:hashlib.sha256((gen/n).read_bytes()).hexdigest() for k,n in meta['files'].items()}}
 (dest/'current.json').write_text(json.dumps(revised,indent=2))
 result=dict(status='RAW_CORE_RECOVERED_AND_FIVE_TRAIL_SESSIONS_RECONSTRUCTED_NOT_COMPLETE',recovered_raw_rows=len(raw),recovered_price_sessions=DAYS,restored_trail_sessions=[str(d.date()) for d in TRAIL_DAYS],pre_gap_trail_max_relative_error=err,active_gate_changes_on_shared_dates=int((comparison.old_active!=comparison.new_active).sum()),unresolved_parent_and_base_sessions=DAYS,source_sha256=sources,canonical_history_unchanged=True,limits=['0050 halt dates have no tradable quote: no invented ETF fills','Seven sessions still lack original BASE/L4 and parent shares/signals: strict complete-session DD replay remains blocked','Corrected historical runtime is research only; original prefix certification is intentionally removed'])
 (a.out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
