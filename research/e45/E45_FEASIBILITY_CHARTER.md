# E45 Paper Feasibility Charter

Date: 2026-09-05  
Status: **OPEN — paper research only**  
Parent ballot: Register #6 Item 3 — stitch path **DEFERRED** (not REJECT)  
Canonical status: `research/e45/E45_OFFICIAL_STATUS.md`

## Objective

Research until we can answer: **Is E45_E3 feasible as a crisis overlay on the early stack?**  
Only after a clear paper verdict may humans ballot whether to switch live.

## Non-goals (hard)

- Do **not** modify E45 strategy logic or locked `E3_WINNER` parameters  
- Do **not** change live wiring / `forward/e21`  
- Do **not** change `DEFAULT_BOOKS_VERSION` (live remains `E22_v2s_tw`)  
- Do **not** promote or reject E45  
- Do **not** treat −13.16% as verified; label remains `NOT_VERIFIED_HISTORICAL_NARRATIVE`  
- Do **not** invent a replacement MDD

## Comparison pair (locked)

| Arm | Definition |
|---|---|
| **Baseline** | E16 + Exact T+1 E18 + E22_v2s (no E45) |
| **Challenger** | Baseline + E45 profile `E3_VOLTARGET_WINNER` (locked params) |

Secondary (diagnostic only): E45_E1, LEGACY crisis-day scale — not stitch candidates.

## Feasibility gates (paper)

| Gate | Pass rule | Fail rule |
|---|---|---|
| F1 Artifact honesty | All reported MDDs/CAGRs cite dated CSV/JSON from this run or prior dated packs | Narrative −13.16% used as PASS |
| F2 Exact T+1 | Same-bar fills = 0 on both arms | Any same-bar fill |
| F3 Crisis MDD | Challenger crisis-window MDD **strictly better** (shallower) than baseline | Crisis MDD worse or equal |
| F4 Full-sample MDD | Challenger full-sample MDD ≤ baseline MDD (shallower or equal) | Full-sample MDD deeper |
| F5 CAGR giveback | Full-sample CAGR giveback ≤ **2.0 pp** vs baseline **or** crisis-window utility clearly dominates (documented) | Giveback > 2.0 pp with no crisis-window dominance |
| F6 No retune | Uses locked `E3_WINNER` only | Any in-place param search |
| F7 Live untouched | `DEFAULT_BOOKS_VERSION` and forward path unchanged | Any live edit |

| F8 Cost | Challenger fee sum ≤ 1.05× baseline **or** fee-bps/yr ratio ≤ 1.25 | Fee drag explodes vs baseline |
| F9 Stress | MDD better on majority of named stress windows; no window worse by >1 pp | Stress MDD regresses |
| F10 Recovery | Recover days ≤ 1.15× baseline; underwater ≤ baseline+60d; trough MDD not deeper | Slower/deeper recovery |


**Paper verdict language:**

- `FEASIBLE_CONTINUE_PAPER` — F1–F4,F6,F7 pass; F5 marginal → keep researching (cost/stress/recovery), **no live ballot yet**  
- `NOT_FEASIBLE_FOR_LIVE` — F3 or F4 fail, or F5 fails hard → do not agenda live switch; may keep Soft-Frozen CRITICAL research  
- `FEASIBLE_READY_FOR_LIVE_BALLOT` — all F1–F10 pass (F8–F10 = sealed cost/stress/recovery pack) — unlocks human live-switch ballot only (does not flip live)

Default until proven otherwise: stay at stitch **DEFERRED** / live auth **NO**.

## Lineage honesty (mandatory in every report)

- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45`  
- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`

## Outputs

- `research/e45/E45_FEASIBILITY_STUDY_2026-09-05.md` (+ `.json`)  
- `repro/e45-feasibility-study/` (NAV / fills / summary)  
- This charter remains the bar; do not silently rewrite gates mid-run

## Label

`E45_FEASIBILITY_CHARTER_2026-09-05__PAPER_ONLY__NO_LIVE`
