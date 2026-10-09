#!/usr/bin/env python3
"""Run every uncommitted official session in order, with day-cut DD controls.

Paper catch-up is a historical-price simulation, never a broker execution claim.
Existing committed dates cannot be rewound or repaired by inserting fake fills.
"""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
import pandas as pd
from dd_switch_live_replay import verify_runtime_generation
from dd_switch_daily_refresh import VERSION,KEYS
from live_ledger import ALL
from twse_session_sources import cached_load_calendar_window
ROOT=Path(__file__).resolve().parents[1]

def pending_sessions(last,asof,calendar,market):
    if asof<last:raise ValueError('Range runner cannot rewind committed state')
    wanted=[str(d) for d in sorted(calendar) if last<str(d)<=asof]
    required=set(ALL+['TAIEX'])
    for day in wanted:
        rows=market[market.date==day]
        if not required.issubset(set(rows.code)):raise ValueError('Cannot catch up incomplete market session '+day)
        numeric=rows[rows.code.isin(required)][['open','close','adj_close']]
        if numeric.isna().any().any() or (numeric<=0).any().any():raise ValueError('Invalid catch-up prices '+day)
    return wanted

def daycut(source,meta,day,destination):
    generation=verify_runtime_generation(source,meta)
    dest=destination/'generations/day';dest.mkdir(parents=True,exist_ok=True)
    current={**meta,'asof':day,'generation':'generations/day','hashes':{}}
    for key,name in meta['files'].items():
        frame=pd.read_csv(generation/name,dtype={'code':str})
        cut=frame[frame.date<=day]
        if cut.empty or str(cut.date.max())[:10]!=day:raise ValueError('Missing day-cut input '+key+' '+day)
        target=dest/name;cut.to_csv(target,index=False)
        current['hashes'][key]=hashlib.sha256(target.read_bytes()).hexdigest()
    (destination/'current.json').write_text(json.dumps(current,indent=2))
    return current

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--asof',required=True);p.add_argument('--state-dir',type=Path,default=ROOT/'forward/e21')
    p.add_argument('--market',type=Path,default=ROOT/'forward/e21/live_market.csv')
    p.add_argument('--inputs-dir',type=Path,default=ROOT/'data/dd_switch_runtime')
    p.add_argument('--work-dir',type=Path,required=True);p.add_argument('--allow-noncanonical-paths',action='store_true')
    p.add_argument('--skip-excel-dashboard',action='store_true');a=p.parse_args()
    a.state_dir=a.state_dir.resolve();a.market=a.market.resolve();a.inputs_dir=a.inputs_dir.resolve();a.work_dir=a.work_dir.resolve()
    if (ROOT/'repro').resolve() not in a.work_dir.parents:raise SystemExit('Range work directory must be isolated repro')
    state=json.loads((a.state_dir/'portfolio_state.json').read_text());last=str(state['last_date'])[:10]
    market=pd.read_csv(a.market,dtype={'code':str})
    if market.duplicated(['date','code']).any():raise ValueError('Duplicate range market observations')
    calendar=set()
    for year in range(int(last[:4]),int(a.asof[:4])+1):
        sessions,_=cached_load_calendar_window(year);calendar.update(sessions)
    days=pending_sessions(last,a.asof,calendar,market)
    meta=json.loads((a.inputs_dir/'current.json').read_text());verify_runtime_generation(a.inputs_dir,meta)
    if meta.get('version')!=VERSION or not meta.get('prefix_certified') or set(meta['files'])!=KEYS or meta['asof']!=a.asof:
        raise ValueError('Range requires full certified same-asof original generation')
    a.work_dir.mkdir(parents=True,exist_ok=False)
    # Validate every future day before advancing even the first state.
    for day in days:daycut(a.inputs_dir,meta,day,a.work_dir/day/'runtime')
    result=dict(status='ALL_NEW_SESSIONS_PROCESSED',previous_last_date=last,asof=a.asof,
        mode='PAPER_HISTORICAL_CATCHUP' if len(days)>1 else 'PAPER_NEXT_SESSION',days=days,
        existing_committed_history_unchanged=True)
    for day in days:
        runtime=a.work_dir/day/'runtime';env={**os.environ,'E21_DD_INPUTS_DIR':str(runtime),'E21_FILL_PORT':'paper'}
        command=[sys.executable,str(ROOT/'scripts/e21_forward_pipeline.py'),'--asof',day,
                 '--state-dir',str(a.state_dir),'--market',str(a.market),'--fill-port','paper']
        if a.allow_noncanonical_paths:command.append('--allow-noncanonical-paths')
        if a.skip_excel_dashboard:command.append('--skip-excel-dashboard')
        with (a.work_dir/(day+'.log')).open('w') as log:
            subprocess.run(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        updated=json.loads((a.state_dir/'portfolio_state.json').read_text())
        if updated['last_date']!=day:raise RuntimeError('Session did not commit expected date')
        print(day,'PASS',flush=True)
    if days:
        subprocess.run([sys.executable,str(ROOT/'scripts/e21_qc.py'),'--state-dir',str(a.state_dir),
                        *(['--allow-noncanonical-paths'] if a.allow_noncanonical_paths else [])],cwd=ROOT,check=True)
    if days:(a.state_dir/'session_catchup_audit.json').write_text(json.dumps(result,indent=2))
    (a.work_dir/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()
