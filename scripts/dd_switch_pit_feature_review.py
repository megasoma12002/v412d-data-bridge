#!/usr/bin/env python3
"""Bounded feature-only experiment; no portfolio, trades or returns are generated."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from dd_switch_pit_features import features_at
from soft_assist_helpers import LIVE_KD
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'repro/dd-switch-full-history-audit'
CODES = ['2880', '2886', '2892', '5880']


def main():
    market_path = ROOT / 'repro/dd-switch-seven-session-rebuild/inputs/parents_with_off.csv'
    versions_path = OUT / 'announcement_versions_research.json'
    ledger_path = ROOT / 'data/dividend_events/e22_dividend_events.csv'
    market = pd.read_csv(market_path, dtype={'code': str})
    market['date'] = pd.to_datetime(market.date)
    versions = json.loads(versions_path.read_text())
    ledger = pd.read_csv(ledger_path, dtype={'code': str}).fillna('')
    calendar = pd.DatetimeIndex(sorted(market.date.unique()))
    params = {k: LIVE_KD[k] for k in ['k_thresh', 'season_start', 'season_end', 'pre_days', 'active_score']}
    legacy_kd = build_kd_season_tilt_scores(market, ledger, CODES, **params)
    legacy_ok = build_pre_exdiv_window_buy_ok(calendar, ledger, CODES, pre_days=params['pre_days'])
    rows = []
    for year in (2025, 2026):
        for month, day in ((5, 15), (6, 5), (7, 1)):
            t = calendar[calendar <= pd.Timestamp(year, month, day)][-1]
            cutoff = t.date().isoformat() + 'T13:30:00+08:00'
            result = features_at(market, versions, calendar, CODES, cutoff, params)
            # Verify both a physically truncated price input and poisoned future prices.
            prefix = features_at(market[market.date <= t], versions, calendar, CODES, cutoff, params)
            altered = market.copy()
            altered.loc[altered.date > t, ['high', 'low', 'close']] *= 100.
            additions = [dict(r, reported_at=(t + pd.Timedelta(days=1)).date().isoformat() + 'T14:00:00+08:00',
                              ex_date='2099-12-31') for r in versions if r['code'] in CODES][:20]
            future = features_at(altered, versions + additions, calendar, CODES, cutoff, params)
            if result != prefix or result != future:
                raise ValueError('Future inputs changed a prior feature decision')
            for code in CODES:
                rows.append(dict(date=result['date'], code=code,
                                 legacy_full_ledger_kd=float(legacy_kd.loc[t, code]),
                                 snapshot_kd=result['kd'][code],
                                 kd_changed=not np.isclose(legacy_kd.loc[t, code], result['kd'][code]),
                                 legacy_full_ledger_buy_ok=bool(legacy_ok.loc[t, code]),
                                 snapshot_buy_ok=result['buy_ok'][code],
                                 buy_mask_changed=bool(legacy_ok.loc[t, code]) != result['buy_ok'][code],
                                 known_schedules=result['known_schedules'], future_invariance_passed=True))
            print(json.dumps(dict(cutoff=cutoff, checked_names=len(CODES), status='FEATURE_ONLY_PASS')), flush=True)
    with (OUT / 'pit_feature_snapshot_check.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    summary = dict(status='RESEARCH_FEATURE_GATE_TESTED_CERTIFICATION_STILL_BLOCKED',
                   cutoff_days=len(rows) // len(CODES), name_cutoffs=len(rows),
                   kd_changed=sum(r['kd_changed'] for r in rows),
                   buy_mask_changed=sum(r['buy_mask_changed'] for r in rows),
                   future_invariance_passed=True, tests_passed=10,
                   historical_revision_inventory_complete=False, publication_vintage_certified=False,
                   calendar_vintage_certified=False, production_integrated=False,
                   backtest_ready=False, backtest_executed=False, canonical_modified=False,
                   inputs_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in (market_path, versions_path, ledger_path)},
                   limitations=['Reported clocks are not historical publication archive certification',
                                'Calendar labels are observed market sessions, not a certified historical calendar vintage',
                                'Bounded 2025/2026 feature checks do not certify all historical dates',
                                'The legacy comparison changes both event availability and the calendar-prefix issue; no causal NAV attribution',
                                'Stable event identities and complete revisions still require source proof'])
    (OUT / 'pit_feature_snapshot_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k != 'inputs_sha256'}))


if __name__ == '__main__':
    main()
