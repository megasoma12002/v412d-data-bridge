#!/usr/bin/env python3
"""Read-only whole-lineage data audit. Incomplete evidence must not certify live."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from dd_switch_session_market import HALTS
from twse_session_sources import cached_load_calendar_window
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok
from soft_assist_helpers import LIVE_KD

ROOT=Path(__file__).resolve().parents[1]
CORE=['2880','2886','2892','5880']
END='2026-10-08'
AUDIT_HALTS={**HALTS,'2412':pd.date_range('2010-01-21','2010-02-07').union(pd.date_range('2011-01-07','2011-01-24')),
             '3045':pd.date_range('2011-09-27','2011-10-12'),
             '2884':pd.to_datetime(['2025-11-05'])}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def frame(path):
    data=pd.read_csv(path,dtype={'code':str}).assign(date=lambda x:x.date.astype(str).str[:10])
    if 'code' not in data and path.name=='e10s2_0050_adjusted.csv':data['code']='0050'
    return data

def archive_prices(out):
    rows=[]
    for path in sorted((out/'sources').glob('*_20*.json')):
        # Exact annual price snapshots only. Gap/adjacent responses overlap
        # them and must not multiply joined quote counts.
        suffix=path.stem.rsplit('_',1)
        if len(suffix)!=2 or len(suffix[1])!=4 or not suffix[1].isdigit():continue
        payload=json.loads(path.read_text())
        if payload.get('status')!=200: continue
        for r in payload.get('data',[]):
            rows.append(dict(date=r['date'],code=str(r['stock_id']),open=r['open'],high=r['max'],low=r['min'],close=r['close'],volume=r['Trading_Volume']))
    result=pd.DataFrame(rows)
    if len(result) and result.duplicated(['date','code']).any():
        raise ValueError('Duplicate archived annual price evidence')
    return result

def audit_quotes(name, data, benchmark, fresh, out):
    start,end=data.date.min(),min(data.date.max(),END)
    duplicates=data[data.duplicated(['date','code'],keep=False)].copy()
    issues=[];coverage=[]
    for code,g in data.groupby('code'):
        first,last=g.date.min(),g.date.max()
        # Crop to this artifact's lifespan. Separate tail gaps below.
        expected={d for d in benchmark if max(start,first)<=d<=end}
        have=set(g.date)
        missing=sorted(expected-have)
        for day in missing:
            issue='EXPECTED_KNOWN_HALT_NO_QUOTE' if code in AUDIT_HALTS and pd.Timestamp(day) in AUDIT_HALTS[code] else 'MISSING_BENCHMARK_DATE'
            issues.append(dict(dataset=name,code=code,date=day,issue=issue))
        coverage.append(dict(dataset=name,code=code,start=first,end=last,rows=len(g),benchmark_expected=len(expected),missing=len(missing),last_date_before_panel_end=last<end))
    if 'tradable' in data:
        eligible=data.tradable.astype(str).str.lower().eq('true')
    else:eligible=pd.Series(True,index=data.index)
    # Reconstruct raw private OHLC from the explicitly stored adjustment factor.
    check=data.copy()
    if 'adjusted_close' in check and 'close' not in check:
        factor='backward_adjustment_factor' if 'backward_adjustment_factor' in check else ('factor' if 'factor' in check else None)
        if factor:check['close']=check.adjusted_close/check[factor]
    if 'adjusted_open' in check and 'backward_adjustment_factor' in check:
        for col in ['open','high','low','close']:
            check[col]=check['adjusted_'+col]/check.backward_adjustment_factor
    for col in ['open','high','low','close']:
        if col not in check:continue
        numeric=pd.to_numeric(check[col],errors='coerce')
        bad=eligible & (~np.isfinite(numeric) | (numeric<=0))
        for r in check.loc[bad,['date','code']].itertuples(index=False):issues.append(dict(dataset=name,date=r.date,code=r.code,issue='INVALID_'+col.upper()))
    if all(c in check for c in ['open','high','low','close']):
        bad=eligible & ((check.high+1e-6<check[['open','close']].max(axis=1))|(check.low-1e-6>check[['open','close']].min(axis=1))|(check.high<check.low))
        for r in check.loc[bad,['date','code']].itertuples(index=False):issues.append(dict(dataset=name,date=r.date,code=r.code,issue='OHLC_ORDER'))
    jumps=[]
    if 'close' in check:
        for code,g in check.groupby('code'):
            g=g.sort_values('date');changes=pd.to_numeric(g.close,errors='coerce').pct_change()
            for i in changes[changes.abs()>.35].index:
                jumps.append(dict(dataset=name,code=code,date=check.loc[i,'date'],raw_return=float(changes.loc[i]),issue='REVIEW_CORPORATE_ACTION_OR_BAD_QUOTE'))
    comparisons=[]
    if len(fresh) and 'close' in check:
        paired=check.merge(fresh,on=['date','code'],suffixes=('_artifact','_redownload'))
        for col in ['open','high','low','close','volume']:
            if col+'_artifact' not in paired:continue
            a=pd.to_numeric(paired[col+'_artifact'],errors='coerce');b=pd.to_numeric(paired[col+'_redownload'],errors='coerce')
            delta=(a-b).abs();mask=delta>np.maximum(1e-6,b.abs()*1e-9)
            for r in paired.loc[mask].itertuples(index=False):
                comparisons.append(dict(dataset=name,date=r.date,code=r.code,field=col,artifact=float(getattr(r,col+'_artifact')),redownload=float(getattr(r,col+'_redownload'))))
        compared=len(paired)
    else:compared=0
    pd.DataFrame(issues,columns=['dataset','code','date','issue']).to_csv(out/(name+'_issues.csv'),index=False)
    pd.DataFrame(comparisons,columns=['dataset','date','code','field','artifact','redownload']).to_csv(out/(name+'_redownload_differences.csv'),index=False)
    pd.DataFrame(jumps,columns=['dataset','code','date','raw_return','issue']).to_csv(out/(name+'_large_moves.csv'),index=False)
    return dict(rows=len(data),dates=data.date.nunique(),start=start,end=data.date.max(),duplicates=len(duplicates),issues=len(issues),issue_counts=pd.Series([r['issue'] for r in issues],dtype=str).value_counts().to_dict(),redownload_compared_rows=compared,redownload_difference_fields=len(comparisons),redownload_difference_by_field=pd.Series([r['field'] for r in comparisons],dtype=str).value_counts().to_dict(),large_raw_moves=len(jumps),coverage=coverage)

def audit_dividends(out,benchmark):
    path=ROOT/'data/dividend_events/e22_dividend_events.csv';d=pd.read_csv(path,dtype={'code':str}).fillna('')
    raw={}
    for rel in ['data/dividend_events/e22_dividend_raw.json','data/dividend_events/e22_dividend_raw_private.json']:
        raw.update(json.loads((ROOT/rel).read_text()))
    yahoo=json.loads((ROOT/'data/dividend_events/e22_payment_date_yahoo_backfill.json').read_text())
    yahoo_keys={(str(r['code']),r['cash_ex_date'],r['cash_payment_date']) for r in yahoo.get('updates',[])}
    official_path=out/'sources/yuanta_0050_dividends.json'
    official=json.loads(official_path.read_text())['rows'] if official_path.exists() else json.loads((ROOT/'research/ops/yuanta_etf_div_0050.json').read_text())['rows']
    official_by_date={r['cash_ex_date']:r for r in official}
    rows=[]
    for event in d.to_dict('records'):
        for leg in ['cash','stock']:
            amount=float(event[leg+'_dividend'] or 0)
            if amount<=0:continue
            code=event['code'];ex=event[leg+'_ex_date'];pay=event[leg+'_payment_date'];ann=event['announcement_date']
            source='FILLED_LEDGER_NO_ROW_LEVEL_PRIMARY_PAYMENT_PROOF'
            price_amount_match=None;payment_match=None
            if code=='0050' and leg=='cash' and ex in official_by_date:
                ref=official_by_date[ex];price_amount_match=bool(np.isclose(amount,float(ref['cash_dividend']),rtol=0,atol=1e-8));payment_match=pay==ref['cash_payment_date'];source='PRIMARY_YUANTA_HISTORY_CURRENT_SNAPSHOT'
            elif leg=='cash' and (code,ex,pay) in yahoo_keys:source='SECONDARY_YAHOO_PAYMENT_BACKFILL'
            ex_field='CashExDividendTradingDate' if leg=='cash' else 'StockExDividendTradingDate'
            earnings='CashEarningsDistribution' if leg=='cash' else 'StockEarningsDistribution'
            surplus='CashStatutorySurplus' if leg=='cash' else 'StockStatutorySurplus'
            matches=[r for r in raw.get(code,[]) if str(r.get(ex_field,''))[:10]==ex]
            if matches and code!='0050':
                price_amount_match=any(np.isclose(amount,float(r.get(earnings,0) or 0)+float(r.get(surplus,0) or 0),rtol=0,atol=1e-7) for r in matches)
                if leg=='cash' and any(str(r.get('CashDividendPaymentDate',''))[:10]==pay and pay for r in matches):
                    source='SECONDARY_FINMIND_PAYMENT_PRESENT'
            rows.append(dict(code=code,leg=leg,ex_date=ex,payment_date=pay,amount=amount,announcement_date=ann,announcement_time=event['announcement_time'],missing_announcement=not bool(ann),missing_ex=not bool(ex),missing_payment=not bool(pay),pay_before_ex=bool(pay and ex and pay<ex),announcement_after_ex=bool(ann and ex and ann>ex),amount_source_match=price_amount_match,payment_source_match=payment_match,payment_provenance=source,ex_on_verified_benchmark=ex in benchmark if ex in benchmark or (ex[:4] in ['2025','2026']) else None,publication_vintage_certified=False))
    result=pd.DataFrame(rows);result.to_csv(out/'dividend_event_audit.csv',index=False)
    primary=result[result.payment_provenance.eq('PRIMARY_YUANTA_HISTORY_CURRENT_SNAPSHOT')]
    return dict(ledger_rows=len(d),positive_legs=len(result),cash_legs=int(result.leg.eq('cash').sum()),stock_legs=int(result.leg.eq('stock').sum()),missing_announcement_legs=int(result.missing_announcement.sum()),missing_ex=int(result.missing_ex.sum()),missing_payment=int(result.missing_payment.sum()),pay_before_ex=int(result.pay_before_ex.sum()),announcement_after_ex=int(result.announcement_after_ex.sum()),duplicate_legs=int(result.duplicated(['code','leg','ex_date']).sum()),scheduled_ex_on_closed_verified_date=int(result.ex_on_verified_benchmark.eq(False).sum()),provenance=result.payment_provenance.value_counts().to_dict(),amount_source_mismatch=int(result.amount_source_match.eq(False).sum()),official_0050_compared=len(primary),official_0050_mismatches=int((primary.amount_source_match.eq(False)|primary.payment_source_match.eq(False)).sum()),primary_vintage_verified_legs=0)

def feature_availability(market,dividends,out):
    """Actual historical feature functions, full ledger vs known announcements.

    Market always ends at the same cutoff; only future event knowledge changes.
    A discrepancy proves sensitivity, not a causal NAV loss or a deployable fix.
    """
    market=market.copy();market.date=pd.to_datetime(market.date)
    dividends=dividends.copy().fillna('');ann=pd.to_datetime(dividends.announcement_date,errors='coerce')
    cal=pd.DatetimeIndex(sorted(market.date.unique()));rows=[]
    params={k:LIVE_KD[k] for k in ['k_thresh','season_start','season_end','pre_days','active_score']}
    full_kd=build_kd_season_tilt_scores(market,dividends,CORE,**params)
    full_ok=build_pre_exdiv_window_buy_ok(cal,dividends,CORE,pre_days=params['pre_days'],also_stock_ex=True)
    # Every date whose pre-ex mask can use an announcement not yet published.
    future_mask=[]
    for event in dividends[dividends.code.isin(CORE)].to_dict('records'):
        ex=pd.to_datetime(event['cash_ex_date'],errors='coerce');announcement=pd.to_datetime(event['announcement_date'],errors='coerce')
        if pd.isna(ex):continue
        eligible=cal[cal>=ex]
        if not len(eligible):continue
        i=cal.get_loc(eligible[0])
        for day in cal[max(0,i-int(params['pre_days'])):i+1]:
            if pd.isna(announcement) or day<announcement:
                future_mask.append(dict(date=str(day.date()),code=event['code'],ex_date=str(ex.date()),announcement_date=event['announcement_date'],issue='PRE_EX_MASK_BEFORE_ANNOUNCEMENT'))
    pd.DataFrame(future_mask,columns=['date','code','ex_date','announcement_date','issue']).to_csv(out/'pre_ex_announcement_violations.csv',index=False)
    for year in range(2012,2027):
        for month,day in [(4,30),(5,15),(7,1)]:
            cutoff=pd.Timestamp(year,month,day);past=cal[cal<=cutoff]
            if not len(past) or cutoff>cal.max():continue
            t=past[-1];m=market[market.date<=t];known=dividends[ann.notna()&(ann<=t)]
            scores=build_kd_season_tilt_scores(m,known,CORE,**params)
            ok=build_pre_exdiv_window_buy_ok(past,known,CORE,pre_days=params['pre_days'],also_stock_ex=True)
            for code in CORE:
                rows.append(dict(date=str(t.date()),code=code,full_ledger_kd=float(full_kd.loc[t,code]),announcement_prefix_kd=float(scores.loc[t,code]),kd_changed=not np.isclose(full_kd.loc[t,code],scores.loc[t,code]),full_ledger_buy_ok=bool(full_ok.loc[t,code]),announcement_prefix_buy_ok=bool(ok.loc[t,code]),buy_ok_changed=bool(full_ok.loc[t,code])!=bool(ok.loc[t,code])))
    result=pd.DataFrame(rows);result.to_csv(out/'feature_announcement_prefix_audit.csv',index=False)
    return dict(parameters=dict(params),cutoff_dates=result.date.nunique(),name_cutoffs=len(result),kd_changed=int(result.kd_changed.sum()),buy_mask_changed=int(result.buy_ok_changed.sum()),pre_ex_unpublished_name_days=len(future_mask),ex_date_announcement_availability_not_separately_proved=True,method='Same market prefix; remove event rows whose recorded announcement is later than cutoff. Recorded announcement may itself not prove final ex-date was available.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=ROOT/'repro/dd-switch-full-history-audit');args=parser.parse_args();out=args.out.resolve()
    if (ROOT/'repro').resolve() not in out.parents:raise ValueError('Research only')
    out.mkdir(exist_ok=True,parents=True);fresh=archive_prices(out)
    benchmark=set(fresh.loc[fresh.code.eq('TAIEX'),'date']) if len(fresh) else set()
    for year in [2025,2026]:
        sessions,_=cached_load_calendar_window(year)
        benchmark.update(str(d) for d in sessions if str(d).startswith(str(year)) and str(d)<=END)
    pd.DataFrame([dict(date=d,source='PRIMARY_CACHED_TWSE_CALENDAR' if d[:4] in ['2025','2026'] else 'SECONDARY_FINMIND_REDOWNLOAD') for d in sorted(benchmark)]).to_csv(out/'verified_date_benchmark.csv',index=False)
    paths={
        'canonical_market':'forward/e21/live_market.csv',
        'corrected_parents':'repro/dd-switch-seven-session-rebuild/inputs/parents_with_off.csv',
        'corrected_mothers':'repro/dd-switch-seven-session-rebuild/inputs/mothers_with_off.csv',
        'private_fin':'data/market/private_fin_adjusted.csv',
        'telecom_etf_raw':'data/telecom_0050_complete/telecom_0050_2010_latest_ohlcv.csv',
        'telecom_adjusted':'forward/e9/e9_telecom_adjusted.csv',
        'etf_adjusted':'forward/e10s2/e10s2_0050_adjusted.csv',
        'off_actual':'repro/dd-switch-seven-session-rebuild/inputs/00631L_actual.csv'}
    reports={};inventory=[]
    for name,rel in paths.items():
        path=ROOT/rel;data=frame(path)
        # Synthetic prelisting marks are not expected to have raw market evidence.
        if name.startswith('corrected_'):data=data[~data.mark_policy.eq('PRE_LIST_NO_POSITION')]
        report=audit_quotes(name,data,benchmark,fresh,out);reports[name]=report
        inventory.append(dict(dataset=name,path=rel,sha256=sha(path),rows=len(data),start=data.date.min(),end=data.date.max(),available_at_present='available_at' in data,publication_vintage_present='vintage' in data))
        print('QUOTE_AUDITED',name,len(data),report['issues'],flush=True)
    pd.DataFrame(inventory).to_csv(out/'input_inventory.csv',index=False)
    dividends=audit_dividends(out,benchmark)
    features=feature_availability(frame(ROOT/paths['corrected_parents']),pd.read_csv(ROOT/'data/dividend_events/e22_dividend_events.csv',dtype={'code':str}),out)
    navs=[];fills=[];source_cal=set(frame(ROOT/paths['corrected_parents']).date)
    evidence_years=set(fresh[fresh.code=='TAIEX'].date.str[:4])|{'2025','2026'}
    sorted_benchmark=sorted(benchmark)
    import bisect
    clock_rows=[]
    for kind in ['parents','mothers']:
        folder=ROOT/'repro/dd-switch-seven-session-rebuild'/kind
        for path in sorted(folder.glob('nav_*.csv')):
            data=pd.read_csv(path);expected={d for d in benchmark if data.date.min()<=d<=data.date.max()};missing=sorted(expected-set(data.date))
            navs.append(dict(book=path.stem,path=str(path.relative_to(ROOT)),sha256=sha(path),rows=len(data),start=data.date.min(),end=data.date.max(),missing_benchmark_dates=missing,duplicate_dates=int(data.date.duplicated().sum()),invalid_nav=int((~np.isfinite(data.nav)|(data.nav<=0)).sum())))
        for path in sorted(folder.glob('fills_*.csv')):
            data=pd.read_csv(path,dtype={'code':str});same=int((data.fill_date<=data.signal_date).sum());prelist=int(((data.code=='00631L')&(data.fill_date<'2014-10-31')).sum());halt=0
            for code,days in HALTS.items():halt+=int(((data.code==code)&pd.to_datetime(data.fill_date).isin(days)).sum())
            unknown=int((~data.fill_date.isin(source_cal)).sum())
            # Compare only fully evidenced signal-to-fill date intervals.
            exact=delayed=unevidenced=0
            for r in data.itertuples():
                interval=pd.date_range(r.signal_date,r.fill_date,freq='D')
                if any(str(d.year) not in evidence_years for d in interval):unevidenced+=1;continue
                j=bisect.bisect_right(sorted_benchmark,r.signal_date)
                if j>=len(sorted_benchmark):unevidenced+=1
                elif r.fill_date==sorted_benchmark[j]:exact+=1
                else:
                    delayed+=1
                    clock_rows.append(dict(book=path.stem,code=r.code,side=r.side,signal_date=r.signal_date,first_qualified_session=sorted_benchmark[j],fill_date=r.fill_date,issue='LATER_FILL_REQUIRES_ORDER_LIFECYCLE_ATTRIBUTION_NOT_AUTOMATIC_CLOCK_ERROR'))
            fills.append(dict(book=path.stem,rows=len(data),same_or_before_signal=same,prelisting_fills=prelist,halt_fills=halt,fill_outside_market_panel=unknown,next_benchmark_date=exact,later_than_next_benchmark_date=delayed,unevidenced_clock_rows=unevidenced))
    (out/'nav_coverage.json').write_text(json.dumps(navs,indent=2));pd.DataFrame(fills).to_csv(out/'fill_date_audit.csv',index=False)
    pd.DataFrame(clock_rows).to_csv(out/'later_fills_to_attribute.csv',index=False)
    manifest=json.loads((out/'source_manifest.json').read_text());access=json.loads((out/'primary_access.json').read_text()) if (out/'primary_access.json').exists() else []
    blockers=[dict(id='OFFICIAL_PRE2025_CALENDAR',reason='TWSE historical API access denied; provider dates are secondary; complete pre-2025 official calendar still unproved'),dict(id='FULL_RAW_PRICE_EXTERNAL_CONFIRMATION',reason=('Provider quota reached; per-stock full-history re-download incomplete' if any(r['status']!='FETCHED' for r in manifest) else 'All requested annual snapshots obtained and compared; FinMind shares original ancestry, so independent historical primary proof remains incomplete')),dict(id='DIVIDEND_VINTAGE',reason='27 ETF announcements absent and no historical revision/publication archive for all legs'),dict(id='FEATURE_FUTURE_EVENT_DEPENDENCY',reason='Feature functions use full ex-date ledger without announcement availability gate; see actual prefix experiment'),dict(id='FULL_LIVE_FUNDED_HISTORY',reason='Mother DD/TRAIL retain shadow and return stitching; full live historical joint capital execution not certified'),dict(id='HISTORICAL_CORPORATE_ACTION_COMPLETENESS',reason='Two explicit ETF splits and known halts verified; all other historical action completeness needs primary event inventory')]
    enrichment_path=out/'announcement_evidence_summary.json'
    if enrichment_path.exists():
        enrichment=json.loads(enrichment_path.read_text())
        if enrichment.get('ledger_sha256')!=sha(ROOT/'data/dividend_events/e22_dividend_events.csv'):
            raise ValueError('Announcement evidence report is stale; rerun its audit first')
        for blocker in blockers:
            if blocker['id']=='DIVIDEND_VINTAGE':
                blocker['reason']=f"0050 has {enrichment['primary_reported_time_supported_legs']} primary reported schedule/final timestamp matches; {enrichment['remaining_primary_time_legs']} positive legs still lack primary timestamp proof and all revision inventories remain uncertified"
            if blocker['id']=='HISTORICAL_CORPORATE_ACTION_COMPLETENESS':
                blocker['reason']=f"{enrichment['split_contracts_primary_matched']} ETF split/halt/unit contracts have primary reported time proof; {enrichment['zero_dividend_ex_right_candidates']} zero-dividend ex-right rows need action classification, subscription/unit evidence and complete historical primary inventory"
    blockers.extend([dict(id='RESEARCH_GAP_CANDIDATES_NOT_PROMOTED',reason='34 missing quotes recovered in independent research candidates (10 core, 24 private); original canonical inputs intentionally unchanged'),dict(id='HISTORICAL_LATER_ORDER_FILLS',count=len(clock_rows),reason='Evidenced fills occur after first qualified session; funding/residual/stale-order lifecycle attribution pending, not automatically invalid T+1 qualification'),dict(id='SCHEDULED_EX_DATE_ON_CLOSED_SESSION',reason='2891 cash scheduled ex 2026-07-10 falls outside official sessions; effective-date router convention exists but primary schedule/amendment proof still required')])
    summary=dict(status='AUDIT_COMPLETE_FULL_HISTORY_CERTIFICATION_BLOCKED',publication_allowed=False,asof=END,scope='DD_SWITCH parent/mother lineage plus eight private-financial raw-adjusted inputs; not every obsolete research file',benchmark_sessions=len(benchmark),benchmark_years=sorted({d[:4] for d in benchmark}),official_calendar_years=[2025,2026],external_source_counts=pd.Series([r['status'] for r in manifest]).value_counts().to_dict(),primary_access=access,quotes=reports,dividends=dividends,feature_availability=features,navs=navs,fills=fills,blockers=blockers,limits=['A FinMind re-download shares ancestry with original FinMind prices: consistency evidence, not independent cross-provider proof','TAIEX archived panel is CLOSE_ONLY_PROXY: historical open/high/low equal close and volume=0; close consistency is reported separately; proxy OHLC/volume must not support intraday claims','Dates before each artifact start and after cutoff are excluded; prelisting synthetic marks never counted as tradable quotes','Price integrity and ledger arithmetic do not prove point-in-time availability or execution depth','Next-session qualification is not a guarantee of next-session fill: later paper fills need funding/order lifecycle attribution','Nothing writes canonical data, runtime or broker state'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'blockers.json').write_text(json.dumps(blockers,indent=2))
    hashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/v for v in paths.values()]+[ROOT/'data/dividend_events/e22_dividend_events.csv',ROOT/'scripts/within_sleeve_alloc.py',Path(__file__),ROOT/'scripts/dd_switch_full_history_sources.py']}
    (out/'audited_input_sha256.json').write_text(json.dumps(hashes,indent=2));print('FULL_HISTORY_AUDIT_COMPLETE',json.dumps(dict(benchmark_sessions=len(benchmark),dividends=dividends,features=features)),flush=True)

if __name__=='__main__':main()
