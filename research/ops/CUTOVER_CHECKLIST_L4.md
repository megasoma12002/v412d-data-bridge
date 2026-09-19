# Cutover checklist — L4_DD_PATH_08_50

Status: **PREP ONLY — NOT AUTHORIZED**  
Soft-Frozen live Financial clip: **[0.60, 0.90] KEEP** (FINBAND).  
Parent decision: `research/ops/HUMAN_DECISION_REGISTER.md` (#4 **DEFER**).  
Observe: `L4_DD_PATH_PROMOTE_PROPOSAL.md` · runbook: `L4_DD_PATH_MONTH_END_RUNBOOK.md` · monitor: `L4_DD_PATH_MONTH_END_MONITOR.md`

This file is **not** authorization to cut over L4.

## What cutover would change

- Wire **path-dependent DD-path logic** into live (not a static Financial clip swap):  
  FIN_CAP **[0.35, 0.50]** only while TAIEX active DD from 252d peak **≤ −8%**; else Soft-Frozen BASE.
- Live Soft-Frozen default remains BASE until that PR merges.

## Gates (all required)

| # | Gate | Current (asof **2026-09-16** pack) | Pass? |
|---|---|---|---|
| 1 | Held-out research | `PASS_HELDOUT_L4` | YES |
| 2 | Exact T+1 on paper books | Dual-paper ledgers | YES |
| 3 | ≥1 **clean** month-end (no YTD/1y `PAUSE_REVIEW`) | YTD gb **~9.53 pp** · trailing_1y gb **~5.33 pp** → dual **PAUSE_REVIEW** | **NO** |
| 4 | Sealed / decision-window hygiene | sealed MDD worse than BASE; sealed gb ~2.99 pp | **WATCH** (ALERT) |
| 5 | Live QC smoke green on `forward/e21` | Ops Phase 1 workflow | Separate check |
| 6 | Live↔paper recon reviewed (thin overlap OK to note) | INDEX_DRIFT non-decision (ops residual) | Watch |
| 7 | Explicit human approval + dedicated cutover PR | Not opened | **NO** |
| 8 | Soft-Frozen single-source untouched until PR | `e16_soft_frozen_base.py` / FINBAND KEEP | YES |

## Blockers now

1. **YTD and trailing_1y both `PAUSE_REVIEW`** (>5 pp giveback) — extend observation via month-end pack; does **not** revoke `PASS_HELDOUT_L4`.  
2. Sealed MDD worse than BASE (paper ALERT) — no cutover talk.  
3. No human cutover PR drafted against live path.  
4. Soft-Frozen KEEP until explicit PR.

## When gates clear — PR shape (do not pre-merge)

1. Title: `Cutover: wire L4_DD_PATH_08_50 DD-path (Soft-Frozen human-approved)`  
2. Body must quote this checklist with all gates YES + fresh `L4_DD_PATH_MONTH_END_MONITOR.json`  
3. Implementation: DD-path branch in live pipeline **only** under flag / explicit default change approved in PR  
4. Forbidden in that PR: FIN50 static clip, BLEND_025 bundle, E45/E50 overlay, history rewrite  

## Operator loop until then

```bash
python3 scripts/e16_l4_dd_path_dual_paper_ledgers.py
python3 scripts/e16_l4_dd_path_month_end_monitor.py
# or: python3 scripts/ops_month_end_paper_pack.py
# review research/gaps/L4_DD_PATH_MONTH_END_MONITOR.md
```

## Parallel note

- FIN50 static cutover remains **REJECT for now** (`NOT_READY_SEALED_CAGR`).  
- FINCAP BLEND_025 observe remains separate (register #3/#5) — do not conflate.  
- Hygiene sync note: `research/ops/L4_HYGIENE_CHECKLIST_SYNC_2026-09-19.md`

Label: `CUTOVER_CHECKLIST_L4__NOT_AUTHORIZED`
