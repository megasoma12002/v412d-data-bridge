#!/usr/bin/env python3
"""Read-only reconciliation of alternative-source dates and price-unit evidence.

Writes research diagnostics only. Never chooses executable prices by fitting
them to the local book, and never labels a secondary calendar official.
"""
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'

EVIDENCE = {
    '2014-07-23': {
        'status': 'ALTERNATE_NONTRADING_ROW_REPORTED_TWSE_CLOSURE',
        'source_class': 'CONTEMPORANEOUS_DIRECT_NEWS_REPORT_NOT_EXCHANGE_ARCHIVE',
        'url': 'https://m.cnyes.com/news/id/1255061',
        'action': 'DO_NOT_ADD_AS_TRADING_SESSION'},
    '2016-07-08': {
        'status': 'ALTERNATE_NONTRADING_ROW_REPORTED_TWSE_CLOSURE',
        'source_class': 'CNA_CONTEMPORANEOUS_REPORT_YAHOO_HOST_NOT_EXCHANGE_ARCHIVE',
        'url': 'https://tw.stock.yahoo.com/news/颱風尼伯特來襲-股匯期8日休市-120746889.html',
        'action': 'DO_NOT_ADD_AS_TRADING_SESSION'},
    '2023-05-25': {
        'status': 'LOCAL_MISSING_SESSION_NEWS_AND_ALTERNATE_INDEX_AGREE',
        'source_class': 'CONTEMPORANEOUS_DIRECT_MARKET_NEWS_REPORT_NOT_EXCHANGE_ARCHIVE',
        'url': 'https://anuenews.cnyes.com/news/id/5191203',
        'action': 'OBTAIN_RAW_QUOTES_AND_UNIT_CONTRACT_BEFORE_REBUILD'},
}

def main():
    extra = OUT/'calendar_conflict_additional_evidence.json'
    if extra.exists():
        EVIDENCE.update(json.loads(extra.read_text()))
    hashes = json.loads((OUT/'audited_input_sha256.json').read_text())
    immutable = {p: h for p, h in hashes.items()
                 if not p.startswith(('scripts/', 'repro/dd-switch-full-history-audit/'))}
    for p, expected in immutable.items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != expected:
            raise ValueError('Audited input changed: '+p)
    core = pd.read_csv(ROOT/'repro/dd-switch-seven-session-rebuild/inputs/parents_with_off.csv', dtype={'code': str})
    fresh = pd.read_csv(OUT/'alternate_normalized_prices.csv.gz', dtype={'code': str})
    from dd_switch_full_history_sources import CODES
    if set(fresh.code)!=set(CODES):
        raise ValueError('Incomplete persisted alternate source universe')
    idx = fresh[(fresh.code=='TAIEX') & fresh.close.notna() & (fresh.close>0)].sort_values('date')
    observed = set(idx.date)
    original = set(core[core.code=='TAIEX'].date)
    observed = {d for d in observed if min(original)<=d<=max(original)}
    conflicts = []
    for day in sorted(observed ^ original):
        record = dict(date=day, local_present=day in original, alternate_present=day in observed)
        record.update(EVIDENCE.get(day, dict(status='UNRESOLVED_CALENDAR_CONFLICT', source_class='NO_PRIMARY_DECISION', url='', action='RETAIN_LOCAL_PENDING_PRIMARY_PROOF')))
        reported = record.get('reported_index_close')
        if reported is not None and day in original:
            local_close = float(core[(core.code=='TAIEX') & (core.date==day)].iloc[0].close)
            record['reported_close_difference'] = abs(local_close-reported)
            if record['reported_close_difference']>.005:
                raise ValueError('Contemporaneous index close mismatch: '+day)
        if record['status']=='ALTERNATE_NONTRADING_ROW_REPORTED_TWSE_CLOSURE':
            at = idx[idx.date==day].iloc[0]
            prior = idx[idx.date<day].iloc[-1]
            fields = ['open_provider','high_provider','low_provider','close_provider','volume']
            record['alternate_identical_to_previous_row'] = bool(all(at[c]==prior[c] for c in fields))
        conflicts.append(record)
    pd.DataFrame(conflicts).to_csv(OUT/'calendar_conflict_reconciliation.csv', index=False)
    candidates = fresh[fresh.date=='2023-05-25'].copy()
    candidates['price_status'] = 'SECONDARY_UNIT_HYPOTHESIS_NOT_EXECUTABLE'
    candidates['publication_allowed'] = False
    candidates.to_csv(OUT/'missing_20230525_source_candidates.csv', index=False)
    differences = pd.read_csv(OUT/'alternate_price_differences.csv', dtype={'code':str})
    differences['year'] = differences.date.str[:4]
    grouped = differences.groupby(['dataset','code','year']).agg(differing_fields=('field','size'), affected_dates=('date','nunique'), max_absolute_difference=('difference',lambda x:x.abs().max())).reset_index()
    grouped['interpretation'] = 'UNRESOLVED_PRICE_UNIT_OR_SOURCE_DIFFERENCE_NOT_PROVEN_LOCAL_ERROR'
    grouped.to_csv(OUT/'price_unit_unresolved_by_year.csv', index=False)
    # ETF source units demonstrably vary: provider/raw comparison is diagnostic
    # only. Neither representation is silently selected as executable history.
    pairs = core[core.code.isin(['0050','00631L']) & core.tradable].merge(fresh, on=['date','code'], suffixes=('_local','_alternate'))
    tests = []
    for code, group in pairs.groupby('code'):
        for year, rows in group.groupby(group.date.str[:4]):
            valid = rows[rows.close_provider.notna()]
            raw = (valid.close_local-valid.close_provider).abs()<=.005
            hypothesis = (valid.close_local-valid.close_alternate).abs()<=.005
            tests.append(dict(code=code,year=year,compared_rows=len(valid),provider_close_matches=int(raw.sum()),split_hypothesis_matches=int(hypothesis.sum()),neither_matches=int((~raw & ~hypothesis).sum()),certified_raw_conversion=False))
    pd.DataFrame(tests).to_csv(OUT/'etf_price_unit_hypothesis_check.csv', index=False)
    result = dict(status='DATA_RECONCILIATION_FINISHED_WITH_OPEN_BLOCKERS', backtest_ready=False, publication_allowed=False, audited_canonical_inputs_unchanged=True, calendar_conflicts=len(conflicts), reported_closed_alternate_dates=2, supported_local_sessions=sum(r['status']=='LOCAL_SESSION_SUPPORTED_ALTERNATE_INDEX_OMISSION' for r in conflicts), primary_supported_local_sessions=sum(r.get('source_class')=='PRIMARY_TWSE_PUBLISHED_DATE_EVIDENCE' for r in conflicts), full_historical_official_calendar_certified=False, newly_identified_local_missing_dates=['2023-05-25'], unresolved_calendar_conflicts=sum(r['status']=='UNRESOLVED_CALENDAR_CONFLICT' for r in conflicts), source_candidates_not_promoted=len(candidates), unresolved_price_fields=len(differences), unresolved_price_fields_are_not_proven_local_errors=True, private_quotes_recovered_research_only=24, core_quotes_recovered_research_only=10, required_before_full_backtest=['Full official historical calendar proof remains distinct from news-supported conflict decisions','Historical split/rights unit contract and exceptional price discrepancies','Dividend date availability/revisions and payment evidence'], backtest_executed=False)
    (OUT/'reconciliation_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'calendar_evidence.json').write_text(json.dumps(EVIDENCE,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    main()
