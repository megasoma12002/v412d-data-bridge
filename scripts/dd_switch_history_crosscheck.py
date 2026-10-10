#!/usr/bin/env python3
"""Test alternate source unit hypotheses and recover separately checked gaps.

Yahoo OHLC has inconsistent historical split/rights adjustments. Multiplying
split events is a hypothesis, not a certified raw-price conversion. Differences
must not be reported as proven errors in the local source. Dividends do not enter
the tested conversion. Volume definitions differ and are not synthesized.
No canonical writes; no point-in-time or full official-history certification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from dd_switch_full_history_sources import ROOT,CODES
from dd_switch_session_market import SPLITS
from twse_session_sources import cached_load_calendar_window

def yahoo_frame(out,code):
    path=out/'sources'/('yahoo_'+code+'.json');obj=json.loads(path.read_text())['chart']['result'][0]
    q=pd.DataFrame(obj['indicators']['quote'][0]);q['date']=pd.to_datetime(obj['timestamp'],unit='s',utc=True).tz_convert('Asia/Taipei').strftime('%Y-%m-%d');q['code']=code
    events=[]
    for event in obj.get('events',{}).get('splits',{}).values():
        day=pd.to_datetime(event['date'],unit='s',utc=True).tz_convert('Asia/Taipei').strftime('%Y-%m-%d');ratio=float(event['numerator'])/float(event['denominator']);events.append(dict(code=code,date=day,factor=ratio,source='YAHOO_SPLIT_EVENT'))
    # Test official ETF ratios; Yahoo does not consistently apply them to all
    # historical periods. The resulting series is diagnostic, not executable.
    for day,changes in SPLITS.items():
        if code in changes and not any(e['date']==day for e in events):events.append(dict(code=code,date=day,factor=changes[code],source='VERIFIED_OFFICIAL_ETF_SPLIT_CONTRACT'))
    factor=pd.Series(1.,index=q.index)
    for event in events:factor.loc[q.date<event['date']]*=event['factor']
    q['raw_unit_conversion']=factor
    for col in ['open','high','low','close']:q[col+'_provider']=q[col];q[col]*=factor
    # Provider volume is retained as received, not asserted equal to FinMind.
    q['volume_source']='YAHOO_REPORTED_VOLUME_NOT_UNIT_NORMALIZED'
    return q,events

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-full-history-audit');args=parser.parse_args();out=args.out.resolve()
    if (ROOT/'repro').resolve() not in out.parents:raise ValueError('Research only')
    records=[];splits=[];all_rows=[]
    for code in CODES:
        if not (out/'sources'/('yahoo_'+code+'.json')).exists():continue
        q,events=yahoo_frame(out,code);all_rows.append(q);splits.extend(events)
    fresh=pd.concat(all_rows,ignore_index=True)
    destination=out/'alternate_normalized_prices.csv.gz'
    fresh.to_csv(destination,index=False,compression='gzip')
    persisted=pd.read_csv(destination,dtype={'code':str})
    if len(persisted)!=len(fresh) or set(persisted.code)!=set(fresh.code):
        raise ValueError('Incomplete persisted alternate price diagnostic')
    pd.DataFrame(splits).to_csv(out/'alternate_unit_events.csv',index=False)
    idx=fresh[(fresh.code=='TAIEX')&fresh.close.notna()&(fresh.close>0)];dates=set(idx.date)
    official=[]
    for year in [2025,2026]:
        cal,_=cached_load_calendar_window(year);expected={str(d) for d in cal if str(d).startswith(str(year)) and str(d)<='2026-10-08'}
        observed={d for d in dates if d.startswith(str(year))};official.append(dict(year=year,missing_in_yahoo=sorted(expected-observed),extra_in_yahoo=sorted(observed-expected)))
    core=pd.read_csv(ROOT/'repro/dd-switch-seven-session-rebuild/inputs/parents_with_off.csv',dtype={'code':str});private=pd.read_csv(ROOT/'data/market/private_fin_adjusted.csv',dtype={'code':str})
    local=private[['date','code','volume','raw_close']].rename(columns={'raw_close':'close'}).copy()
    for col in ['open','high','low']:local[col]=private['adjusted_'+col]/private.backward_adjustment_factor
    mismatches=[];provider_missing=[]
    for name,data in [('core',core[core.tradable & ~core.code.eq('TAIEX')]),('private',local),('index_close',core[core.code=='TAIEX'])]:
        paired=data.merge(fresh,on=['date','code'],suffixes=('_local','_alternate'),how='left')
        cols=['close'] if name=='index_close' else ['open','high','low','close']
        for r in paired[paired.close_alternate.isna()][['date','code']].itertuples(index=False):provider_missing.append(dict(dataset=name,date=r.date,code=r.code,issue='ALTERNATE_SOURCE_HAS_NO_QUOTE_NOT_A_LOCAL_MISSING_ROW'))
        tested=paired[paired.close_alternate.notna()].copy();field_counts={};max_error={}
        for col in cols:
            a=pd.to_numeric(tested[col+'_local'],errors='coerce');b=pd.to_numeric(tested[col+'_alternate'],errors='coerce');delta=(a-b).abs()
            # Yahoo quote arrays carry float32 and rounded split multipliers.
            # Half the minimum TW equity tick; index precision uses same 0.005.
            mask=delta>.005;field_counts[col]=int(mask.sum());max_error[col]=float(delta.max())
            for row in tested.loc[mask].itertuples(index=False):mismatches.append(dict(dataset=name,date=row.date,code=row.code,field=col,local=float(getattr(row,col+'_local')),alternate=float(getattr(row,col+'_alternate')),difference=float(getattr(row,col+'_local')-getattr(row,col+'_alternate'))))
        by_code=[]
        for code,g in paired.groupby('code'):
            expected={d for d in dates if g.date.min()<=d<=g.date.max()};have=set(g.date);missing=sorted(expected-have)
            by_code.append(dict(code=code,rows=len(g),missing_benchmark_dates=missing,alternate_missing_quotes=int(g.close_alternate.isna().sum())))
        records.append(dict(dataset=name,paired=len(paired),compared_rows=len(tested),differences=field_counts,max_absolute_difference=max_error,coverage=by_code))
    pd.DataFrame(mismatches,columns=['dataset','date','code','field','local','alternate','difference']).to_csv(out/'alternate_price_differences.csv',index=False)
    pd.DataFrame(provider_missing).to_csv(out/'alternate_provider_missing_quotes.csv',index=False)
    # Recover 16 private-financial dates in a research copy only. Both adjacent
    # local raw OHLC must agree with normalized alternate prices, and original
    # adjustment factor must stay constant across each gap.
    additions=[];gap_checks=[]
    for code in sorted(private.code.unique()):
        sub=private[private.code==code].sort_values('date');p=sub.set_index('date');q=fresh[fresh.code==code].set_index('date')
        for day in ['2025-02-06','2026-05-28']:
            if day in p.index:continue
            before=p[p.index<day].iloc[-1];after=p[p.index>day].iloc[0];bd=p[p.index<day].index[-1];ad=p[p.index>day].index[0]
            if day not in q.index or pd.isna(q.loc[day,'close']):raise ValueError('No alternate gap quote '+code+' '+day)
            fa=float(before.backward_adjustment_factor);fb=float(after.backward_adjustment_factor)
            if not np.isclose(fa,fb,rtol=1e-10,atol=1e-12):raise ValueError('Adjustment changed inside gap '+code+' '+day)
            errors=[]
            for date,row in [(bd,before),(ad,after)]:
                for col in ['open','high','low','close']:
                    original=float(row['adjusted_'+col])/float(row.backward_adjustment_factor)
                    errors.append(abs(original-float(q.loc[date,col])))
            if max(errors)>.005:raise ValueError('Alternate adjacent quote mismatch '+code+' '+day+' '+str(max(errors)))
            row=q.loc[day];addition=dict(code=code,date=day,volume=float(row.volume),backward_adjustment_factor=fa,raw_close=float(row.close))
            for col in ['open','high','low','close']:addition['adjusted_'+col]=float(row[col])*fa
            additions.append(addition);gap_checks.append(dict(code=code,date=day,before=bd,after=ad,max_adjacent_raw_ohlc_difference=max(errors),adjustment_factor=fa,raw_unit_conversion=float(row.raw_unit_conversion),source='SECONDARY_YAHOO_EXPLICIT_SHARE_UNIT_CONVERSION',volume_comparable_to_original=False,publication_allowed=False))
    repaired=pd.concat([private,pd.DataFrame(additions)],ignore_index=True).sort_values(['code','date']);repaired.to_csv(out/'private_fin_repaired_research.csv',index=False);pd.DataFrame(additions).to_csv(out/'private_fin_recovered_16.csv',index=False);pd.DataFrame(gap_checks).to_csv(out/'private_fin_recovery_checks.csv',index=False)
    if repaired.duplicated(['code','date']).any():raise ValueError('Duplicate repaired private quote')
    pd.DataFrame([dict(date=d,source='SECONDARY_YAHOO_TAIEX_VALID_CLOSE') for d in sorted(dates)]).to_csv(out/'alternate_full_history_dates.csv',index=False)
    # Official one-day anchor, explicitly not a historical quote archive.
    primary=json.loads((out/'sources/twse_latest_stock_day_all.json').read_text());primary_rows=[]
    for row in primary:
        code=row['Code']
        if code not in CODES:continue
        raw=str(row['Date']);day=f'{int(raw[:3])+1911:04d}-{raw[3:5]}-{raw[5:7]}'
        own=(local if code in set(private.code) else core);hit=own[(own.code==code)&(own.date==day)]
        if hit.empty:continue
        original=hit.iloc[0]
        for col,field in [('open','OpeningPrice'),('high','HighestPrice'),('low','LowestPrice'),('close','ClosingPrice')]:
            try:value=float(row[field].replace(',',''))
            except ValueError:continue
            primary_rows.append(dict(date=day,code=code,field=col,local=float(original[col]),official=value,absolute_difference=abs(float(original[col])-value)))
    anchor=pd.DataFrame(primary_rows);anchor.to_csv(out/'official_latest_quote_check.csv',index=False)
    result=dict(status='ALTERNATE_HISTORY_CROSSCHECK_COMPLETE_RESEARCH_ONLY',publication_allowed=False,source='Yahoo OHLC converted using disclosed split events plus two official ETF events; current-vintage',valid_index_sessions=len(dates),official_calendar_comparison=official,quotes=records,price_difference_fields=len(mismatches),alternate_missing_quote_rows=len(provider_missing),recovered_private_quotes=len(additions),max_recovery_adjacent_difference=max((r['max_adjacent_raw_ohlc_difference'] for r in gap_checks),default=0),official_latest_anchor_fields=len(anchor),official_latest_anchor_max_difference=float(anchor.absolute_difference.max()),limits=['Full official historical calendar/settlement evidence not obtained','Yahoo index dates need cross-check; neither provider is a publication-vintage archive','Yahoo volume differs from FinMind; volume-dependent signals need a separate volume contract','A recovered research quote is not a canonical live input cutover','PIT feature and historical pending-order findings remain unresolved'])
    result['source']='Yahoo current-vintage OHLC under split-only conversion hypothesis; historical units NOT certified'
    result['price_difference_interpretation']='Unresolved unit/source differences, NOT confirmed local bad-price fields'
    result['limits'].append('ETF history has mixed split units; financial rights adjustments need separate evidence')
    (out/'alternate_crosscheck_summary.json').write_text(json.dumps(result,indent=2));print('ALTERNATE_CROSSCHECK_COMPLETE',json.dumps({k:v for k,v in result.items() if k!='quotes'}),flush=True)

if __name__=='__main__':main()
