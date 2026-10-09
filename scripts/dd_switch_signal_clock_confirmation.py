#!/usr/bin/env python3
"""Confirm close-known P3 state -> next-open order semantics.

Prefix perturbation checks information timing on provided data, not historical
publication availability, executable virtual NAV returns, or intraday quotes.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import live_tipsoft_dd_switch as dd
import tipsoft_ip3_fill_lock_stagea as fl
from live_path3_t0_switch_emitter import build_sat_lead_signal,BOOK_COMP,BOOK_SAT
ROOT=Path(__file__).resolve().parents[1]

def virtual_same_day_witness():
    dates=pd.bdate_range('2025-01-01',periods=100)
    codes=fl.SOFT_CORE;px=pd.DataFrame(100.,index=dates,columns=codes)
    a,b=fl.FIN[:2];px.loc[dates[-1],a]=110.;px.loc[dates[-1],b]=90.
    weights={book:pd.DataFrame(0.,index=dates,columns=codes) for book in [BOOK_COMP,BOOK_SAT]}
    weights[BOOK_COMP][a]=1.;weights[BOOK_SAT][b]=1.
    signal=pd.DataFrame({'date':dates,'book':BOOK_COMP});on=pd.Series(1.,index=dates)
    base,_=fl.simulate_fill(fill='ALWAYS_WITHIN',weights_by_book=weights,px=px,signal=signal,i3_on=on)
    changed=signal.copy();changed.loc[len(changed)-1,'book']=BOOK_SAT
    alt,_=fl.simulate_fill(fill='ALWAYS_WITHIN',weights_by_book=weights,px=px,signal=changed,i3_on=on)
    if not base.nav.iloc[:-1].equals(alt.nav.iloc[:-1]):raise ValueError('Witness changes earlier history')
    if np.isclose(base.nav.iloc[-1],alt.nav.iloc[-1]):raise ValueError('Expected same-day virtual return sensitivity')
    return dict(only_signal_changed_on_final_day=True,earlier_nav_unchanged=True,
                final_comp_nav=float(base.nav.iloc[-1]),final_sat_nav=float(alt.nav.iloc[-1]),
                interpretation='Virtual SC NAV uses day-T choice to score day-T return; observable after close, not proved day-T execution')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--runtime',type=Path,default=ROOT/'repro/dd-switch-original-runtime-t1')
    p.add_argument('--parents',type=Path,default=ROOT/'repro/dd-switch-original-parents-extended')
    p.add_argument('--live',type=Path,default=ROOT/'repro/dd-switch-original-live-t1')
    a=p.parse_args();a.runtime=a.runtime.resolve();a.parents=a.parents.resolve();a.live=a.live.resolve();a.out.mkdir(parents=True,exist_ok=False)
    comp=pd.read_csv(a.parents/('nav_'+BOOK_COMP+'.csv'),parse_dates=['date'])[['date','nav']]
    sat=pd.read_csv(a.parents/('nav_'+BOOK_SAT+'.csv'),parse_dates=['date'])[['date','nav']]
    full=build_sat_lead_signal(comp=comp,sat=sat)
    meta=json.loads((a.runtime/'current.json').read_text());generation=a.runtime/meta['generation']
    paths={k:generation/v for k,v in meta['files'].items()}
    l3=dd._load_nav(paths['base']);p3=dd._load_nav(paths['l4'])
    l4=dd._load_nav(paths['l4']);trail=dd._load_nav(paths['trail'])
    def controls(l,b,t,q):
        r=pd.concat({'l4':dd._returns(l),'trail':dd._returns(t)},axis=1,join='inner').dropna()
        curves=(1+r).cumprod();drawdown=curves/curves.cummax()-1
        want=drawdown.trail>=drawdown.l4
        prem=pd.concat({'base':dd._returns(b),'p3':dd._returns(q)},axis=1,join='inner').dropna()
        score=dd._trail_sum(prem.p3-prem.base,42)
        on=score.fillna(0)>=-.01
        return pd.DataFrame({'want_trail':want,'premium42':score,'trail_on':on,'active':dd.path3_active_series(want,on)})
    baseline=controls(l4,l3,trail,p3);checks=[]
    for day in ['2026-09-29','2026-09-30','2026-10-01','2026-10-05']:
        cutoff=pd.Timestamp(day)
        truncated=build_sat_lead_signal(comp=comp[comp.date<=cutoff],sat=sat[sat.date<=cutoff])
        changed_comp=comp.copy();changed_sat=sat.copy()
        changed_comp.loc[changed_comp.date>cutoff,'nav']*=10
        changed_sat.loc[changed_sat.date>cutoff,'nav']*=.1
        mutated=build_sat_lead_signal(comp=changed_comp,sat=changed_sat)
        expected=full[full.date<=cutoff].reset_index(drop=True)
        pd.testing.assert_frame_equal(expected,truncated.reset_index(drop=True))
        pd.testing.assert_frame_equal(expected,mutated[mutated.date<=cutoff].reset_index(drop=True))
        original_inputs=[l4,l3,trail,p3];mutated_inputs=[]
        for i,d in enumerate(original_inputs):
            d=d.copy();d.loc[d.date>cutoff,'nav']*=10 if i%2==0 else .1;mutated_inputs.append(d)
        after=controls(*mutated_inputs);before=baseline.loc[:cutoff]
        pd.testing.assert_frame_equal(before,after.loc[:cutoff])
        truncated_controls=controls(*[d[d.date<=cutoff] for d in original_inputs])
        pd.testing.assert_frame_equal(before,truncated_controls.loc[:cutoff])
        # premium42(T) explicitly excludes P3/BASE return(T).
        today_changed=p3.copy();today_changed.loc[today_changed.date==cutoff,'nav']*=10
        altered_today=controls(l4,l3,trail,today_changed)
        if baseline.loc[cutoff,'premium42']!=altered_today.loc[cutoff,'premium42']:
            raise ValueError('TRAIL42 today unexpectedly includes today return')
        checks.append(dict(cutoff=day,p3_prefix_equals_truncated=True,p3_future_perturbation_no_effect=True,
                           dd_prefix_equals_truncated=True,dd_future_perturbation_no_effect=True,
                           premium42_excludes_today_return=True))
    orders=pd.read_csv(a.live/'orders.csv',dtype={'code':str})
    fills=pd.read_csv(a.live/'fills.csv',dtype={'code':str})
    post=orders[(orders.signal_date>'2026-09-29')&(orders.carve_out_id.fillna('')=='T0_CARVE_FIN_SAT_SWITCH')]
    if not post.execution_clock.eq('NEXT_SESSION_OPEN').all() or not post.signal_available.eq('AFTER_CLOSE').all():
        raise ValueError('P3 order clock qualification failed')
    new=fills[fills.fill_date>'2026-09-29']
    if not new.fill_date.gt(new.signal_date).all():raise ValueError('Same-day replay execution found')
    summary=dict(status='CONFIRMED_CLOSE_KNOWN_P3_SIGNAL_NEXT_SESSION_EXECUTION',checks=checks,
                 p3_post_seed_orders=len(post),orders_after_close_next_open=True,new_fills=len(new),same_day_fills=0,
                 virtual_same_day_witness=virtual_same_day_witness(),
                 interpretation=['P3 state(T) uses provided parent NAV through T, available after T close for T+1 orders',
                     'TRAIL42 ON(T) uses lag-one 42-observation premium through T-1; DD choice(T) uses virtual NAV through T',
                     'Legacy virtual SC same-day score and research DD same-day return selection are not executable-return proof',
                     'Close-observable synthetic virtual score is not automatically lookahead when only used for next-session decisions'],
                 limits=['Historical input publication/asof vintage not verified by these prefix tests',
                         'No intraday snapshot, quote depth or actual T0 execution validation',
                         'Current T+1 paper result remains limited to observed window and original synthetic control definition'],
                 source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.live/'orders.csv',a.live/'fills.csv',a.runtime/'current.json']})
    pd.DataFrame(checks).to_csv(a.out/'prefix_checks.csv',index=False)
    post.to_csv(a.out/'p3_order_clocks.csv',index=False)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
