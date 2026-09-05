# E45 Stage 1–3 Status (Post Charter ACCEPT)

Date: 2026-09-05  
Ballot: **ACCEPT charter** (human) — Stage 1–3 research **OPEN**  
Live stitch: **still FORBIDDEN**  
Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`** (do not invent a replacement)

Authority: `HUMAN_DECISION_REGISTER.md` #6c · `E45_LIVE_STITCH_CHARTER.md` · `E45_LIVE_STITCH_DECISION_PACK.md`

## What this stage may do

1. Freeze / score verification bars V1–V6  
2. Recompute / attach dated MDD artifacts  
3. Paper-only Exact T+1 challenger report with honest MDD labels  
4. Dual-paper observe sleeve **design** (+ optional later OPEN observe)

## What this stage may **not** do

- Four-layer live stitch / live-wire into `forward/e21`  
- Soft-Frozen flip  
- History rewrite  
- Bundling L4 / FIN50 / BLEND / odd-lot / tax DEFAULT promote  
- Treating Soft-Frozen_CRITICAL as proof of −13.16%

## Verification bars V1–V6

| # | Bar | Status | Notes |
|---|---|---|---|
| V1 | Artifact match | **FAIL** | No dated CSV/JSON MDD == −0.1316 |
| V2 | Lineage honesty | **PASS (labeled)** | Claim kept `NOT_VERIFIED`; publish verified lineage MDDs instead |
| V3 | Exact T+1 | **PASS (shared path)** | Fill clock on E18 / early-stack path; E45 emits exposure only |
| V4 | Cost / stress | **PARTIAL** | Lineage E3 cost CSV attached; E45-named seal still open (`E45_V4_COST_STRESS_PACK.md`) |
| V5 | No single-year | **PARTIAL** | Multi-window paper metrics attached; named multi-crisis seal still open (`E45_V5_MULTI_WINDOW_PACK.md`) |
| V6 | Soft-Frozen KEEP | **PASS** | Clip unchanged; this pack does not flip |

**Stage gate:** V1 still FAIL ⇒ **no stitch PR**. Continue paper / design only.

## Stage progress

| Stage | Status | Artifact |
|---|---|---|
| 0 Charter ACCEPT | **DONE** 2026-09-05 | Decision pack + register #6c |
| 1 Verification recompute | **DONE** (refresh) | `research/e45/E45_MDD_1316_VERIFICATION.*` · `repro/e45-mdd-verify/` |
| 2 Paper challenger report | **DONE (memo)** | `research/e45/E45_STAGE2_PAPER_CHALLENGER_MEMO.md` |
| 3 Dual-paper observe design | **DONE (design)** | `research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md` · checklist · window metrics |
| 3b Operating observe | **NOT OPENED** | Needs human `E45 OPEN dual-paper observe` |
| 4 Stitch checklist + human PR | **BLOCKED** | Needs V1–V6 all PASS + second ballot |
| 5 Post-QC / claim policy | **N/A** | Live unchanged |

## Dual-paper design snapshot (paper only)

Refresh: Stage-3 script `scripts/e45_stage3_dual_paper_windows.py`

| Window | MDD Δ vs BASE (pp; + = shallower) | CAGR giveback (pp) |
|---|---:|---:|
| full | +1.88 | 2.99 |
| heldout_2019_plus | +1.88 | 5.65 |
| sealed_2023_plus | +4.90 | 9.40 |

Interpretation: E45_E3 overlay **improves MDD** on paper windows but with **material CAGR giveback** (especially sealed). Observe ≠ promote; stitch still blocked by V1.

## Paper challenger snapshot (Stage 2)

| Variant | CAGR | MDD | vs claim −13.16% |
|---|---:|---:|---:|
| E16+E18+E22_v2s | 13.78% | −22.64% | unmatched |
| E16+E18+E22_v2s+E45_E3 | **10.79%** | **−20.76%** | unmatched |
| Closest lineage val | — | **−15.81%** (E1.1) | |err| ≈ 2.65 pp |

## Next actions

1. Human may `E45 OPEN dual-paper observe` (paper month-end) **or** `E45 KEEP design only`  
2. Optional: build E45-named cost multiples + crisis-year attribution to chase V4/V5 PASS  
3. **Do not** open live stitch PR until V1–V6 all PASS + second human ACCEPT

## Label

`E45_STAGE12_STATUS_2026-09-05__ACCEPT_CHARTER__STAGE3_DESIGN_DONE__STITCH_FORBIDDEN`
