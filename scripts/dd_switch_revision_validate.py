#!/usr/bin/env python3
"""Verify saved response hashes and persist current evidence gaps without enabling strategy execution."""
import csv, gzip, hashlib, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'repro/dd-switch-full-history-audit'
def main():
    summary=json.loads((OUT/'revision_settlement_summary.json').read_text())
    pairs=0;unavailable={};source_statuses={}
    for source in ('mops_actions','mops_revisions','mops_statutory','settlement_pages','etf_raw','targeted_issuers'):
        manifest=OUT/'sources'/source/'manifest.json'
        if not manifest.exists():continue
        rows=json.loads(manifest.read_text())
        unavailable[source]=sum(r['status']=='UNAVAILABLE' for r in rows)
        source_statuses[source]=dict(Counter(r['status'] for r in rows))
        for r in rows:
            packed=(ROOT/r['path']).read_bytes()
            assert hashlib.sha256(packed).hexdigest()==r['compressed_sha256'],r.get('id',r.get('url'))
            assert hashlib.sha256(gzip.decompress(packed)).hexdigest()==r['response_sha256'],r.get('id',r.get('url'))
            pairs+=1
    inputs=json.loads((OUT/'audited_input_sha256.json').read_text())
    verified=0; absent=[]
    for name,sha in inputs.items():
        if not name.endswith('.csv'):continue
        if not (ROOT/name).exists():absent.append(name);continue
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
        verified+=1
    missing=list(csv.DictReader((OUT/'remaining_dividend_payment_gaps.csv').open()))
    versions=json.loads((OUT/'mops_linked_revision_versions.json').read_text())
    stage_rows=[]
    for gap in missing:
        linked=[r for r in versions if r.get('event_id')==gap['event_id'] and r.get('new_share_listing_dates')]
        stage_rows.append(dict(event_id=gap['event_id'],ledger_payment_date=gap['ledger_payment_date'],explicit_listing_evidence=[{k:r[k] for k in ('id','url','response_sha256','new_share_listing_dates')} for r in linked],delivery_certified=False))
    (OUT/'remaining_dividend_share_stage_evidence.json').write_text(json.dumps(stage_rows,ensure_ascii=False,indent=2)+'\n')
    chains=list(csv.DictReader((OUT/'remaining_announcement_chain_gaps.csv').open()))
    actions=list(csv.DictReader((OUT/'subscription_settlement_check.csv').open()))
    past=[r for r in actions if not r['new_share_delivery_date'] and r['not_yet_due_asof']=='False']
    with (OUT/'remaining_subscription_delivery_gaps.csv').open('w',newline='') as h:
        writer=csv.DictWriter(h,fieldnames=list(actions[0]),lineterminator='\n');writer.writeheader();writer.writerows(past)
    result=dict(summary,payment_schedule_missing=len(missing),payment_schedule_missing_by_leg=dict(Counter(r['leg'] for r in missing)),announcement_chain_missing=len(chains),announcement_chain_missing_by_code=dict(Counter(r['code'] for r in chains)),past_subscription_delivery_missing=len(past),uncaptured_responses=unavailable,source_response_statuses=source_statuses,source_hash_pairs_verified=pairs,canonical_input_hashes_verified=verified,canonical_inputs_absent=absent,capture_progress=json.loads((OUT/'monitored_capture_progress.json').read_text()),additional_capture_progress={name:json.loads((OUT/name).read_text()) for name in ('targeted_capture_progress.json','issuer_capture_progress.json','etf_asset_capture_reviewed_progress.json','etf_app_capture_progress.json','etf_announcement_api_valid_progress.json','historical_original_probe_progress.json','yuanta_0050_pdf_probe_progress.json','yuanta_0050_pdf_capture_progress.json') if (OUT/name).exists()},issuer_pdf_validation=json.loads((OUT/'yuanta_0050_pdf_validation.json').read_text()) if (OUT/'yuanta_0050_pdf_validation.json').exists() else None,validation_scope='Saved public response integrity and current matching; historical revision completeness remains uncertified')
    (OUT/'revision_settlement_validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('limits','capture_progress')}))
if __name__=='__main__':main()
