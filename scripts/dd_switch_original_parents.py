#!/usr/bin/env python3
"""Rebuild original COMP/SAT ledgers in isolation using their generating commit inputs."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import pandas as pd
import fin_sat_path3_daily_share_ssot_stagea as parent
from e45_paper_harness import load_market,load_dividends
from path3_comp_sat_daily_share_ssot import shares_panel_from_long
from dd_switch_original_inputs import append_market,append_dividends
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--asof',default='2026-09-29')
    p.add_argument('--append-tip',action='store_true')
    p.add_argument('--market-tip',type=Path,default=ROOT/'forward/e21/live_market.csv')
    p.add_argument('--off-tip',type=Path,default=ROOT/'repro/dd-switch-t1-r1/00631L_ohlcv.csv')
    p.add_argument('--dividend-tip',type=Path,default=ROOT/'data/dividend_events/e22_dividend_events.csv')
    p.add_argument('--input-ref',default='f73c1ba1f48d77b4728ce510da97ae8a0885038e')
    a=p.parse_args();a.out=a.out.resolve()
    if (ROOT/'repro').resolve() not in a.out.parents:raise ValueError('isolated repro output required')
    a.out.mkdir(parents=True,exist_ok=False);sources={}
    def snapshot(rel):
        f=a.out/'source_snapshot'/rel;f.parent.mkdir(parents=True,exist_ok=True)
        b=subprocess.check_output(['git','show',a.input_ref+':'+rel],cwd=ROOT);f.write_bytes(b)
        sources[rel]=hashlib.sha256(b).hexdigest();return f
    market=load_market(snapshot('forward/e21/live_market.csv'))
    market=market[market.date<='2026-09-29']
    if a.append_tip:
        market=append_market(market,load_market(a.market_tip),a.asof)
        sources['tip:market']=hashlib.sha256(a.market_tip.read_bytes()).hexdigest()
    dividend_path=snapshot('data/dividend_events/e22_dividend_events.csv')
    if a.append_tip:
        dividend_path=append_dividends(dividend_path,a.dividend_tip,a.out/'dividends_append_only.csv',a.asof)
        sources['tip:dividends']=hashlib.sha256(a.dividend_tip.read_bytes()).hexdigest()
    dividends=load_dividends(dividend_path)
    off_path=snapshot('data/def_proxies/00631L_ohlcv.csv')
    if a.append_tip:
        original=pd.read_csv(off_path,parse_dates=['date'])
        tip_path=a.off_tip
        tip=pd.read_csv(tip_path,parse_dates=['date'])
        tip=tip[(tip.date>'2026-09-29')&(tip.date<=a.asof)]
        off_path=a.out/'off_append_only.csv'
        pd.concat([original[original.date<='2026-09-29'],tip],ignore_index=True).to_csv(off_path,index=False)
        sources['tip:00631L']=hashlib.sha256(tip_path.read_bytes()).hexdigest()
    parent.sat.load_market=lambda:market.copy()
    parent.sat.load_dividends=lambda:dividends.copy()
    original_off=parent.sat.load_inv_bars
    def load_off():
        parent.sat.DEF_PRICE=off_path
        return original_off()
    parent.sat.load_inv_bars=load_off
    parent.OUT=a.out/'outputs'
    simulate=parent.simulate_core;names=iter(['OFFENSE','COMP_H150_x_A20','SAT_A20_RELAX'])
    def captured(*args,**kwargs):
        name=next(names);result=simulate(*args,**kwargs)
        result[0].to_csv(a.out/('nav_'+name+'.csv'),index=False)
        result[1].to_csv(a.out/('fills_'+name+'.csv'),index=False)
        (a.out/('meta_'+name+'.json')).write_text(json.dumps(result[2],indent=2,default=str))
        return result
    parent.simulate_core=captured
    report=parent.build_ledgers();parity={}
    for book in ['COMP_H150_x_A20','SAT_A20_RELAX']:
        rel='repro/fin-sat-path3-daily-share-ssot-stagea/outputs/daily_shares_'+book+'.csv'
        old=shares_panel_from_long(pd.read_csv(snapshot(rel),dtype={'code':str}))
        new=shares_panel_from_long(pd.read_csv(parent.OUT/('daily_shares_'+book+'.csv'),dtype={'code':str}))
        candidate_days=len(new)
        new=new[new.index<=pd.Timestamp('2026-09-29')]
        idx=old.index.union(new.index);cols=old.columns.union(new.columns)
        delta=new.reindex(index=idx,columns=cols,fill_value=0).subtract(old.reindex(index=idx,columns=cols,fill_value=0))
        mismatch=(delta.abs()>1e-6).any(axis=1)
        parity[book]=dict(max_share_difference=float(delta.abs().max().max()),mismatched_dates=int(mismatch.sum()),
                          first_mismatch=None if not mismatch.any() else str(mismatch[mismatch].index[0].date()),
                          pass_parity=bool(not mismatch.any()),reference_days=len(old),candidate_days=candidate_days)
        delta.to_csv(a.out/('share_difference_'+book+'.csv'))
    (a.out/'summary.json').write_text(json.dumps(dict(status='PARENT_PARITY' if all(v['pass_parity'] for v in parity.values()) else 'PARENT_MISMATCH',
        input_ref=a.input_ref,asof=a.asof,append_only=a.append_tip,build=report,parity=parity,source_sha256=sources,
        limits=['Legacy uncorrected parent simulation retained for reproduction; not real execution validation']),indent=2))
    print(parity,flush=True)
if __name__=='__main__':main()
