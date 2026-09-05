# Cutover checklist — L4_DD_PATH_08_50

Status: **PREP ONLY** — Soft-Frozen **[0.50, 0.95] stays** until a human PR lands.  
This file is not authorization to cut over.

## What cutover would change

- Wire **path-dependent DD-path logic** into live (not a static Financial clip swap).
- Live Soft-Frozen default remains BASE until that PR merges.

## Gates (all required)

| # | Gate | Current (asof 2026-09-04 pack) | Pass? |
|---|---|---|---|
| 1 | Held-out research | `PASS_HELDOUT_L4` | YES |
| 2 | Exact T+1 on paper books | Required in research path | YES (historical) |
| 3 | ≥1 **clean** month-end (no YTD/1y `PAUSE_REVIEW`) | YTD giveback ~5.39 pp → **PAUSE_REVIEW** | **NO** |
| 4 | Live QC smoke green on `forward/e21` | Ops Phase 1 workflow | Separate check |
| 5 | Live↔paper recon reviewed (thin overlap OK to note) | INDEX_DRIFT ~2.2% on 10 sessions | Watch |
| 6 | Explicit human approval + dedicated cutover PR | Not opened | **NO** |
| 7 | Soft-Frozen single-source untouched until PR | `e16_soft_frozen_base.py` | KEEP |

## Blockers now

1. **YTD / trailing giveback PAUSE_REVIEW** — extend observation via `ops_month_end_paper_pack`.  
2. No human cutover PR drafted against live path.

## When gates clear — PR shape (do not pre-merge)

1. Title: `Cutover: wire L4_DD_PATH_08_50 DD-path (Soft-Frozen human-approved)`  
2. Body must quote this checklist with all gates YES  
3. Implementation: DD-path branch in live pipeline **only** under flag / explicit default change approved in PR  
4. Forbidden in that PR: FIN50 static clip, E45/E50 overlay, history rewrite  

## Operator loop until then

```bash
python3 scripts/ops_month_end_paper_pack.py
# review research/gaps/L4_DD_PATH_MONTH_END_MONITOR.md
```

Label: `CUTOVER_CHECKLIST_L4__NOT_AUTHORIZED`
