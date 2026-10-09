#!/usr/bin/env python3
"""Reconcile reported primary timestamps; never promote incomplete vintage proof.

The archived files contain normalized facts, not original HTTP responses.
Reported announcement timestamps are distinct from retrieval times and from
proof that no earlier/later revision exists. This is a research-only boundary.
"""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
FACT_FIELDS = ('reported_at', 'ex_date', 'payment_date', 'amount', 'estimated_amount')


def timestamp(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return dt


def load_facts(directory):
    merged, manifest = {}, []
    for path in sorted(directory.glob('announcement_facts_*.json')):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append(dict(path=str(path.relative_to(ROOT)), normalized_facts_sha256=digest,
                             original_response_sha256=None))
        for row in json.loads(path.read_text()):
            query = parse_qs(urlsplit(row['source_url']).query)
            key = tuple(query[name][0] for name in ('company', 'date', 'fund', 'seq'))
            result = merged.setdefault(key, dict(code=row['code'], stage=row['stage'],
                                               source_urls=[], field_provenance={},
                                               revision_inventory_complete=False))
            if result['stage'] != row['stage']:
                raise ValueError('Conflicting announcement stage')
            if row['source_url'] not in result['source_urls']:
                result['source_urls'].append(row['source_url'])
            for field in FACT_FIELDS:
                if field not in row:
                    continue
                if field in result and result[field] != row[field]:
                    raise ValueError(f'Conflicting primary facts: {key} {field}')
                result[field] = row[field]
                result['field_provenance'].setdefault(field, []).append(
                    dict(source_url=row['source_url'], fact_file=str(path.relative_to(ROOT)),
                         normalized_facts_sha256=digest))
            if 'reported_at' in result:
                timestamp(result['reported_at'])
    return sorted(merged.values(), key=lambda r: r.get('reported_at', '')), manifest


def research_snapshot(versions, cutoff):
    """Latest reported fields at an aware cutoff, with final/estimated amounts separate.

    Does not assert certified vintage or call any production feature function.
    Unknown timestamps fail closed rather than being inferred from an ex-date.
    """
    cutoff = timestamp(cutoff)
    result = {}
    known = [r for r in versions if r.get('reported_at')]
    for row in sorted(known, key=lambda r: timestamp(r['reported_at'])):
        if timestamp(row['reported_at']) > cutoff:
            continue
        key = row['event_id']
        event = result.setdefault(key, dict(event_id=key, code=row['code'], leg='cash',
                                           publication_vintage_certified=False))
        for field in ('ex_date', 'payment_date', 'estimated_amount'):
            if field in row:
                event[field] = row[field]
                event[field + '_reported_at'] = row['reported_at']
        if row['stage'] == 'FINAL' and 'amount' in row:
            event['amount'] = row['amount']
            event['amount_reported_at'] = row['reported_at']
    return list(result.values())


def reconcile(ledger, facts):
    rows, versions = [], []
    for event in ledger:
        for leg in ('cash', 'stock'):
            if float(event[leg + '_dividend'] or 0) <= 0:
                continue
            ex = event[leg + '_ex_date']
            matched = [r for r in facts if r['code'] == event['code'] and
                       r.get('ex_date') == ex and leg == 'cash']
            final = [r for r in matched if r['stage'] == 'FINAL' and
                     all(f in r for f in ('reported_at', 'amount', 'payment_date'))]
            schedule = [r for r in matched if r['stage'] == 'ESTIMATE_SCHEDULE' and
                        'reported_at' in r and 'payment_date' in r]
            for r in matched:
                versions.append(dict(r, event_id=f"{event['code']}:{leg}:{ex}"))
            mismatches = []
            for r in final:
                if abs(r['amount'] - float(event[leg + '_dividend'])) > 1e-8:
                    mismatches.append('FINAL_AMOUNT')
                if r['payment_date'] != event[leg + '_payment_date']:
                    mismatches.append('FINAL_PAYMENT_DATE')
            for r in schedule:
                if r['payment_date'] != event[leg + '_payment_date']:
                    mismatches.append('SCHEDULE_PAYMENT_DATE')
            if final and schedule and min(timestamp(r['reported_at']) for r in final) < min(timestamp(r['reported_at']) for r in schedule):
                mismatches.append('STAGE_CLOCK_ORDER')
            if any(timestamp(r['reported_at']).date().isoformat() > ex for r in matched if r.get('reported_at')):
                mismatches.append('ANNOUNCEMENT_AFTER_EX')
            rows.append(dict(code=event['code'], leg=leg, ex_date=ex,
                             schedule_reported_at=min((r['reported_at'] for r in schedule), default=''),
                             final_amount_reported_at=min((r['reported_at'] for r in final), default=''),
                             final_matches=len(final), schedule_matches=len(schedule),
                             primary_reported_time_supported=bool(final and schedule and not mismatches),
                             mismatch_fields='|'.join(sorted(set(mismatches))),
                             publication_vintage_certified=False,
                             status='PRIMARY_REPORTED_FIELDS_MATCH' if final and schedule and not mismatches
                             else 'PRIMARY_EVIDENCE_INCOMPLETE_OR_MISMATCH'))
    return rows, versions


def write_csv(path, rows):
    if not rows:
        raise ValueError('Empty audit report')
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def audit_splits():
    from dd_switch_session_market import HALTS, SPLITS
    facts_path = OUT / 'sources/etf_split_announcement_facts.json'
    facts = json.loads(facts_path.read_text())
    results = []
    for effective, codes in SPLITS.items():
        for code, ratio in codes.items():
            match = [r for r in facts if r['code'] == code]
            schedule = [r for r in match if r['stage'] == 'APPLICATION_SCHEDULE']
            final = [r for r in match if r['stage'] == 'FINAL_UNITS_REFERENCE_PRICE']
            if len(schedule) != 1 or len(final) != 1:
                raise ValueError('Missing unique split stage evidence')
            schedule, final = schedule[0], final[0]
            for row in (schedule, final):
                if row['ratio'] != ratio or row['effective'] != effective:
                    raise ValueError('Split unit contract disagrees with primary facts')
                if row['halt_start'] != str(HALTS[code].min().date()) or row['halt_end'] != str(HALTS[code].max().date()):
                    raise ValueError('Split halt contract mismatch')
            if timestamp(schedule['reported_at']).date().isoformat() >= schedule['halt_start']:
                raise ValueError('Schedule proof was published after halt began')
            if timestamp(final['reported_at']).date().isoformat() >= effective:
                raise ValueError('Final split proof was published after resume')
            if abs(final['last_exchange_close'] / ratio - final['reference_price']) > .005:
                raise ValueError('Split reference price inconsistent with rounding')
            results.append(dict(code=code, effective=effective, ratio=ratio,
                                schedule_reported_at=schedule['reported_at'],
                                final_reported_at=final['reported_at'],
                                status='SPLIT_HALT_UNIT_CONTRACT_PRIMARY_MATCH',
                                publication_vintage_certified=False))
    return results


def main():
    facts, manifest = load_facts(OUT / 'sources')
    ledger_path = ROOT / 'data/dividend_events/e22_dividend_events.csv'
    ledger = list(csv.DictReader(ledger_path.open()))
    rows, versions = reconcile(ledger, facts)
    write_csv(OUT / 'announcement_field_check.csv', rows)
    missing = [r for r in rows if not r['primary_reported_time_supported']]
    write_csv(OUT / 'announcement_evidence_remaining.csv', missing)
    (OUT / 'announcement_versions_research.json').write_text(json.dumps(versions, indent=2) + '\n')
    (OUT / 'announcement_fact_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Zero-dividend ex-right rows may contain subscription/capital events.
    # Excluding them from the positive-dividend audit does not prove no action.
    exceptional = [dict(code=r['code'], announcement_date_secondary=r['announcement_date'],
                        ex_date_secondary=r['stock_ex_date'],
                        classification='ZERO_DIVIDEND_EX_RIGHT_REQUIRES_ACTION_PROOF',
                        share_ratio=None, subscription_price=None, primary_verified=False)
                   for r in ledger if r['stock_ex_date'] and float(r['stock_dividend'] or 0) == 0]
    write_csv(OUT / 'nondividend_action_candidates.csv', exceptional)
    splits = audit_splits()
    (OUT / 'split_announcement_check.json').write_text(json.dumps(splits, indent=2) + '\n')
    summary = dict(status='PRIMARY_TIMESTAMP_ENRICHMENT_COMPLETE_CERTIFICATION_BLOCKED',
                   normalized_primary_announcements=len(facts), positive_dividend_legs=len(rows),
                   primary_reported_time_supported_legs=sum(r['primary_reported_time_supported'] for r in rows),
                   remaining_primary_time_legs=len(missing),
                   mismatched_legs=sum(bool(r['mismatch_fields']) for r in rows),
                   zero_dividend_ex_right_candidates=len(exceptional),
                   split_contracts_primary_matched=len(splits),
                   publication_vintage_certified_legs=0, backtest_ready=False,
                   backtest_executed=False, canonical_modified=False,
                   ledger_sha256=hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
                   limits=['Normalized fact hashes do not authenticate original HTTP bodies',
                           'Reported timestamps do not certify first publication or a complete revision inventory',
                           'Research snapshot is not integrated into production feature/entitlement code',
                           'Zero-dividend ex-right candidates must not be treated as free stock dividends'])
    (OUT / 'announcement_evidence_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
