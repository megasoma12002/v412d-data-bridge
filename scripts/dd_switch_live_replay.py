#!/usr/bin/env python3
"""Replay the production pipeline from a verified pre-stale live snapshot.

Separate state directory and day-cut runtime files prevent future controller
observations from entering any historical decision. Canonical books untouched.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def verify_runtime_generation(runtime,meta):
    runtime=Path(runtime).resolve()
    generation=(runtime/meta['generation']).resolve()
    if runtime not in generation.parents:raise RuntimeError('Runtime generation outside source directory')
    for key,name in meta['files'].items():
        source=(generation/name).resolve()
        if generation not in source.parents:raise RuntimeError('Runtime file outside generation')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=meta['hashes'][key]:
            raise RuntimeError('Source runtime checksum mismatch: '+key)
    return generation

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed', default='2026-09-29')
    p.add_argument('--out', type=Path, default=ROOT/'repro/dd-switch-live-t1-r1')
    p.add_argument('--inputs-dir',type=Path,default=ROOT/'data/dd_switch_runtime',help='Versioned research runtime to day-cut')
    p.add_argument('--end',help='Last replay signal date; defaults to input generation asof')
    p.add_argument('--force-active-for-gap-study',action='store_true',help='Hypothetical exit ablation only; not original strategy')
    p.add_argument('--recon-research-policy',choices=['audit','epsilon','one_lot','sleeve_5bp','sleeve_20bp'],help='Isolated Path3 reconciliation sensitivity; never a live setting')
    p.add_argument('--exposure-research-policy',choices=['immediate','two_day','three_day'],help='Isolated initial handoff staging; no live promotion')
    a = p.parse_args()
    if a.force_active_for_gap_study and a.recon_research_policy:
        p.error('Reconciliation study must preserve the real DD gate')
    if a.exposure_research_policy and (a.force_active_for_gap_study or a.recon_research_policy):
        p.error('Exposure study cannot combine other policy overrides')
    out = a.out.resolve()
    source = ROOT/'forward/e21'
    if out == source or source in out.parents:
        raise SystemExit('Replay must not overwrite live history')
    out.mkdir(parents=True, exist_ok=False)
    seed = pd.Timestamp(a.seed)
    state = json.loads((source/'portfolio_state.json').read_text())
    nav = pd.read_csv(source/'nav.csv')
    row = nav.loc[pd.to_datetime(nav.date).eq(seed)].iloc[0]
    fills = pd.read_csv(source/'fills.csv',dtype={'code':str})
    past = fills[pd.to_datetime(fills.fill_date)<=seed]
    pos = (past.quantity * past.side.map({'BUY':1,'SELL':-1})).groupby(past.code).sum().to_dict()
    # Live bootstrap contains no dividends; refuse if a stock event could be lost.
    if nav.loc[pd.to_datetime(nav.date)<=seed,'e22_stock_shares_added'].fillna(0).abs().sum() or row.e22_receivable_balance:
        raise RuntimeError('Need keyed dividend snapshot for this seed')
    state.update(positions=pos,cash=float(row.cash),last_date=a.seed,last_nav=float(row.nav_e16_e18),e22_receivables={},e22_applied_keys=[])
    (out/'portfolio_state.json').write_text(json.dumps(state,indent=2))
    for name,datecol in [('fills','fill_date'),('orders','signal_date'),('signals','date'),('nav','date')]:
        df=pd.read_csv(source/(name+'.csv'),dtype={'code':str})
        df[pd.to_datetime(df[datecol])<=seed].to_csv(out/(name+'.csv'),index=False)
    runtime=a.inputs_dir.resolve()
    meta=json.loads((runtime/'current.json').read_text())
    verify_runtime_generation(runtime,meta)
    market=pd.read_csv(source/'live_market.csv',parse_dates=['date'],dtype={'code':str})
    end=pd.Timestamp(a.end or meta['asof'])
    if end>pd.Timestamp(meta['asof']):raise RuntimeError('Replay end exceeds controller input tip')
    dates=sorted(market.loc[(market.date>seed)&(market.date<=end),'date'].unique())
    if not dates:raise RuntimeError('No sessions after replay seed')
    for day in dates:
        day=pd.Timestamp(day)
        dest=out/'runtime'
        generation=dest/'generations/day'
        generation.mkdir(parents=True,exist_ok=True)
        current={**meta,'asof':day.strftime('%F'),'generation':'generations/day','hashes':{}}
        for key,name in meta['files'].items():
            df=pd.read_csv(runtime/meta['generation']/name,dtype={'code':str},parse_dates=['date'])
            target=generation/name
            df[df.date<=day].to_csv(target,index=False)
            current['hashes'][key]=hashlib.sha256(target.read_bytes()).hexdigest()
        (dest/'current.json').write_text(json.dumps(current))
        env={**os.environ,'E21_DD_INPUTS_DIR':str(dest)}
        entry='dd_switch_gap_pipeline.py' if a.force_active_for_gap_study else 'e21_forward_pipeline.py'
        if a.recon_research_policy:
            env['DD_RECON_RESEARCH_POLICY']=a.recon_research_policy
            entry='dd_switch_recon_pipeline.py'
        if a.exposure_research_policy:
            env['DD_EXPOSURE_RESEARCH_POLICY']=a.exposure_research_policy
            entry='dd_switch_exposure_pipeline.py'
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/entry),'--market',str(source/'live_market.csv'),'--state-dir',str(out),'--asof',day.strftime('%F'),'--allow-noncanonical-paths','--skip-excel-dashboard'],env=env,text=True,capture_output=True)
        (out/(day.strftime('%F')+'.log')).write_text(result.stdout+result.stderr)
        if result.returncode:
            print(result.stdout+result.stderr)
            raise SystemExit(result.returncode)
        print(day.strftime('%F'), result.stdout[-450:],flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/e21_qc.py'),'--state-dir',str(out),'--allow-noncanonical-paths'],env=env,check=True)
    rebuilt=pd.read_csv(out/'nav.csv')
    vals=rebuilt.nav_e16_e18
    latest=float(vals.iloc[-1]); initial=float(vals.iloc[0])
    result=dict(seed=a.seed,end=str(rebuilt.date.iloc[-1]),initial=initial,final=latest,profit=latest-initial,return_pct=(latest/initial-1)*100,recorded_dates_mdd_pct=float((vals/vals.cummax()-1).min()*100),original_tip=float(nav.nav_e16_e18.iloc[-1]),tip_difference=latest-float(nav.nav_e16_e18.iloc[-1]),scope='production pipeline counterfactual after seed; earlier live records preserved')
    result['gate_mode']='FORCED_ACTIVE_EXIT_ABLATION' if a.force_active_for_gap_study else meta['version']
    result['runtime_source']=str(runtime)
    result['recon_research_policy']=a.recon_research_policy
    result['exposure_research_policy']=a.exposure_research_policy
    result['runtime_manifest_sha256']=hashlib.sha256((runtime/'current.json').read_bytes()).hexdigest()
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
