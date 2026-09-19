# Ops Month-End Paper Pack

Generated: `2026-09-19T05:46:51.969125+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen **[0.60, 0.90] unchanged**; no cutover.

- Refresh ledgers: **True**
- All steps OK: **True**
- Data freshness (hard): **True**

## Data freshness

| Signal | Value |
|---|---|
| Live market tip | `2026-09-16` (age 3 cal days) |
| E22 events age | 5 cal days · fetch `PASS` · kpi_ok `True` |
| Shadow reconcile | all_ok `True` |

Detail: `research/ops/MONTH_END_DATA_FRESHNESS.md` · cadence note: `research/ops/MONTH_END_PACK_FRESHNESS.md`

| Step | OK | Exit |
|---|---|---:|
| `l4_dual_paper_ledgers` | True | 0 |
| `fincap50_dual_paper_ledgers` | True | 0 |
| `blend025_dual_paper_ledgers` | True | 0 |
| `e45_dual_paper_ledgers` | True | 0 |
| `e45_blend005_dual_paper_ledgers` | True | 0 |
| `e45_sleeve_local_dual_paper_ledgers` | True | 0 |
| `e45_m2_bil_fx_dual_paper_ledgers` | True | 0 |
| `fin_within_sleeve_dual_paper_ledgers` | True | 0 |
| `fin_priv_native_dual_paper_ledgers` | True | 0 |
| `soft_assist_dual_paper_ledgers` | True | 0 |
| `sleeve_tilt_dual_paper_ledgers` | True | 0 |
| `fuse_additive_dual_paper_ledgers` | True | 0 |
| `e45_defend_handoff_dual_paper_ledgers` | True | 0 |
| `l4_month_end` | True | 0 |
| `fincap50_month_end` | True | 0 |
| `blend025_month_end` | True | 0 |
| `e45_month_end` | True | 0 |
| `e45_blend005_month_end` | True | 0 |
| `e45_sleeve_local_month_end` | True | 0 |
| `e45_m2_bil_fx_month_end` | True | 0 |
| `fin_within_sleeve_month_end` | True | 0 |
| `fin_priv_native_month_end` | True | 0 |
| `soft_assist_month_end` | True | 0 |
| `sleeve_tilt_month_end` | True | 0 |
| `fuse_additive_month_end` | True | 0 |
| `e45_defend_handoff_month_end` | True | 0 |
| `soft_sleeve_observe_overlap` | True | 0 |
| `track_a_s9a1` | True | 0 |
| `live_paper_recon` | True | 0 |
| `e22_data_quality_kpi` | True | 0 |
| `e22_gap6_fidelity_kpi` | True | 0 |
| `data_source_shadow_reconcile` | True | 0 |
| `data_source_phase_c_probes` | True | 0 |
| `data_source_resilience_kpi` | True | 0 |
| `fincap50_sealed_cagr_charter_screen` | True | 0 |
| `ops_alert_scan` | True | 0 |

## Hard rules

- No Soft-Frozen flip
- Dual-paper / held-out PASS ≠ cutover license
- Never rewrite `forward/e21` history
- Pack ≠ dividend re-fetch (use `v412e22-dividend-events` on-demand)

## Re-run

```bash
# Fast path (monitors only)
python3 scripts/ops_month_end_paper_pack.py
# Formal month-end (rebuild observe ledgers)
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers
# Formal + fail closed on stale market tip / E22
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers --fail-on-stale
```

Authority: `research/STRATEGY_DEBT_BOARD.md`
