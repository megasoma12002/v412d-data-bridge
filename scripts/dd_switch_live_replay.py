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

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed', default='2026-09-29')
    p.add_argument('--out', type=Path, default=ROOT/'repro/dd-switch-live-t1-r1')
    a = p.parse_args()
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
    runtime=ROOT/'data/dd_switch_runtime'
    meta=json.loads((runtime/'current.json').read_text())
    market=pd.read_csv(source/'live_market.csv',parse_dates=['date'],dtype={'code':str})
    dates=sorted(market.loc[market.date>seed,'date'].unique())
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
        result=subprocess.run([sys.executable,str(ROOT/'scripts/e21_forward_pipeline.py'),'--market',str(source/'live_market.csv'),'--state-dir',str(out),'--asof',day.strftime('%F'),'--allow-noncanonical-paths','--skip-excel-dashboard'],env=env,text=True,capture_output=True)
        (out/(day.strftime('%F')+'.log')).write_text(result.stdout+result.stderr)
        if result.returncode:
            print(result.stdout+result.stderr)
            raise SystemExit(result.returncode)
        print(day.strftime('%F'), result.stdout[-450:],flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/e21_qc.py'),'--state-dir',str(out),'--allow-noncanonical-paths'],env=env,check=True)
    rebuilt=pd.read_csv(out/'nav.csv')
    vals=rebuilt.nav_e16_e18
    latest=float(vals.iloc[-1]); initial=float(vals.iloc[0])
    result=dict(seed=a.seed,end=str(rebuilt.date.iloc[-1]),initial=initial,final=latest,profit=latest-initial,return_pct=(latest/initial-1)*100,mdd_pct=float((vals/vals.cummax()-1).min()*100),original_tip=float(nav.nav_e16_e18.iloc[-1]),tip_difference=latest-float(nav.nav_e16_e18.iloc[-1]),scope='production pipeline counterfactual after seed; earlier live records preserved')
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
