#!/usr/bin/env python3
"""List every remaining evidence category without converting leads into settlement facts."""
import csv
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'repro/dd-switch-full-history-audit'


def read(name):
    return list(csv.DictReader((OUT / name).open()))


def main():
    rows = []

    def add(category, identity, status, available, required):
        rows.append(dict(category=category, event_id=identity, status=status,
                         available_evidence=available, required_to_close=required,
                         backtest_permission=False))

    scoped = json.loads((OUT / 'scoped_delivery_evidence.json').read_text())
    holder = {r['event_id']: r for r in scoped['public_holder_distribution_rows']}
    stage = {r['event_id']: r for r in json.loads((OUT / 'remaining_dividend_share_stage_evidence.json').read_text())}
    for r in read('remaining_0050_revision_stage_gaps.csv'):
        add('0050_REVISION_STAGE', r['event_id'], 'OPEN',
            f"ESTIMATE={r['estimate_versions']}; FINAL={r['final_versions']}",
            'Issuer-original ' + r['missing_stages'] + '; exact fund, ex/payment dates and amount; preserved publication/version provenance')
    for r in read('remaining_dividend_payment_gaps.csv'):
        evidence = []
        if r['event_id'] in holder:
            h = holder[r['event_id']]
            evidence.append('MOE holder-only credit ' + h['reported_distribution_date'])
        if stage.get(r['event_id'], {}).get('explicit_listing_evidence'):
            evidence.append('Primary listing notice; separate delivery date absent')
        add('STOCK_DELIVERY', r['event_id'], 'OPEN', '; '.join(evidence) or 'Declaration/capital registration; no dated general delivery',
            'Original issuer or transfer-agent general stock delivery date for this allocation; listing/record date and holder-only credit insufficient')
    for r in read('remaining_subscription_delivery_gaps.csv'):
        available = 'Subscription window ' + r['subscription_start'] + '..' + r['subscription_end']
        available += '; voucher=' + (r['subscription_voucher_delivery_date'] or 'unavailable')
        available += '; primary ordinary listing=' + (r['new_share_listing_date'] or 'unavailable')
        add('SUBSCRIPTION_DELIVERY', r['code'] + ':subscription:' + r['ex_date'], 'OPEN', available,
            'General final ordinary-share book-entry/conversion delivery notice; preserve voucher stage; paid holder election required before simulated credit')
    for r in read('dividend_settlement_check.csv'):
        if r['payment_date_conflict'] == 'True':
            add('RIGHTS_ORDINARY_PHASE', r['event_id'], 'OPEN_MODEL_AND_QUOTES',
                'Ledger early stage=' + r['ledger_payment_date'] + '; primary ordinary=' + r['latest_primary_payment_date'] + '; source=' + r['source_id'],
                'Separate entitlement, rights instrument and ordinary conversion; verify prices, units and trade eligibility in intervening period before changing ledger')
    for r in read('subscription_settlement_check.csv'):
        if r['not_yet_due_asof'] == 'True' and not r['new_share_delivery_date']:
            add('FUTURE_SUBSCRIPTION', r['code'] + ':subscription:' + r['ex_date'], 'NOT_DUE_ASOF_2026_10_08',
                'Public future subscription schedule', 'Observe final delivery when published; do not count as overdue or assume subscription')
    restored = json.loads((OUT / 'audited_input_restoration.json').read_text())
    for path, sha in restored['inputs'].items():
        add('RESEARCH_INPUT', path, 'CLOSED_EXACT_HASH', sha, 'Closed by input-only restoration; no strategy run')
    add('HISTORICAL_REVISION_INVENTORY', 'ALL_RESEARCH_EVENTS', 'OPEN',
        'Current saved indexes and original announcements; revised versions retained',
        'Demonstrable original/revised historical coverage, including omissions; current indexes alone cannot certify completeness')
    add('PUBLICATION_VINTAGE', 'ALL_RESEARCH_EVENTS', 'OPEN',
        'Date-only source availability retained; certified legs=0',
        'Historical availability/version proof and conservative execution timing for each input; do not invent publication clocks')
    # Carry every broader certification blocker as well. These are existing audit
    # findings, not a claim that the strategy or whole-lineage audit ran again.
    for blocker in json.loads((OUT / 'blockers.json').read_text()):
        add('FULL_HISTORY_CERTIFICATION', blocker['id'], 'OPEN_PRIOR_AUDIT_FINDING',
            'Existing blockers.json; ' + blocker['reason'],
            'Resolve the stated source/model/lifecycle requirement, then rerun the relevant audit; input recovery alone is insufficient')
    with (OUT / 'comprehensive_remaining_gap_inventory.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    summary = dict(counts=dict(Counter(r['category'] for r in rows)),
                   counts_are_not_additive=True, backtest_ready=False, backtest_executed=False,
                   canonical_modified=False, input_gap_count=0,
                   note='Categories overlap; open evidence gaps are derived from the latest verified audit outputs')
    (OUT / 'comprehensive_gap_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
