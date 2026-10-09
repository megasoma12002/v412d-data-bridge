#!/usr/bin/env python3
"""Validate research-only repaired quotes against archived annual source evidence."""
import json
from pathlib import Path
import dd_switch_full_history_audit as audit

def main():
    out = audit.ROOT / 'repro/dd-switch-full-history-audit'
    fresh = audit.archive_prices(out)
    dates = set(audit.frame(out / 'verified_date_benchmark.csv').date)
    results = {}
    for name, filename in [('research_core_candidate', 'core_finmind_repaired_candidate.csv.gz'), ('research_private_candidate', 'private_fin_finmind_repaired_candidate.csv.gz')]:
        results[name] = audit.audit_quotes(name, audit.frame(out / filename), dates, fresh, out)
    for result in results.values():
        if result['duplicates'] or result['issue_counts'].get('MISSING_BENCHMARK_DATE', 0):
            raise ValueError('Research candidate has unresolved duplicate or missing quote')
        if result['redownload_difference_by_field'].get('close', 0):
            raise ValueError('Research candidate close differs from archived source')
    result = dict(status='RESEARCH_CANDIDATE_QUOTE_CHECK_PASS', backtest_ready=False, canonical_modified=False, results=results)
    (out / 'candidate_integrity.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({name: dict(rows=r['rows'], duplicates=r['duplicates'], issues=r['issue_counts'], source_compared_rows=r['redownload_compared_rows'], price_differences=r['redownload_difference_by_field']) for name, r in results.items()}))

if __name__ == '__main__':
    main()
