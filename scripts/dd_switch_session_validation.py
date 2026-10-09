#!/usr/bin/env python3
"""Independent share/cash/dividend rebuild and official session/fill audits."""
import argparse,hashlib,io,json,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from dd_switch_session_market import SPLITS,HALTS,GAPS
from dd_switch_full_live_books import Book
from e22_books_apply import apply_books_for_date
from e22_dividend_accounting import load_dividend_events
from e22_mops_payment_amendments import load_amendments
from twse_session_sources import cached_load_calendar_window
from path3_comp_sat_daily_share_ssot import shares_panel_from_long
ROOT=Path(__file__).resolve().parents[1]

def audit_book(nav,fills,market,events,version):
 b=Book(500000000.);dates=nav.date.tolist();fill_by={d:x for d,x in fills.groupby('fill_date')};panel=market.set_index(['date','code']);rows=[];split_rows=[]
 for day in dates:
  px=panel.loc[day,'close'].to_dict()
  for code,factor in SPLITS.get(day,{}).items():
   if code not in px:continue
   before=b.positions.get(code,0);b.positions[code]=before*factor;split_rows.append(dict(date=day,code=code,factor=factor,shares_before=before,shares_after=b.positions[code],cash=b.cash))
  entitlement=dict(b.positions)
  for f in fill_by.get(day,pd.DataFrame()).itertuples():
   if not panel.loc[(day,f.code),'tradable']:raise ValueError('Ineligible fill '+day+' '+f.code)
   if pd.Timestamp(f.signal_date)>=pd.Timestamp(day):raise ValueError('Fill before signal qualification')
   if abs(f.gross-f.quantity*f.fill_price)>1e-5:raise ValueError('Fill gross mismatch')
   b.trade(day,f.code,f.side,f.quantity,f.fill_price,f.fees_tax)
  cal,settle=cached_load_calendar_window(int(day[:4]),soft_miss=True)
  b.positions,b.cash,b.receivables,result=apply_books_for_date(day,b.positions,b.cash,events,version=version,skip_keys=b.applied,mark_prices=px,receivables=b.receivables,session_dates=cal,settlement_dates=settle,entitlement_positions=entitlement,mops_amendments=load_amendments())
  b.applied.update(r['key'] for r in result.details)
  ref=nav.loc[nav.date.eq(day)].iloc[0]
  rows.append(dict(date=day,nav_residual=b.nav(px)-float(ref.nav),cash_residual=b.cash-float(ref.cash),receivable_residual=sum(b.receivables.values())-float(ref.receivables),cash=b.cash,minimum_shares=min(b.positions.values(),default=0)))
 residuals=pd.DataFrame(rows)
 if residuals[['nav_residual','cash_residual','receivable_residual']].abs().max().max()>1e-4:raise ValueError('Independent account reconciliation failed')
 return residuals,pd.DataFrame(split_rows),dict(max_nav_residual=float(residuals.nav_residual.abs().max()),max_cash_residual=float(residuals.cash_residual.abs().max()),min_cash=float(residuals.cash.min()),fills=len(fills),same_bar_fills=0,ineligible_fills=0)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);a=p.parse_args();build=a.build.resolve()
 if (ROOT/'repro').resolve() not in build.parents:raise ValueError('Research only')
 dest=build/'validation';dest.mkdir(exist_ok=True);records={};official=[]
 for year in [2025,2026]:
  cal,_=cached_load_calendar_window(year);official += [str(d) for d in cal if str(d).startswith(str(year)) and str(d)<='2026-10-08']
 for kind,books in [('parents',['OFFENSE','COMP_H150_x_A20','SAT_A20_RELAX']),('mothers',['BASE','L4'])]:
  market=pd.read_csv(build/'inputs'/(kind+'_with_off.csv'),dtype={'code':str});events=load_dividend_events(build/'inputs'/(kind+'_dividends.csv'),require_exists=True,fail_closed_amounts=True)
  for name in books:
   nav=pd.read_csv(build/kind/('nav_'+name+'.csv'));fills=pd.read_csv(build/kind/('fills_'+name+'.csv'),dtype={'code':str})
   missing=set(official)-set(nav.date)
   if missing:raise ValueError('Missing official sessions '+str(missing))
   res,splits,record=audit_book(nav,fills,market,events,'E22_v3_recv_pay_effdelay');res.to_csv(dest/(name+'_book_residuals.csv'),index=False);splits.to_csv(dest/(name+'_split_book.csv'),index=False)
   record.update(official_sessions_2025_2026=len(official),missing_sessions=[],gap_nav_rows=nav[nav.date.isin(GAPS)][['date','nav','cash']].to_dict('records'));records[name]=record;print('BOOK_VALIDATED',name,record['max_nav_residual'],flush=True)
 # Verify corrections did not perturb prior state before the first restored day.
 ref='f73c1ba1f48d77b4728ce510da97ae8a0885038e';prefix={}
 for book in ['COMP_H150_x_A20','SAT_A20_RELAX']:
  rel='repro/fin-sat-path3-daily-share-ssot-stagea/outputs/daily_shares_'+book+'.csv';old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show',ref+':'+rel],cwd=ROOT)),dtype={'code':str});new=pd.read_csv(build/'parents/outputs'/('daily_shares_'+book+'.csv'),dtype={'code':str})
  old=shares_panel_from_long(old);new=shares_panel_from_long(new);old=old.loc[:'2025-02-05'];new=new.loc[:'2025-02-05'];idx=old.index.union(new.index);cols=old.columns.union(new.columns);delta=new.reindex(index=idx,columns=cols,fill_value=0)-old.reindex(index=idx,columns=cols,fill_value=0);err=float(delta.abs().max().max());prefix[book]=dict(max_share_difference=err,pass_parity=err==0)
  if err:raise ValueError('Pre-gap parent changed')
 report=dict(status='OFFICIAL_SESSION_AND_INDEPENDENT_BOOK_AUDITS_PASS',official_sessions_2025_2026=len(official),books=records,pre_gap_parent_parity=prefix,halt_days={c:[str(d.date()) for d in days] for c,days in HALTS.items()},split_events=SPLITS,limits=['Official session validation covers 2025/2026; earlier dividend effective dates retain legacy fallback assumptions','Halt valuation is last exchange close; economic fund NAV during halt is not claimed','Mothers DD/TRAIL retain original shadow/return stitching, not a jointly-funded full live account'])
 (dest/'summary.json').write_text(json.dumps(report,indent=2));summary=json.loads((build/'summary.json').read_text());summary['official_sessions_2025_2026']=len(official);(build/'summary.json').write_text(json.dumps(summary,indent=2))
if __name__=='__main__':main()
