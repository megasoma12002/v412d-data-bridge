#!/usr/bin/env python3
"""Verify newly fetched raw gap quotes against adjacent archived raw prices."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from dd_switch_full_history_sources import ROOT

OUT=ROOT/'repro/dd-switch-full-history-audit'

def main():
    manifest=json.loads((OUT/'gap_source_manifest.json').read_text())
    if any(r['status']!='FETCHED' for r in manifest):raise ValueError('Gap download incomplete')
    raw=[]
    for rec in manifest:
        for r in json.loads((ROOT/rec['path']).read_text())['data']:
            raw.append(dict(date=r['date'],code=str(r['stock_id']),open=r['open'],high=r['max'],low=r['min'],close=r['close'],volume=r['Trading_Volume'],source_path=rec['path']))
    source=pd.DataFrame(raw)
    if source.duplicated(['date','code']).any():raise ValueError('Duplicate gap source quote')
    core=pd.read_csv(ROOT/'repro/dd-switch-seven-session-rebuild/inputs/parents_with_off.csv',dtype={'code':str})
    private=pd.read_csv(ROOT/'data/market/private_fin_adjusted.csv',dtype={'code':str})
    tests=[];patches=[];private_add=[];core_add=[]
    for dataset,market in [('core',core),('private',private)]:
        for code,original in market.groupby('code'):
            days=['2023-05-25'] if dataset=='core' else ['2023-05-25','2025-02-06','2026-05-28']
            original=original.sort_values('date').set_index('date')
            q=source[source.code.eq(code)].set_index('date')
            for day in days:
                if day in original.index:continue
                if day not in q.index:raise ValueError('Missing raw gap quote '+code+' '+day)
                bd=original[original.index<day].index[-1];ad=original[original.index>day].index[0]
                errors=[]
                for neighbor in [bd,ad]:
                    if neighbor not in q.index:raise ValueError('No raw adjacent proof '+code+' '+neighbor)
                    r=original.loc[neighbor]
                    for field in (['close'] if code=='TAIEX' else ['open','high','low','close']):
                        local=float(r['adjusted_'+field])/float(r.backward_adjustment_factor) if dataset=='private' else float(r[field])
                        errors.append(abs(local-float(q.loc[neighbor,field])))
                if max(errors)>.00001:raise ValueError('Raw adjacent mismatch '+code+' '+day+' '+str(max(errors)))
                r=q.loc[day]
                if not (0<float(r.low)<=min(r.open,r.close)<=max(r.open,r.close)<=r.high):raise ValueError('Invalid OHLC')
                factor=None
                if dataset=='core':
                    before=original.loc[bd];after=original.loc[ad]
                    fa=float(before.adj_close)/float(before.close);fb=float(after.adj_close)/float(after.close)
                    if not np.isclose(fa,fb,rtol=1e-10,atol=1e-12):raise ValueError('Core adjustment changed across gap')
                    if before.unit_multiplier!=after.unit_multiplier:raise ValueError('Core share unit changed across gap')
                    factor=fa
                    addition=before.to_dict();addition.update(date=day,code=code,adj_close=float(r.close)*fa)
                    for col in ['open','high','low','close','volume']:addition[col]=float(r[col])
                    # Preserve the original benchmark-only close-proxy contract;
                    # actual source index OHLC remains in the separate evidence.
                    if code=='TAIEX':
                        for col in ['open','high','low']:addition[col]=float(r.close)
                        addition['volume']=0.
                    core_add.append(addition)
                if dataset=='private':
                    fa=float(original.loc[bd].backward_adjustment_factor);fb=float(original.loc[ad].backward_adjustment_factor)
                    if not np.isclose(fa,fb,rtol=1e-10,atol=1e-12):raise ValueError('Adjustment changed across gap')
                    factor=fa
                    addition=dict(code=code,date=day,volume=float(r.volume),backward_adjustment_factor=fa,raw_close=float(r.close))
                    for col in ['open','high','low','close']:addition['adjusted_'+col]=float(r[col])*fa
                    private_add.append(addition)
                patches.append(dict(dataset=dataset,code=code,date=day,**{k:float(r[k]) for k in ['open','high','low','close','volume']},source_path=r.source_path,publication_allowed=False))
                tests.append(dict(dataset=dataset,code=code,date=day,before=bd,after=ad,max_adjacent_raw_ohlc_difference=max(errors),adjustment_factor=factor,status='ADJACENT_RAW_PRICE_CHECK_PASS',volume_source='FINMIND_TRADING_VOLUME_SAME_FIELD_AS_ARCHIVED_SOURCE',publication_allowed=False))
    pd.DataFrame(patches).to_csv(OUT/'finmind_verified_gap_quotes.csv',index=False)
    pd.DataFrame(tests).to_csv(OUT/'finmind_gap_adjacent_checks.csv',index=False)
    candidate=pd.concat([private,pd.DataFrame(private_add)],ignore_index=True).sort_values(['code','date'])
    if candidate.duplicated(['code','date']).any():raise ValueError('Duplicate private candidate')
    candidate.to_csv(OUT/'private_fin_finmind_repaired_candidate.csv.gz',index=False,compression='gzip')
    if len(pd.read_csv(OUT/'private_fin_finmind_repaired_candidate.csv.gz'))!=len(candidate):raise ValueError('Incomplete persisted private candidate')
    core_candidate=pd.concat([core,pd.DataFrame(core_add)],ignore_index=True).sort_values(['date','code'])
    if core_candidate.duplicated(['date','code']).any():raise ValueError('Duplicate core candidate')
    core_candidate.to_csv(OUT/'core_finmind_repaired_candidate.csv.gz',index=False,compression='gzip')
    persisted=pd.read_csv(OUT/'core_finmind_repaired_candidate.csv.gz',dtype={'code':str})
    if len(persisted)!=len(core_candidate) or len(persisted[persisted.date=='2023-05-25'])!=len(core_add):raise ValueError('Incomplete persisted core candidate')
    # Existing rows must be byte-value equivalent after the pandas round trip,
    # apart from floating-point serialization precision.
    old=persisted[persisted.date!='2023-05-25'].sort_values(['date','code']).reset_index(drop=True)
    pd.testing.assert_frame_equal(old,core.sort_values(['date','code']).reset_index(drop=True),check_dtype=False,rtol=1e-12,atol=1e-10)
    result=dict(status='RAW_GAP_VERIFICATION_PASS_RESEARCH_ONLY',quotes=len(patches),core_gap_quotes=len(core_add),private_gap_quotes=len(private_add),max_adjacent_price_difference=max(r['max_adjacent_raw_ohlc_difference'] for r in tests),private_candidate_rows=len(candidate),core_candidate_rows=len(core_candidate),core_adjustment_contract='unchanged adjacent stored factors; no source price fitted to the book',existing_core_rows_unchanged=True,backtest_ready=False,publication_allowed=False,canonical_inputs_modified=False,limits=['Current-vintage secondary source; not full primary historical certification','Research input candidates only; parent/mother signals not rebuilt','Dividend PIT and old historical price discrepancies remain open'])
    (OUT/'gap_recovery_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
