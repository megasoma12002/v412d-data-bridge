#!/usr/bin/env python3
"""Package original lineage reproduction and assert production CSV gate parity."""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd
import live_tipsoft_dd_switch as gate
from dd_switch_gap_attribution import mother_features
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--prefix',type=Path,required=True)
    parser.add_argument('--parents',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();p=args.source;out=args.out;out.mkdir(parents=True,exist_ok=False)
    controls=pd.read_csv(p/'original_controls.csv',parse_dates=['date']).set_index('date')
    want=gate.want_trail_series(l4_nav_path=p/'nav_L4.csv',trail_nav_path=p/'nav_TRAIL.csv')
    on=gate.trail42_on_series(l3_nav_path=p/'nav_BASE.csv',p3_nav_path=p/'nav_P3.csv')
    active=gate.path3_active_series(want,on)
    if not active.index.equals(controls.index) or not active.eq(controls.active).all() or not want.eq(controls.want_trail).all():
        raise ValueError('Serialized production gate differs from reconstruction')
    old,_=mother_features(gate.DEFAULT_L4_NAV,gate.DEFAULT_TRAIL_NAV,gate.LIVESTACK_L3,gate.LIVESTACK_P3)
    common=old.index.intersection(active.index)
    parity={'want_trail':int(old.want_trail.loc[common].ne(want.loc[common]).sum()),
            'trail_on':int(old.trail_on.loc[common].ne(on.loc[common]).sum()),
            'active':int(old.active.loc[common].ne(active.loc[common]).sum())}
    if any(parity.values()):raise ValueError('Original prefix gate decisions changed: '+str(parity))
    controls.to_csv(out/'controls_all_dates.csv');controls.loc['2026-09-29':].to_csv(out/'gate_decisions_0929_1008.csv')
    frames=[]
    for name in ['BASE','P3','L4','SC_WITHIN','SC_TRAIL42_CASH','TRAIL','DD_SWITCH']:
        n=pd.read_csv(p/('nav_'+name+'.csv'),parse_dates=['date'])
        if name in ['BASE','P3']:
            n[['date','nav','cash','receivables','gross_equity']].to_csv(out/('book_'+name+'.csv'),index=False)
        frames.append(n.set_index('date').nav.rename(name))
    pd.concat(frames,axis=1).to_csv(out/'all_mother_navs.csv')
    cert=json.loads((args.prefix/'summary.json').read_text())
    ext=json.loads((p/'summary.json').read_text())
    parents=json.loads((args.parents/'summary.json').read_text())
    for source in [cert,ext,parents]:
        if not all(v['pass_parity'] for v in source['parity'].values()):raise ValueError('Prefix parity failed')
    for name,data in [('prefix_parity',cert),('extension_parity',ext),('parent_parity',parents)]:
        (out/(name+'.json')).write_text(json.dumps(data,indent=2))
    for name in ['BASE','P3']:
        for kind in ['shares','fills']:
            d=pd.read_csv(p/(kind+'_'+name+'.csv'),dtype={'code':str})
            d[d['fill_date' if kind=='fills' else 'date']>='2026-08-24'].to_csv(out/(kind+'_'+name+'_recent.csv'),index=False)
    summary={'status':'ORIGINAL_RESEARCH_PREFIX_REPRODUCED_AND_APPEND_ONLY_EXTENDED',
        'cutoff':'2026-09-29','extended_through':ext['cutoff'],'production_gate_formula_match':True,
        'prefix_gate_disagreement':parity,'parent_max_share_difference':0.0,
        'mother_max_relative_error':max(v['max_relative_error'] for v in cert['parity'].values()),
        'sessions_after_cutoff':len(controls.loc['2026-09-30':]),
        'path3_off_sessions_after_cutoff':int((~controls.loc['2026-09-30':].active).sum()),
        'last_decision':controls.iloc[-1].to_dict(),
        'construction_refs':{'live_stack':ext['input_ref'],'upper_layers':ext['upper_input_ref'],'parent_ledgers':parents['input_ref']},
        'program_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in
            [ROOT/'scripts/dd_switch_original_reproduction.py',ROOT/'scripts/dd_switch_original_parents.py',Path(__file__).resolve()]},
        'limits':['Legacy same-day DD selector and return stitching retained; not causal live alpha validation',
            'Historical date gaps and corporate actions preserved for parity; corrections require separate version',
            'BASE/P3 and COMP/SAT are share/cash books; TRAIL/DD are stitched return series, not jointly funded books',
            'Path3 active means no DD gate-triggered FIN/TEL flatten; within-sleeve rebalancing still applies',
            'No runtime publication, deployment, broker action or original forward rewrite']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
