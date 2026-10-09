#!/usr/bin/env python3
"""Separate fixed-fill clock attribution from causal handoff policy feedback.

Same-close is an unavailable-price diagnostic, not a deployable T0 strategy.
Accepted fills are frozen for clock attribution; feedback policies regenerate
orders daily with identical frozen original controls and actual cash/holdings.
"""
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from dd_switch_full_live_books import Book,load_prices,metrics,reconstruct
from dd_switch_original_live_audit import clock_audit
from e22_dividend_accounting import load_dividend_events
from live_ledger import fees_tax_for
ROOT=Path(__file__).resolve().parents[1]
SEED='2026-09-29'
def clock_price(panel,row,mode):
    day=row.signal_date if mode=='signal_close' else row.fill_date
    raw=float(panel.loc[(day,str(row.code)),'close' if mode!='next_open' else 'open'])
    return day,raw*(1+row.slippage_bp/10000 if row.side=='BUY' else 1-row.slippage_bp/10000)
def fixed_clock(fills,panel,calendar,initial,mode):
    rows=[]
    for row in fills.itertuples():
        # The six already-authorized 9/29 intents retain their original fills.
        day,price=clock_price(panel,row,mode) if row.signal_date>SEED else (row.fill_date,row.fill_price)
        fee=fees_tax_for(side=row.side,code=row.code,gross=row.quantity*price)
        rows.append(dict(fill_id=row.fill_id,signal_date=row.signal_date,fill_date=day,code=row.code,side=row.side,quantity=row.quantity,fill_price=price,fees_tax=fee))
    transformed=pd.DataFrame(rows);b=Book(initial);nav=[];positions=[];minimum_cash=initial
    for day in calendar:
        today=transformed[transformed.fill_date==day].copy()
        today['buy']=today.side.eq('BUY');today=today.sort_values(['signal_date','buy','fill_id'])
        for row in today.itertuples():
            b.trade(day,row.code,row.side,row.quantity,row.fill_price,row.fees_tax)
            minimum_cash=min(minimum_cash,b.cash)
        close=panel.loc[day,'close'].to_dict();nav.append(dict(date=day,nav=b.nav(close),cash=b.cash))
        for c,q in b.positions.items():positions.append(dict(date=day,code=c,quantity=q))
    return pd.DataFrame(nav),pd.DataFrame(positions),transformed,dict(**metrics(pd.DataFrame(nav),initial),fees_tax=sum(r['fees_tax'] for r in b.fills),minimum_cash_after_trade=minimum_cash)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out=a.out.resolve()
    if (ROOT/'repro').resolve() not in a.out.parents:raise SystemExit('Research output only')
    a.out.mkdir(parents=True,exist_ok=False)
    panel,calendar=load_prices();events=load_dividend_events(ROOT/'data/dividend_events/e22_dividend_events.csv',require_exists=True,fail_closed_amounts=True)
    base=ROOT/'repro/dd-switch-original-live-t1'
    base_nav,_,_,_,_,_,base_report=reconstruct(base,panel,calendar,events)
    assert base_report['dividend_records']==0
    days=base_nav.date.tolist();fills=pd.read_csv(base/'fills.csv',dtype={'code':str})
    controls=['date','tipsoft_dd_want_trail','tipsoft_dd_trail42_on','tipsoft_dd_path3_active']
    expected_controls=pd.read_csv(base/'signals.csv')[controls]
    clock_reports={};clock_navs={};transformed={};final_positions=None
    for mode in ['next_open','signal_close','next_close']:
        nav,pos,f,r=fixed_clock(fills,panel,days,base_report['initial'],mode)
        if mode=='next_open':
            pd.testing.assert_series_equal(nav.nav,base_nav.nav,check_names=False,rtol=1e-12)
            final_positions=pos[pos.date==days[-1]].set_index('code').quantity.sort_index()
        else:
            pd.testing.assert_series_equal(pos[pos.date==days[-1]].set_index('code').quantity.sort_index(),final_positions)
        clock_reports[mode]=r;clock_navs[mode]=nav;transformed[mode]=f
        nav.to_csv(a.out/(mode+'_complete_nav.csv'),index=False);f.to_csv(a.out/(mode+'_fixed_fills.csv'),index=False)
    comparisons=[]
    post=fills[fills.signal_date>SEED]
    for row in post.itertuples():
        op=float(panel.loc[(row.fill_date,row.code),'open']);sc=float(panel.loc[(row.signal_date,row.code),'close']);nc=float(panel.loc[(row.fill_date,row.code),'close'])
        sign=1 if row.side=='BUY' else -1
        comparisons.append(dict(fill_id=row.fill_id,signal_date=row.signal_date,fill_date=row.fill_date,code=row.code,side=row.side,quantity=row.quantity,
            signal_close=sc,next_open=op,next_close=nc,
            signal_close_vs_next_open_gross=sign*row.quantity*(op-sc),
            next_close_vs_next_open_gross=sign*row.quantity*(op-nc)))
    clock_delta=pd.DataFrame(comparisons);clock_delta.to_csv(a.out/'fixed_clock_by_fill.csv',index=False)
    clock_delta.groupby('code')[['signal_close_vs_next_open_gross','next_close_vs_next_open_gross']].sum().to_csv(a.out/'fixed_clock_by_asset.csv')
    reports={};clocks={};audit=[];sources={};tracking=[]
    for policy in ['immediate','two_day','three_day']:
        source=ROOT/('repro/dd-switch-exposure-'+policy)
        nav,pos,resid,book,_,_,r=reconstruct(source,panel,calendar,events)
        f=pd.read_csv(source/'fills.csv',dtype={'code':str});o=pd.read_csv(source/'orders.csv',dtype={'code':str});s=pd.read_csv(source/'signals.csv')
        pd.testing.assert_frame_equal(s[controls],expected_controls)
        if policy=='immediate':pd.testing.assert_frame_equal(f,pd.read_csv(ROOT/'repro/dd-switch-live-repair-range/fills.csv',dtype={'code':str}))
        r.update(policy=policy,nav_gain_vs_immediate=r['final_nav']-base_report['final_nav'],fee_saving_vs_immediate=base_report['fees_tax']-r['fees_tax'],controls_equal=True)
        clocks[policy]=clock_audit(f,o,calendar,SEED);r['new_fills']=clocks[policy]['post_seed_fills']
        for suffix,frame in [('complete_nav',nav),('positions',pos),('book_residuals',resid),('fills',f)]:frame.to_csv(a.out/(policy+'_'+suffix+'.csv'),index=False)
        rows=[json.loads(line) for line in (source/'exposure_audit.jsonl').read_text().splitlines()]
        for row in rows:
            row['original_delta_notional']=sum(abs(q)*float(panel.loc[(row['date'],c),'close']) for c,q in row['original_delta'].items())
            row['staged_unissued_notional']=sum(abs(q-row['emitted_delta'].get(c,0))*float(panel.loc[(row['date'],c),'close']) for c,q in row['original_delta'].items())
            audit.append(row)
        r['first_signal_unissued_notional']=rows[0]['staged_unissued_notional'];r['max_close_target_delta_notional']=max(row['original_delta_notional'] for row in rows)
        for day,g in pos.groupby('date'):
            bpos=pd.read_csv(ROOT/'repro/dd-switch-live-repair-books/LINEAGE_T1_positions.csv',dtype={'code':str});bg=bpos[bpos.date==day]
            pmap=dict(zip(g.code,g.quantity));bmap=dict(zip(bg.code,bg.quantity));value=float(nav.loc[nav.date==day,'nav'].iloc[0])
            gap=sum(abs(pmap.get(c,0)-bmap.get(c,0))*float(panel.loc[(day,c),'close']) for c in set(pmap)|set(bmap))
            tracking.append(dict(policy=policy,date=day,absolute_holdings_difference_notional=gap,difference_pct_nav=gap/value*100))
        reports[policy]=r
        for name in ['fills.csv','orders.csv','signals.csv','portfolio_state.json','exposure_audit.jsonl']:
            sources[str((source/name).relative_to(ROOT))]=hashlib.sha256((source/name).read_bytes()).hexdigest()
    pd.DataFrame(tracking).to_csv(a.out/'daily_holdings_difference.csv',index=False)
    pd.DataFrame(audit).to_json(a.out/'stage_audit.jsonl',orient='records',lines=True)
    pd.DataFrame(reports.values()).to_csv(a.out/'policy_comparison.csv',index=False)
    original=json.loads((ROOT/'repro/dd-switch-live-repair-books/summary.json').read_text())
    for name,value in original['source_sha256'].items():
        if name.startswith('forward/e21/'):
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value
    for key,r in clock_reports.items():
        r['net_gain_vs_next_open']=r['final_nav']-clock_reports['next_open']['final_nav']
        r['fee_difference_vs_next_open']=r['fees_tax']-clock_reports['next_open']['fees_tax']
    result=dict(status='FIXED_CLOCK_ATTRIBUTION_AND_INITIAL_HANDOFF_SENSITIVITY_ONLY',seed=SEED,end=days[-1],clock_reports=clock_reports,feedback_reports=reports,clock_audits=clocks,
        original_bridge=original['bridges']['ORIGINAL'],source_sha256=sources,
        changed_clock_fills=len(post),same_final_shares_all_clock_modes=True,canonical_history_hashes_unchanged=True,
        runtime_manifest_sha256=hashlib.sha256((ROOT/'repro/dd-switch-live-repair-runtime-certified/current.json').read_bytes()).hexdigest(),
        program_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__).resolve(),ROOT/'scripts/dd_switch_exposure_pipeline.py',ROOT/'scripts/dd_switch_live_replay.py']},limits=[
        '32-session book, only seven regenerated dates and one initial handoff; no statistical best-policy claim',
        'Signal-close uses a final-close-derived signal and is unavailable executable T0; attribution upper/reference only',
        'Clock comparison changes exactly 33 fills with signal_date after seed; six 9/29 pending intents stay unchanged; no order regeneration, final pending orders excluded equally',
        'Negative cash or shares rejected; no dividends in observed window; fees recalculated at each price',
        'Feedback staging recalculates target against actual holdings every day; no stale remainder queue',
        'Book flips bypass staging; DD gate downstream overrides staged plans with full exits',
        'Fixed 5bp paper slippage; no opening-auction liquidity or broker capacity evidence',
        'Canonical live history and strategy rules not modified; no deployment'])
    (a.out/'summary.json').write_text(json.dumps(result,indent=2))
    print(pd.DataFrame(reports.values())[['policy','return_pct','observed_mdd_pct','nav_gain_vs_immediate','fee_saving_vs_immediate','new_fills']].to_string(index=False))
    print(json.dumps(clock_reports,indent=2))
if __name__=='__main__':main()
