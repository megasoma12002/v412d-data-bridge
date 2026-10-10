#!/usr/bin/env python3
"""Reconcile original-lineage production replay and bridge recovery vs R1.

No historical research CAGR inference; before-seed actual records are preserved.
"""
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from dd_switch_full_live_books import load_prices,reconstruct
from dd_switch_gap_attribution import book_flows
from e22_dividend_accounting import load_dividend_events
from dd_switch_live_replay import verify_runtime_generation
import live_tipsoft_dd_switch as gate
ROOT=Path(__file__).resolve().parents[1]
TERMS=['holding_pnl','open_to_close_trade_pnl','execution_price_pnl','fee_pnl']

def clock_audit(fills,orders,calendar,seed):
    dates=sorted(calendar);next_day=dict(zip(dates[:-1],dates[1:]))
    post=fills[fills.fill_date>seed].copy()
    if (post.fill_date<=post.signal_date).any():raise ValueError('Non-T+1 fill after seed')
    if (post.quantity%1000).abs().gt(1e-6).any():raise ValueError('Non-board-lot new fill')
    stamped=orders[orders.signal_date>seed]
    path=stamped[stamped.get('carve_out_id',pd.Series('',index=stamped.index)).fillna('')=='T0_CARVE_FIN_SAT_SWITCH']
    if len(path) and not path.execution_clock.eq('NEXT_SESSION_OPEN').all():raise ValueError('DD order lacks T+1 qualification')
    post['next_session']=post.signal_date.map(next_day)
    if post.next_session.isna().any() or (post.fill_date<post.next_session).any():raise ValueError('Fill before next session')
    return dict(post_seed_fills=len(post),same_day_fills=int((post.fill_date==post.signal_date).sum()),
                next_session_fills=int(post.fill_date.eq(post.next_session).sum()),
                delayed_fills=int(post.fill_date.gt(post.next_session).sum()),
                path3_post_seed_orders=len(path),all_path3_orders_next_session_open=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lineage-live',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seed',default='2026-09-29');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    panel,calendar=load_prices()
    events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    sources={'ORIGINAL':ROOT/'forward/e21','R1':ROOT/'repro/dd-switch-live-t1-r1',
             'FORCED_ACTIVE':ROOT/'repro/dd-switch-gap-forced-active','LINEAGE_T1':a.lineage_live.resolve()}
    reports={};flows={};hashes={};clocks={};signal_rows=[]
    for name,source in sources.items():
        nav,pos,audit,book,_,_,report=reconstruct(source,panel,calendar,events)
        fills=pd.read_csv(source/'fills.csv',dtype={'code':str});orders=pd.read_csv(source/'orders.csv',dtype={'code':str})
        flows[name]=book_flows(nav,pos,fills,panel,report['initial']).set_index(['date','code'])
        reports[name]=report
        report['post_seed_fee_tax']=float(fills.loc[fills.fill_date>a.seed,'fees_tax'].sum())
        clocks[name]=clock_audit(fills,orders,calendar,a.seed)
        nav.to_csv(a.out/(name+'_complete_nav.csv'),index=False);pos.to_csv(a.out/(name+'_positions.csv'),index=False)
        audit.to_csv(a.out/(name+'_book_residuals.csv'),index=False)
        flows[name].to_csv(a.out/(name+'_asset_daily_pnl.csv'))
        signals=pd.read_csv(source/'signals.csv')
        cols=['date','path3_t0_weight_reason','path3_t0_n_orders','tipsoft_dd_want_trail','tipsoft_dd_trail42_on','tipsoft_dd_path3_active','tipsoft_dd_reason']
        signal_rows.append(signals.loc[signals.date>a.seed,[c for c in cols if c in signals]].assign(source=name))
        for f in ['fills.csv','orders.csv','signals.csv','portfolio_state.json','nav.csv']:
            hashes[str((source/f).relative_to(ROOT))]=hashlib.sha256((source/f).read_bytes()).hexdigest()
    pd.concat(signal_rows).to_csv(a.out/'signal_comparison.csv',index=False)
    bridges={}
    for other in ['ORIGINAL','R1','FORCED_ACTIVE']:
        diff=flows['LINEAGE_T1'][TERMS].subtract(flows[other][TERMS],fill_value=0)
        totals=diff.sum().to_dict();target=reports['LINEAGE_T1']['final_nav']-reports[other]['final_nav']
        residual=sum(totals.values())-target
        if abs(residual)>1e-4:raise ValueError('Bridge residual')
        diff.to_csv(a.out/('LINEAGE_minus_'+other+'_asset_daily.csv'))
        diff.groupby(level='code').sum().to_csv(a.out/('LINEAGE_minus_'+other+'_by_asset.csv'))
        bridges[other]=dict(total=target,components=totals,residual=residual)
    original_gap=reports['ORIGINAL']['final_nav']-reports['R1']['final_nav']
    recovered=bridges['R1']['total']
    replay=json.loads((a.lineage_live/'summary.json').read_text())
    runtime=Path(replay['runtime_source']);manifest=runtime/'current.json';meta=json.loads(manifest.read_text())
    generation=verify_runtime_generation(runtime,meta)
    want=gate.want_trail_series(l4_nav_path=generation/meta['files']['l4'],trail_nav_path=generation/meta['files']['trail'])
    on=gate.trail42_on_series(l3_nav_path=generation/meta['files']['base'],p3_nav_path=generation/meta['files']['l4'])
    active=gate.path3_active_series(want,on)
    live_signals=pd.read_csv(a.lineage_live/'signals.csv').set_index('date')
    for day in live_signals.index[live_signals.index>a.seed]:
        if not bool(live_signals.loc[day,'tipsoft_dd_path3_active'])==bool(active.loc[pd.Timestamp(day)]):
            raise ValueError('Replay gate differs from full verified input asof')
    summary=dict(status='RECONCILED_PRODUCTION_T1_ORIGINAL_LINEAGE_AFTER_SEED',seed=a.seed,sources=reports,clock_audits=clocks,
                 bridges=bridges,original_minus_R1=original_gap,recovered_vs_R1=recovered,
                 recovered_gap_pct=100*recovered/original_gap,remaining_original_minus_lineage=-bridges['ORIGINAL']['total'],
                 source_sha256=hashes,runtime_manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                 replay_gate_matches_packaged_lineage=True,
                 program_sha256={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in
                     [Path(__file__).resolve(),ROOT/'scripts/dd_switch_original_runtime.py',ROOT/'scripts/dd_switch_live_replay.py']},limits=[
                     'Only observed 2026-08-24..10-08 window; production regenerated after 9/29, prior actual records retained',
                     'Current production configuration is held fixed after seed; not a full-history replay of historical configuration changes',
                     'Controller shadows retain original research stitch and calendar/corporate-action assumptions',
                     'Paper fixed-open slippage and fees, no depth/participation/auction-liquidity proof',
                     'No T0 execution validation or broker fills; no automatic model promotion'])
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2))
if __name__=='__main__':main()
