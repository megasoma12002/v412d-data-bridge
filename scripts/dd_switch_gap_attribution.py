#!/usr/bin/env python3
"""Exact close-to-close book bridge + original/R1 mother parity audit.

Accounting terms are exact; they are not separable causal effects of repairing
sources. A controlled active-gate ablation separately tests the exit decision.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import live_tipsoft_dd_switch as gate
from dd_switch_full_live_books import load_prices,prices_on,reconstruct
from e22_dividend_accounting import load_dividend_events

ROOT=Path(__file__).resolve().parents[1]

def book_flows(nav,positions,fills,panel,initial):
    previous={};previous_prices=None;previous_nav=initial;rows=[]
    snapshots={d:dict(zip(g.code,g.quantity)) for d,g in positions.groupby('date')}
    for r in nav.itertuples():
        day=r.date;close=prices_on(panel,day,'close');op=prices_on(panel,day,'open')
        codes=set(previous)|set(snapshots.get(day,{}))|set(fills.loc[fills.fill_date==day,'code'])
        day_rows=[]
        for code in sorted(codes):
            fs=fills[(fills.fill_date==day)&(fills.code==code)]
            holding=previous.get(code,0)*(close[code]-previous_prices[code]) if previous_prices else 0
            trading=sum((1 if f.side=='BUY' else -1)*f.quantity*(close[code]-op[code]) for f in fs.itertuples())
            slip=sum((1 if f.side=='BUY' else -1)*f.quantity*(op[code]-f.fill_price) for f in fs.itertuples())
            fees=-float(fs.fees_tax.sum())
            day_rows.append(dict(date=day,code=code,holding_pnl=holding,open_to_close_trade_pnl=trading,
                                 execution_price_pnl=slip,fee_pnl=fees,total=holding+trading+slip+fees))
        residual=float(r.nav)-previous_nav-sum(x['total'] for x in day_rows)
        # This actual window has no eligible dividends, receivables or splits.
        # Refuse to hide corporate-action or price errors in a residual bucket.
        if abs(residual)>1e-4:
            raise ValueError('Unclassified book action / residual on '+day+': '+str(residual))
        rows.extend(day_rows)
        previous=snapshots.get(day,{})
        previous_prices=close;previous_nav=float(r.nav)
    return pd.DataFrame(rows)

def mother_features(l4,trail,base,p3):
    def nav(path):return pd.read_csv(path,parse_dates=['date']).set_index('date').nav
    l,t,b,p=map(nav,(l4,trail,base,p3))
    joined=pd.concat({'l4':l.pct_change().fillna(0),'trail':t.pct_change().fillna(0)},axis=1,join='inner').dropna()
    curve=(1+joined).cumprod();dd=curve/curve.cummax()-1
    prem=pd.concat({'base':b.pct_change().fillna(0),'p3':p.pct_change().fillna(0)},axis=1,join='inner').dropna()
    score=(prem.p3-prem.base).shift(1).rolling(42,min_periods=14).sum()
    wt=dd.trail>=dd.l4
    out=pd.DataFrame(dict(want_trail=wt,l4_dd=dd.l4,trail_dd=dd.trail,
                         premium42=score,trail_on=score.fillna(0)>=-.01))
    out=out.dropna(subset=['l4_dd','trail_dd'])
    out['want_trail']=out.want_trail.astype(bool)
    out['active']=~out.want_trail|out.trail_on
    return out,(l,t,b,p)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-gap-attribution')
    p.add_argument('--ablation',type=Path)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    panel,calendar=load_prices()
    events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    sources={'ORIGINAL':ROOT/'forward/e21','R1':ROOT/'repro/dd-switch-live-t1-r1'}
    if a.ablation:sources['FORCED_ACTIVE']=a.ablation.resolve()
    flow={};reports={};hashes={}
    for name,source in sources.items():
        nav,pos,_,_,_,_,report=reconstruct(source,panel,calendar,events)
        fills=pd.read_csv(source/'fills.csv',dtype={'code':str})
        flow[name]=book_flows(nav,pos,fills,panel,report['initial'])
        reports[name]=report
        flow[name].to_csv(a.out/(name+'_asset_daily_pnl.csv'),index=False)
        nav.to_csv(a.out/(name+'_complete_nav.csv'),index=False)
        for file in ('fills.csv','orders.csv','signals.csv'):
            hashes[str((source/file).relative_to(ROOT))]=hashlib.sha256((source/file).read_bytes()).hexdigest()
    terms=['holding_pnl','open_to_close_trade_pnl','execution_price_pnl','fee_pnl']
    o=flow['ORIGINAL'].set_index(['date','code'])[terms]
    r=flow['R1'].set_index(['date','code'])[terms]
    delta=r.subtract(o,fill_value=0)
    delta['net_gap']=delta.sum(axis=1)
    delta.reset_index().to_csv(a.out/'gap_asset_daily.csv',index=False)
    delta.groupby(level='date').sum().to_csv(a.out/'gap_daily.csv')
    delta.groupby(level='code').sum().sort_values('net_gap').to_csv(a.out/'gap_by_asset.csv')
    totals=delta[terms].sum().to_dict()
    target=reports['R1']['final_nav']-reports['ORIGINAL']['final_nav']
    if abs(sum(totals.values())-target)>1e-4:raise ValueError('Gap decomposition identity failed')
    orig_paths=[gate.DEFAULT_L4_NAV,gate.DEFAULT_TRAIL_NAV,gate.LIVESTACK_L3,gate.LIVESTACK_P3]
    r1_paths=[ROOT/'repro/dd-switch-t1-r1/nav_L4.csv',ROOT/'repro/dd-switch-t1-r1/nav_TRAIL.csv',
              ROOT/'repro/dd-switch-t1-r1/controller_base.csv',ROOT/'repro/dd-switch-t1-r1/nav_L4.csv']
    original,original_navs=mother_features(*orig_paths);rebuilt,rebuilt_navs=mother_features(*r1_paths)
    common=original.index.intersection(rebuilt.index)
    parity=pd.concat({'original':original.loc[common],'R1':rebuilt.loc[common]},axis=1)
    parity.to_csv(a.out/'mother_overlap.csv')
    count={key:int(original.loc[common,key].ne(rebuilt.loc[common,key]).sum()) for key in ('want_trail','trail_on','active')}
    nav_parity={}
    for key,old,new in zip(('L4','TRAIL','BASE','P3'),original_navs,rebuilt_navs):
        idx=old.index.intersection(new.index)
        rel_old=old.loc[idx]/old.loc[idx].iloc[0]
        rel_new=new.loc[idx]/new.loc[idx].iloc[0]
        nav_parity[key]=dict(common_dates=len(idx),reference_start=str(old.index.min().date()),
                             candidate_start=str(new.index.min().date()),
                             max_normalized_relative_error=float((rel_new/rel_old-1).abs().max()))
    contract=dict(mode='AS_IS_RESEARCH_LINEAGE_PARITY_BEFORE_REFRESH',
                  status='BLOCK_R1_AS_DROP_IN_ORIGINAL_REFRESH' if any(count.values()) else 'GATE_PARITY_ONLY',
                  reference_cutoff=str(original.index.max().date()),
                  reference_source_files=[str(p.relative_to(ROOT)) for p in orig_paths],
                  rules=dict(dd_choice='TRAIL_DD >= L4_DD',trail_window=42,min_observations=14,
                             premium_shift=1,trail_threshold=-.01),
                  required_checks=['Reproduce original mother NAV/returns and decisions on their historical prefix before adding new dates',
                                   'Keep original construction, full-account scope, initial state, corporate actions and capital reentry budgets identifiable',
                                   'Date/corporate-action/execution corrections get a separate model version with measured deviations, not silent substitution',
                                   'Continue original parents with real updated prices and actual book state; never forward-fill mother NAV',
                                   'Prove causal signal availability and jointly funded share/cash trades before promotion'],
                  observed_disagreement=count,normalized_nav_parity=nav_parity,
                  notes='Diagnostic contract only; no runtime/production approval bypass or automatic model promotion')
    (a.out/'original_mother_reconstruction_contract.json').write_text(json.dumps(contract,indent=2))
    for path in orig_paths+r1_paths:hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    signals=[]
    for name,source in sources.items():
        df=pd.read_csv(source/'signals.csv')
        cols=['date','path3_t0_weight_reason','path3_t0_n_orders','tipsoft_dd_want_trail',
              'tipsoft_dd_trail42_on','tipsoft_dd_path3_active','tipsoft_dd_reason']
        signals.append(df.loc[df.date>='2026-09-29',[c for c in cols if c in df]].assign(source=name))
    pd.concat(signals).to_csv(a.out/'recent_signal_comparison.csv',index=False)
    results=dict(status='EXACT_ACCOUNTING_BRIDGE_NOT_ORIGINAL_MODEL_REPRODUCTION',sources=reports,
                 gap_R1_minus_original=target,accounting_components=totals,
                 bridge_residual=sum(totals.values())-target,
                 mother_common_observations=len(common),mother_disagreement=count,
                 mother_normalized_nav_parity=nav_parity,
                 original_refresh_parity_status=contract['status'],
                 original_mother_end=str(original.index.max().date()),
                 limits=['Accounting decomposition is exact but not independent causal attribution of source changes',
                         'Force-active arm is hypothetical exit ablation with same rebuilt parents and DD T+1 clock, not original strategy',
                         'Original research mothers end 9/29; do not forward-fill their NAV or pretend to know later gates',
                         'Mother parity replicates production inner-join semantics; calendar defects remain separate issues',
                         'Original research return stitches, full holdings feedback and T0 execution still require faithful reconstruction'],
                 source_sha256=hashes)
    if a.ablation:
        results['forced_active_minus_R1']=reports['FORCED_ACTIVE']['final_nav']-reports['R1']['final_nav']
        results['forced_active_minus_original']=reports['FORCED_ACTIVE']['final_nav']-reports['ORIGINAL']['final_nav']
        forced=flow['FORCED_ACTIVE'].set_index(['date','code'])[terms]
        remain=forced.subtract(o,fill_value=0)
        remain.groupby(level='code').sum().to_csv(a.out/'remaining_gap_by_asset.csv')
        results['forced_active_remaining_gap_components']=remain.sum().to_dict()
        results['exit_ablation_gap_components']=forced.subtract(r,fill_value=0).sum().to_dict()
        results['gap_closed_by_exit_ablation_pct']=results['forced_active_minus_R1']/(-target)*100
    (a.out/'summary.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({k:v for k,v in results.items() if k!='source_sha256'},indent=2))

if __name__=='__main__':main()
