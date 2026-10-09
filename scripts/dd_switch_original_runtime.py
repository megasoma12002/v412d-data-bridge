#!/usr/bin/env python3
"""Package verified original-lineage inputs for isolated production T+1 replay.

This does not promote legacy research assumptions into canonical runtime.
"""
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from live_path3_t0_switch_emitter import build_sat_lead_signal,BOOK_COMP,BOOK_SAT
from dd_switch_original_reproduction import normalize_signal
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lineage',type=Path,required=True)
    p.add_argument('--parents',type=Path,required=True)
    p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve()
    if (ROOT/'repro').resolve() not in out.parents:raise ValueError('isolated repro runtime required')
    audit=json.loads((a.audit/'summary.json').read_text())
    if audit['status']!='ORIGINAL_RESEARCH_PREFIX_REPRODUCED_AND_APPEND_ONLY_EXTENDED' or any(audit['prefix_gate_disagreement'].values()):
        raise ValueError('Verified original prefix required')
    for source in [a.lineage,a.parents]:
        s=json.loads((source/'summary.json').read_text())
        if not all(v['pass_parity'] for v in s['parity'].values()):raise ValueError('Source parity failed')
    asof=audit['extended_through'];generation=out/'generations/original-lineage'
    generation.mkdir(parents=True,exist_ok=False)
    sources={'off':a.parents/'off_append_only.csv','base':a.lineage/'nav_BASE.csv',
             'l4':a.lineage/'nav_L4.csv','trail':a.lineage/'nav_TRAIL.csv','dd':a.lineage/'nav_DD_SWITCH.csv'}
    for book in [BOOK_COMP,BOOK_SAT]:sources['shares_'+book]=a.parents/'outputs'/('daily_shares_'+book+'.csv')
    files={};hashes={};source_hashes={}
    for key,source in sources.items():
        frame=pd.read_csv(source,dtype={'code':str})
        if str(frame.date.max())[:10]!=asof:raise ValueError('Source tip mismatch: '+key)
        name=key+'.csv';(generation/name).write_bytes(source.read_bytes())
        files[key]=name;hashes[key]=hashlib.sha256((generation/name).read_bytes()).hexdigest()
        source_hashes[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
    comp=pd.read_csv(a.parents/('nav_'+BOOK_COMP+'.csv'),parse_dates=['date'])
    sat=pd.read_csv(a.parents/('nav_'+BOOK_SAT+'.csv'),parse_dates=['date'])
    signal=build_sat_lead_signal(comp=comp,sat=sat)
    historic_path=ROOT/'repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_signal.csv'
    historic=normalize_signal(pd.read_csv(historic_path,parse_dates=['date']))
    signal=pd.concat([historic[historic.date<='2026-09-29'],signal[signal.date>'2026-09-29']],ignore_index=True)
    signal.to_csv(generation/'signal.csv',index=False);files['signal']='signal.csv'
    hashes['signal']=hashlib.sha256((generation/'signal.csv').read_bytes()).hexdigest()
    meta={'version':'DD_SWITCH_ORIGINAL_LINEAGE_T1_RESEARCH','controller_model_scope':'VERIFIED_ORIGINAL_RESEARCH_LINEAGE_ISOLATED_ONLY',
          'asof':asof,'generation':'generations/original-lineage','files':files,'hashes':hashes,
          'clock':'CLOSE_T_TO_NEXT_SESSION_OPEN','original_research_preserved':True,
          'source_hashes':source_hashes,'audit_sha256':hashlib.sha256((a.audit/'summary.json').read_bytes()).hexdigest()}
    (out/'current.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({'runtime':str(out),'asof':asof,'files':len(files)},indent=2))
if __name__=='__main__':main()
