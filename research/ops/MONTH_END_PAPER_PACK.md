# Ops Month-End Paper Pack

Generated: `2026-09-12T13:42:41.989263+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen **[0.60, 0.90] unchanged**; no cutover.

- Refresh ledgers: **True**
- All steps OK: **True**

| Step | OK | Exit |
|---|---|---:|
| `l4_dual_paper_ledgers` | True | 0 |
| `fincap50_dual_paper_ledgers` | True | 0 |
| `blend025_dual_paper_ledgers` | True | 0 |
| `e45_dual_paper_ledgers` | True | 0 |
| `e45_blend025_dual_paper_ledgers` | True | 0 |
| `e45_blend005_dual_paper_ledgers` | True | 0 |
| `e45_sleeve_local_dual_paper_ledgers` | True | 0 |
| `e45_m2_bil_fx_dual_paper_ledgers` | True | 0 |
| `fin_within_sleeve_dual_paper_ledgers` | True | 0 |
| `fin_priv_native_dual_paper_ledgers` | True | 0 |
| `soft_assist_dual_paper_ledgers` | True | 0 |
| `sleeve_tilt_dual_paper_ledgers` | True | 0 |
| `l4_month_end` | True | 0 |
| `fincap50_month_end` | True | 0 |
| `blend025_month_end` | True | 0 |
| `e45_month_end` | True | 0 |
| `e45_blend025_month_end` | True | 0 |
| `e45_blend005_month_end` | True | 0 |
| `e45_sleeve_local_month_end` | True | 0 |
| `e45_m2_bil_fx_month_end` | True | 0 |
| `fin_within_sleeve_month_end` | True | 0 |
| `fin_priv_native_month_end` | True | 0 |
| `soft_assist_month_end` | True | 0 |
| `sleeve_tilt_month_end` | True | 0 |
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


## Soft ∥ Sleeve observe (this pack)

| Track | Challenger | Held-out score | Alerts | Verdict |
|---|---|---:|---|---|
| Soft-assist | `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` | ≈+0.101 | none | `KEEP_OBSERVE` |
| Sleeve-tilt | `SLEEVE_RSI14_LT30_a0225` | ≈+0.099 | none | `KEEP_OBSERVE` |

Overlap heldout: corr ≈ **+0.112** · same-sign **48.1%** · both− **25.1%** · joint DD **46.9%** · high_joint_dd=`True` → **no combo** (Gate H).  
Checklist: `MONTH_END_PROMOTE_GATE_CHECKLIST.md`. Fuse research charter (screen not run): `SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.md`.

## Hard rules

- No Soft-Frozen flip
- Dual-paper / held-out PASS ≠ cutover license
- Never rewrite `forward/e21` history

## Re-run

```bash
python3 scripts/ops_month_end_paper_pack.py
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow
```

Authority: `research/STRATEGY_DEBT_BOARD.md`
