#!/usr/bin/env python3
"""Rebuild gap-complete parents/mothers with locked strategy and ETF contracts.

Research-only corrected lineage. Original reproductions and live history remain
immutable. Historical market/split fixes intentionally break old prefix parity.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import pandas as pd
import fin_sat_path3_daily_share_ssot_stagea as parent
import fin_sat_path3_path4_livestack_twin_stageb as ls
import tipsoft_ip3_fill_lock_stagea as fl
from e45_paper_harness import load_dividends
from e50_early_stack_combined_nav import simulate_core
from dd_switch_original_inputs import append_dividends
from dd_switch_session_market import repair_equity,attach_off,raw_response,SPLITS,GAPS,HALTS
from path3_comp_sat_daily_share_ssot import shares_panel_from_long
from live_path3_t0_switch_emitter import build_sat_lead_signal
from dd_switch_crisis_audit import features
from twse_session_sources import cached_load_calendar_window
ROOT=Path(__file__).resolve().parents[1]
REFS={'parents':'f73c1ba1f48d77b4728ce510da97ae8a0885038e','mothers':'5449f76b3a3feba434f40e0c5e10483e32c00b44'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--stage',choices=['inputs','parents','mothers','all'],default='all');a=p.parse_args();a.out=a.out.resolve()
 if (ROOT/'repro').resolve() not in a.out.parents:raise ValueError('Research directory only')
 a.out.mkdir(parents=True,exist_ok=True);sources={}
 def snapshot(ref,rel):
  path=a.out/'snapshots'/ref/rel
  if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(subprocess.check_output(['git','show',ref+':'+rel],cwd=ROOT))
  sources[ref+':'+rel]=hashlib.sha256(path.read_bytes()).hexdigest();return path
 inputs=a.out/'inputs';inputs.mkdir(exist_ok=True)
 live=pd.read_csv(ROOT/'forward/e21/live_market.csv',dtype={'code':str},parse_dates=['date'])
 for kind,ref in REFS.items():
  original=pd.read_csv(snapshot(ref,'forward/e21/live_market.csv'),dtype={'code':str},parse_dates=['date'])
  market=repair_equity(original,live,ROOT);market.to_csv(inputs/(kind+'_market.csv'),index=False)
  append_dividends(snapshot(ref,'data/dividend_events/e22_dividend_events.csv'),ROOT/'data/dividend_events/e22_dividend_events.csv',inputs/(kind+'_dividends.csv'),'2026-10-08')
 off=pd.read_csv(ROOT/'data/def_proxies/00631L_ohlcv.csv',dtype={'code':str},parse_dates=['date'])
 latest=ROOT/'repro/dd-switch-seven-session-rebuild/sources/00631L_latest.json'
 if not latest.exists():latest=ROOT/'repro/dd-switch-seven-session-complete-release/sources/00631L_latest.json'
 extra=raw_response(latest);extra['adj_close']=extra.close
 off=pd.concat([off,extra[~extra.date.isin(off.date)]],ignore_index=True).sort_values('date');off.to_csv(inputs/'00631L_actual.csv',index=False)
 official=[]
 for year in [2025,2026]:
  cal,_=cached_load_calendar_window(year);official += [pd.Timestamp(d) for d in cal if str(d).startswith(str(year)) and str(d)<='2026-10-08']
 for kind in REFS:
  market=pd.read_csv(inputs/(kind+'_market.csv'),dtype={'code':str},parse_dates=['date']);days=set(market.date)
  if set(official)-days:raise ValueError('Remaining equity session gaps')
  if not market.groupby('date').code.apply(lambda x:set(ls.FIN+ls.TEL+['0050','TAIEX']).issubset(set(x))).all():raise ValueError('Incomplete session universe')
  attached,_=attach_off(market,off);attached.to_csv(inputs/(kind+'_with_off.csv'),index=False)
  halted=attached[~attached.tradable];halted.to_csv(inputs/(kind+'_nontradable_marks.csv'),index=False)
 (inputs/'manifest.json').write_text(json.dumps(dict(source_refs=REFS,source_sha256=sources,official_sessions_2025_2026=len(official),missing_sessions=[],split_events=SPLITS,mark_policy='LAST_EXCHANGE_CLOSE_PRE_SPLIT_UNITS; NOT FUND NAV',execution_policy='NULL_OPEN_ON_HALT; NO_FILLS; NEWEST_SUSPENDED_INTENT; UNIT_CONVERSION_BEFORE_RESUME_OPEN'),indent=2))
 print('INPUTS_COMPLETE',len(official),flush=True)
 if a.stage=='inputs':return
 parents=a.out/'parents';parents.mkdir(exist_ok=True)
 if a.stage in ['parents','all']:
  market0=pd.read_csv(inputs/'parents_market.csv',dtype={'code':str},parse_dates=['date']);dividends=load_dividends(inputs/'parents_dividends.csv')
  parent.sat.load_market=lambda:market0.copy();parent.sat.load_dividends=lambda:dividends.copy();parent.sat.load_inv_bars=lambda:off.copy();parent.sat.attach_inv=attach_off;parent.OUT=parents/'outputs'
  names=iter(['OFFENSE','COMP_H150_x_A20','SAT_A20_RELAX']);records={}
  def captured(*args,**kwargs):
   name=next(names);sink=kwargs.get('daily_pos_sink',[]);kwargs['daily_pos_sink']=sink;kwargs['share_events']=SPLITS
   nav,fills,meta=simulate_core(*args,**kwargs);nav.to_csv(parents/('nav_'+name+'.csv'),index=False);fills.to_csv(parents/('fills_'+name+'.csv'),index=False);pd.DataFrame(sink).to_csv(parents/('shares_'+name+'.csv'),index=False);records[name]=meta;print('PARENT_COMPLETE',name,len(nav),flush=True);return nav,fills,meta
  parent.simulate_core=captured;parent.build_ledgers();(parents/'summary.json').write_text(json.dumps(records,indent=2,default=str))
  if a.stage=='parents':return
 comp=pd.read_csv(parents/'nav_COMP_H150_x_A20.csv',parse_dates=['date']);sat=pd.read_csv(parents/'nav_SAT_A20_RELAX.csv',parse_dates=['date']);signal=build_sat_lead_signal(comp=comp,sat=sat)
 mothers=a.out/'mothers';mothers.mkdir(exist_ok=True);signal.to_csv(mothers/'signal.csv',index=False)
 market=pd.read_csv(inputs/'mothers_market.csv',dtype={'code':str},parse_dates=['date']);dividends=load_dividends(inputs/'mothers_dividends.csv')
 _,sleeve,_,regime=ls.e16_features(market);cal=pd.DatetimeIndex(sorted(market.date.unique()))
 lows,highs=ls.build_low_high_catalog(market,cal,list(ls.FIN));kd=ls.build_kd_season_tilt_scores(market,dividends,list(ls.FIN),k_thresh=float(ls.LIVE_KD['k_thresh']),season_start=ls.LIVE_KD['season_start'],season_end=ls.LIVE_KD['season_end'],pre_days=int(ls.LIVE_KD['pre_days']),active_score=float(ls.LIVE_KD['active_score']))
 buy_ok=ls.build_pre_exdiv_window_buy_ok(cal,dividends,list(ls.FIN),pre_days=int(ls.LIVE_KD['pre_days']),also_stock_ex=True);scores=ls._buy(kd,lows);sell=ls._sell(highs);target=ls._target_live(ls._sleeve_score(market,sleeve,ls.LIVE_SLEEVE_ALPHA),regime);px=ls._close_panel(market,ls.SOFT_CORE)
 shares={book:shares_panel_from_long(pd.read_csv(parents/'outputs'/('daily_shares_'+book+'.csv'),dtype={'code':str})) for book in [ls.BOOK_COMP,ls.BOOK_SAT]}
 fin,tel=ls._path3_mix_score_panels(sig=signal,shares_by_book=shares,px=px,cal=cal)
 print('MOTHER_OFFENSE',flush=True)
 offnav,_,_=simulate_core(market,target,regime,dividends,apply_e22=True,apply_stock_div=True,capital=float(ls.DEFAULT_CAPITAL),lot_size=int(ls.BOARD_LOT),financial_alloc=ls.FIN_PRE_EXDIV_KD,telecom_alloc=ls.TEL_EQUAL,fin_name_scores=scores,fin_buy_ok=buy_ok,fin_sell_scores=sell,e22_version=ls.E22_VERSION,share_events=SPLITS)
 cool=ls._cool_from_offense(market,offnav);records={};curves={}
 def sim(*args,**kwargs):kwargs['share_events']=SPLITS;return simulate_core(*args,**kwargs)
 ls.simulate_core=sim
 for name,fs,ts,fa,ta,bo in [('BASE',scores,None,ls.FIN_PRE_EXDIV_KD,ls.TEL_EQUAL,buy_ok),('L4',fin,tel,ls.FIN_RS_SOFT_TILT,ls.TEL_RS_SOFT_TILT,None)]:
  sink=[]
  def captured(*args,**kwargs):kwargs['share_events']=SPLITS;kwargs['daily_pos_sink']=sink;return simulate_core(*args,**kwargs)
  ls.simulate_core=captured
  nav,fills,meta=ls._sim(market,target,regime,dividends,scores=fs,buy_ok=bo,sell=sell,exposure=cool,financial_alloc=fa,telecom_alloc=ta,tel_scores=ts)
  curves[name]=nav[['date','nav']].assign(date=lambda x:pd.to_datetime(x.date));nav.to_csv(mothers/('nav_'+name+'.csv'),index=False);fills.to_csv(mothers/('fills_'+name+'.csv'),index=False);pd.DataFrame(sink).to_csv(mothers/('shares_'+name+'.csv'),index=False);records[name]=meta;print('MOTHER_COMPLETE',name,len(nav),flush=True)
 rb=fl._returns(curves['BASE']);rl=fl._returns(curves['L4']);prem=pd.concat({'b':rb,'l':rl},axis=1).dropna();on=(fl._trail_sum(prem.l-prem.b,42).fillna(0)>=-.01).astype(float)
 weights={b:fl._book_soft_weights(s,px) for b,s in shares.items()}
 sc_on,_=fl.simulate_fill(fill='ALWAYS_WITHIN',weights_by_book=weights,px=px,signal=signal,i3_on=on,share_events=SPLITS);sc_cash,_=fl.simulate_fill(fill='FT_TO_CASH',weights_by_book=weights,px=px,signal=signal,i3_on=on,share_events=SPLITS)
 sc_on.to_csv(mothers/'nav_SC_WITHIN.csv',index=False);sc_cash.to_csv(mothers/'nav_SC_CASH.csv',index=False)
 pair=pd.concat({'l4':rl,'on':fl._returns(sc_on),'cash':fl._returns(sc_cash)},axis=1).dropna();trail=pd.DataFrame({'date':pair.index,'nav':(1+pair.l4+pair.cash-pair.on).cumprod().values});trail.to_csv(mothers/'nav_TRAIL.csv',index=False)
 pair=pd.concat({'l4':rl,'trail':fl._returns(trail)},axis=1).dropna();c=(1+pair).cumprod();dd=c/c.cummax()-1;want=dd.trail>=dd.l4;mother=pd.DataFrame({'date':pair.index,'nav':(1+pair.trail.where(want,pair.l4)).cumprod().values});mother.to_csv(mothers/'nav_DD_SWITCH.csv',index=False)
 controls=features({'base':curves['BASE'],'l4':curves['L4'],'trail':trail});controls.to_csv(mothers/'controls.csv')
 needed={d for d in official if d>=controls.index.min()}
 for frame in [comp,sat,signal,curves['BASE'],curves['L4'],trail,mother]:
  if needed-set(pd.to_datetime(frame.date)):raise ValueError('Incomplete reconstructed parent/mother')
 for folder in [parents,mothers]:
  for path in folder.glob('fills_*.csv'):
   fills=pd.read_csv(path,dtype={'code':str});
   for code,days in HALTS.items():
    if ((fills.code.eq(code))&pd.to_datetime(fills.fill_date).isin(days)).any():raise ValueError('Halt fill detected')
 runtime=a.out/'runtime';gen=runtime/'generations/corrected-complete';gen.mkdir(parents=True,exist_ok=True);files={}
 for key,src in {'off':inputs/'00631L_actual.csv','base':mothers/'nav_BASE.csv','l4':mothers/'nav_L4.csv','trail':mothers/'nav_TRAIL.csv','dd':mothers/'nav_DD_SWITCH.csv','signal':mothers/'signal.csv',**{'shares_'+b:parents/'outputs'/('daily_shares_'+b+'.csv') for b in shares}}.items():
  target=gen/(key+'.csv');target.write_bytes(src.read_bytes());files[key]=target.name
 meta=dict(version='DD_SWITCH_GAP_COMPLETE_SPLIT_ELIGIBILITY_RESEARCH_V1',asof='2026-10-08',generation='generations/corrected-complete',files=files,hashes={k:hashlib.sha256((gen/v).read_bytes()).hexdigest() for k,v in files.items()},prefix_certified=False,publication_allowed=False,construction_refs=REFS)
 (runtime/'current.json').write_text(json.dumps(meta,indent=2));(a.out/'summary.json').write_text(json.dumps(dict(status='GAP_COMPLETE_PARENTS_MOTHERS_REBUILT_RESEARCH_ONLY',restored_sessions=GAPS,official_sessions_2025_2026=len(official),missing_sessions=[],runtime=str(runtime),parent_records=json.loads((parents/'summary.json').read_text()),mother_records=records,limits=['Legacy strategy/signal/shadow stitching retained, not fully vintage PIT or complete live account execution','Last exchange close valuation during ETF halts is explicit stale mark, not daily fund NAV','Both 0050 and existing 00631L split contracts applied; regenerated state intentionally differs from archived original','No live overwrite, runtime publication, merge or deployment']),indent=2,default=str));print('REBUILD_COMPLETE',flush=True)
if __name__=='__main__':main()
