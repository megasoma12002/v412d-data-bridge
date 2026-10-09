#!/usr/bin/env python3
"""Build locked original DD controls, certify prefix, then atomically publish.

Generation publication is independent from forward-state writes. An incomplete
build never changes the current pointer. Legacy stitched NAVs are retained only
as close-T control features; all resulting orders remain next-session orders.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,uuid
from pathlib import Path
import pandas as pd
from dd_switch_live_replay import verify_runtime_generation
from live_ledger import ALL,atomic_write_json
from twse_session_sources import cached_load_calendar_window
ROOT=Path(__file__).resolve().parents[1]
VERSION='DD_SWITCH_ORIGINAL_LINEAGE_DAILY_V1'
KEYS={'off','base','l4','trail','dd','signal','shares_COMP_H150_x_A20','shares_SAT_A20_RELAX'}

def assert_previous_generation_preserved(previous_generation,new_generation,files,previous_asof):
    for key,name in files.items():
        old=pd.read_csv(previous_generation/name,dtype={'code':str})
        new=pd.read_csv(new_generation/name,dtype={'code':str})
        old=old[old.date<=previous_asof].reset_index(drop=True)
        new=new[new.date<=previous_asof].reset_index(drop=True)
        try:pd.testing.assert_frame_equal(old,new,check_dtype=False,check_exact=False,rtol=1e-10,atol=1e-8)
        except AssertionError as error:raise ValueError('Published original prefix revised: '+key) from error
    import live_tipsoft_dd_switch as gate
    for calculate,args in [(gate.want_trail_series,dict(l4_nav_path='l4',trail_nav_path='trail')),
                           (gate.trail42_on_series,dict(l3_nav_path='base',p3_nav_path='l4'))]:
        old=calculate(**{k:previous_generation/files[v] for k,v in args.items()})
        new=calculate(**{k:new_generation/files[v] for k,v in args.items()})
        old=old.loc[:previous_asof];new=new.loc[:previous_asof]
        if not old.equals(new):raise ValueError('Published original gate decisions revised')

def validate_market_tip(path,asof):
    frame=pd.read_csv(path,dtype={'code':str},parse_dates=['date'])
    if frame.duplicated(['date','code']).any():raise ValueError('Duplicate market observations')
    dates=[]
    for year in range(2026,pd.Timestamp(asof).year+1):
        sessions,_=cached_load_calendar_window(year)
        dates.extend(str(d) for d in sessions if '2026-09-29'<str(d)<=asof)
    required=set(ALL+['TAIEX'])
    for day in [asof]+dates:
        rows=frame[frame.date==pd.Timestamp(day)]
        if not required.issubset(set(rows.code)):raise ValueError('Incomplete market session: '+day)
        numeric=rows[rows.code.isin(required)][['open','close','adj_close']]
        if numeric.isna().any().any() or (numeric<=0).any().any():raise ValueError('Invalid market prices: '+day)
    return dates

def publish_verified_runtime(source,destination,asof):
    source=Path(source).resolve();destination=Path(destination).resolve()
    meta=json.loads((source/'current.json').read_text());generation=verify_runtime_generation(source,meta)
    if meta.get('version')!='DD_SWITCH_ORIGINAL_LINEAGE_T1_RESEARCH' or not meta.get('original_research_preserved'):
        raise ValueError('Only certified original lineage may be published')
    certification=meta.get('certification') or {}
    expected_refs=dict(live_stack='5449f76b3a3feba434f40e0c5e10483e32c00b44',
        upper_layers='97933be85192e8d0ef89695be0c292342bba694d',parent_ledgers='f73c1ba1f48d77b4728ce510da97ae8a0885038e')
    if (certification.get('status')!='ORIGINAL_RESEARCH_PREFIX_REPRODUCED_AND_APPEND_ONLY_EXTENDED'
        or certification.get('construction_refs')!=expected_refs
        or any((certification.get('prefix_gate_disagreement') or {'missing':1}).values())
        or certification.get('parent_max_share_difference')!=0
        or certification.get('mother_max_relative_error',1)>1e-10):
        raise ValueError('Original prefix certification required for publication')
    if meta['asof']!=asof or set(meta['files'])!=KEYS:raise ValueError('Incomplete same-day original generation')
    for key,name in meta['files'].items():
        frame=pd.read_csv(generation/name,usecols=['date'])
        if frame.empty or str(frame.date.max())[:10]!=asof:raise ValueError('Stale original generation: '+key)
    previous_pointer=destination/'current.json'
    if previous_pointer.exists():
        previous=json.loads(previous_pointer.read_text())
        if previous.get('version')==VERSION:
            if previous['asof']>asof:raise ValueError('Cannot rewind published runtime')
            previous_generation=verify_runtime_generation(destination,previous)
            if previous['files']!=meta['files']:raise ValueError('Original runtime file contract changed')
            assert_previous_generation_preserved(previous_generation,generation,meta['files'],previous['asof'])
    digest=hashlib.sha256(json.dumps(meta['hashes'],sort_keys=True).encode()).hexdigest()[:20]
    relative='generations/original-'+asof+'-'+digest
    target=destination/relative
    if target.exists():
        for key,name in meta['files'].items():
            if hashlib.sha256((target/name).read_bytes()).hexdigest()!=meta['hashes'][key]:
                raise ValueError('Published generation corruption; refuse overwrite')
    else:
        temporary=destination/'generations'/('.building-'+uuid.uuid4().hex)
        temporary.mkdir(parents=True,exist_ok=False)
        try:
            for name in meta['files'].values():shutil.copyfile(generation/name,temporary/name)
            os.replace(temporary,target)
        except BaseException:
            shutil.rmtree(temporary,ignore_errors=True);raise
    pointer={**meta,'generation':relative,'version':VERSION,
        'controller_model_scope':'ORIGINAL_LEGACY_CLOSE_FEATURES_FOR_T1_FORWARD',
        'prefix_certified':True,'clock':'CLOSE_T_TO_NEXT_SESSION_OPEN'}
    verify_runtime_generation(destination,pointer)
    atomic_write_json(destination/'current.json',pointer)
    return pointer

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--asof',required=True);p.add_argument('--market',type=Path,default=ROOT/'forward/e21/live_market.csv')
    p.add_argument('--dividends',type=Path,default=ROOT/'data/dividend_events/e22_dividend_events.csv')
    p.add_argument('--off-tip',type=Path);p.add_argument('--refresh-prices',action='store_true')
    p.add_argument('--out',type=Path,required=True);p.add_argument('--publish',action='store_true')
    p.add_argument('--runtime-dir',type=Path,default=ROOT/'data/dd_switch_runtime');a=p.parse_args()
    a.out=a.out.resolve();a.market=a.market.resolve();a.dividends=a.dividends.resolve()
    if (ROOT/'repro').resolve() not in a.out.parents:raise SystemExit('Build directory must be isolated under repro')
    if a.asof<'2026-09-29':raise SystemExit('Original daily append starts at certified 9/29 boundary')
    validate_market_tip(a.market,a.asof);a.out.mkdir(parents=True,exist_ok=False)
    off=a.off_tip.resolve() if a.off_tip else None
    if a.refresh_prices:
        from dd_switch_rebuild import refresh_off
        price_dir=a.out/'official-prices';price_dir.mkdir()
        base=None
        pointer=a.runtime_dir/'current.json'
        if pointer.exists():
            prior=json.loads(pointer.read_text())
            if prior.get('version')==VERSION and prior.get('prefix_certified') and prior['asof']<=a.asof:
                prior_generation=verify_runtime_generation(a.runtime_dir,prior)
                base=prior_generation/prior['files']['off']
        refresh_off(pd.Timestamp(a.asof),price_dir,base_path=base,calendar_path=a.market,
                    append_after='2026-09-29')
        off=price_dir/'00631L_ohlcv.csv'
    if off is None:raise SystemExit('Explicit official off-tip or --refresh-prices required')
    off_frame=pd.read_csv(off,parse_dates=['date'])
    if off_frame.date.max()<pd.Timestamp(a.asof):raise SystemExit('00631L source does not cover asof')
    def run(script,*args):
        command=[sys.executable,str(ROOT/'scripts'/script),*map(str,args)]
        with (a.out/(script+'.log')).open('w') as log:
            subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        print(script,'PASS',flush=True)
    parents=a.out/'parents';lineage=a.out/'lineage';audit=a.out/'audit';prefix=a.out/'prefix';prefix.mkdir()
    shutil.copyfile(ROOT/'repro/dd-switch-original-lineage-verified/prefix_parity.json',prefix/'summary.json')
    run('dd_switch_original_parents.py','--out',parents,'--asof',a.asof,'--append-tip',
        '--market-tip',a.market,'--off-tip',off,'--dividend-tip',a.dividends)
    run('dd_switch_original_reproduction.py','--out',lineage,'--asof',a.asof,'--extended-parents',parents,
        '--input-ref','5449f76b3a3feba434f40e0c5e10483e32c00b44','--market-tip',a.market,'--dividend-tip',a.dividends)
    run('dd_switch_original_audit.py','--source',lineage,'--prefix',prefix,'--parents',parents,'--out',audit)
    staged=a.out/'runtime'
    run('dd_switch_original_runtime.py','--lineage',lineage,'--parents',parents,'--audit',audit,'--out',staged)
    meta=json.loads((staged/'current.json').read_text());verify_runtime_generation(staged,meta)
    result=dict(status='VERIFIED_ORIGINAL_SAME_DAY_READY',asof=a.asof,staged_runtime=str(staged),published=False,
        source_market_sha256=hashlib.sha256(a.market.read_bytes()).hexdigest(),
        audit_sha256=hashlib.sha256((audit/'summary.json').read_bytes()).hexdigest())
    if a.publish:
        pointer=publish_verified_runtime(staged,a.runtime_dir,a.asof)
        result.update(published=True,runtime=str(a.runtime_dir.resolve()),generation=pointer['generation'])
    (a.out/'refresh_summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
