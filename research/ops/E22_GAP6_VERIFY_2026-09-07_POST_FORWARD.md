# E22 / Gap6 Verify — 2026-09-07 POST-FORWARD


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Human follow-up after Monday schedule landed.  
Generated: `2026-09-07T14:28:00+00:00` (approx)  
Soft-Frozen (at writing): **[0.50, 0.95]** · **live today [0.60, 0.90]**

## Forward

| Item | Value |
|---|---|
| Event | `schedule` success |
| Started | `2026-09-07T14:19:54Z` (~22:19 Taipei — GHA delay) |
| Commit | `61f188c` |
| `last_date` | **2026-09-07** |
| `last_nav` | ≈ **3,207,833** |

## Runbook

| Step | Exit | Verdict |
|---|---:|---|
| `e21_qc.py` | 0 | **PASS** · Exact T+1 ok |
| `e22_gap6_fidelity_kpi.py` | 0 | **PASS** · `kpi_ok=true` · flags `[]` |
| `e22_data_quality_kpi.py` | 0 | **PASS** |
| `ops_alert_scan.py --report-only` | 0 | HIGH (observe PAUSE only) · CRITICAL 0 · Gap6 codes **cleared** |

## Live ledger

| Field | Present |
|---|---|
| `portfolio_state.e22_books_version` | YES (`E22_v2s_tw`) |
| `portfolio_state.e22_manifest` | YES |
| `nav.csv` `e22_version` | **YES** |
| `dividends_applied.csv` | NO (optional; no apply this session) |
| `live_ledger_e22_fields_present` | **TRUE** |

## Pass criteria

| Criterion | Now |
|---|---|
| QC PASS / Exact T+1 | **YES** |
| books_version + manifest | **YES** |
| `nav.e22_version` | **YES** |
| Gap6 missing-flag cleared | **YES** |
| Soft-Frozen unchanged | **YES** |

Label: `E22_GAP6_VERIFY_2026-09-07__POST_FORWARD__EVIDENCE_PRESENT__GAP6_PASS`
