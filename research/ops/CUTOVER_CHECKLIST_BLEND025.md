# Cutover checklist — BLEND_025

Status: **PREP ONLY — NOT AUTHORIZED**  
Soft-Frozen live clips: **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]** · overlay **FUSE_ADDITIVE + COOL_c8** · Class D FinPriv V7 F05 (**KEEP**).  
Parent decisions: `research/ops/HUMAN_DECISION_REGISTER.md` (#3 observe, #5 live NOT READY).  
Observe sleeve: `BLEND_025_DUAL_PAPER_OBSERVE.md` · runbook: `BLEND_025_MONTH_END_RUNBOOK.md`  
Promote gate review (2026-09-26): `BLEND_025_PROMOTE_GATE_REVIEW_2026-09-26.md` → **BLOCKED**

This file satisfies the register re-open prerequisite **“cutover checklist drafted.”**  
It does **not** authorize promote or live-wire.

## What cutover would change (future human PR only)

- Replace Soft-Frozen static Financial path with **BLEND_025** weights:  
  `α=0.25·FIN_CAP_50[0.35,0.50] + 0.75·Soft-Frozen` (renormalized to **live** Soft-Frozen clips).  
- Not a FIN50-only static swap; not L4 DD-path logic.  
- Must re-twin vs current live (`FUSE_COOL` ± Class D) — do not cut over on stale `BASE_E16`-only evidence.

## Gates (all required)

| # | Gate | Current | Pass? |
|---|---|---|---|
| 1 | Exact T+1 on dual-paper books | Required on observe ledgers | YES (harness) |
| 2 | Charter hist gates (OOF / late / sealed) | Screen PASS → paper proposal | YES (research) |
| 3 | Dual-paper **OPERATING OBSERVE** on main | observe sleeve | YES |
| 4 | ≥1 clean month-end: no YTD/1y `PAUSE_REVIEW` | asof **2026-09-16** still `PAUSE_REVIEW` ytd | **NO** |
| 5 | Sealed CAGR giveback vs BASE within charter | sealed MDD ALERT on last print | **NO / WATCH** |
| 6 | Soft-Frozen unchanged until cutover PR | live KEEP | YES |
| 7 | Dedicated cutover checklist all YES + human PR | promote review 2026-09-26 BLOCKED | **NO** |
| 8 | Must not bundle FIN50-only static, L4 DD-path, E45/E50 | — | Policy |

## Blockers now

1. Register #5: live **NOT DECISION-READY** — observe ≠ promote.  
2. Month-end **PAUSE_REVIEW** (ytd giveback > 5 pp) — not sustained clean.  
3. Live SSOT drift (β densify · COOL · Class D) vs older BLEND twin — rebase before promote.  
4. No human cutover PR.  
5. Soft-Frozen KEEP until explicit PR.

## When gates clear — PR shape (do not pre-merge)

1. Title: `Cutover: Soft-Frozen → BLEND_025 (α=0.25·FIN50 + 0.75·BASE)`  
2. Body quotes this checklist with all gates YES + fresh month-end JSON  
3. Implementation: single approved live weight path only — **no silent Soft-Frozen edit**  
4. Forbidden in that PR: FIN50-only lock retune, L4 DD-path, E45/E50 overlay, history rewrite  

## Operator loop until then

```bash
python3 scripts/e16_blend025_dual_paper_ledgers.py
python3 scripts/e16_blend025_month_end_monitor.py
# or: python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers
# review research/gaps/BLEND_025_MONTH_END_MONITOR.md
```

## Parallel note

- FIN50 static cutover remains **REJECT for now** (`NOT_READY_SEALED_CAGR`).  
- L4 cutover remains **DEFER** on its own checklist.  
- Do not conflate BLEND observe PASS with FIN50 or L4 promote.

Label: `CUTOVER_CHECKLIST_BLEND025__NOT_AUTHORIZED__REVIEW_2026-09-26_BLOCKED`
