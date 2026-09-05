# E45 Stage 1–3 Status (Post Charter ACCEPT)

Date: 2026-09-05  
Ballot: **ACCEPT charter** (human) — Stage 1–3 research **OPEN**  
Live stitch: **still FORBIDDEN**  
Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`** (do not invent a replacement)

Authority: `HUMAN_DECISION_REGISTER.md` #6c · `E45_LIVE_STITCH_CHARTER.md` · `E45_LIVE_STITCH_DECISION_PACK.md`

## Verification bars V1–V6

| # | Bar | Status | Notes |
|---|---|---|---|
| V1 | Artifact match | **FAIL** | No dated CSV/JSON MDD == −0.1316 |
| V2 | Lineage honesty | **PASS (labeled)** | Claim kept `NOT_VERIFIED`; publish verified lineage MDDs |
| V3 | Exact T+1 | **PASS (shared path)** | Fill clock on E18 / early-stack; E45 emits exposure only |
| V4 | Cost / stress | **PASS** | E45-named 0×–3× cost table; MDD still shallower vs BASE at 1×–3× (`E45_V4_COST_STRESS_PACK.md`) |
| V5 | No single-year | **PASS** | Crisis-year attribution 2015/2018/2020/2022 improve MDD; max share ~50%; 2008 N/A documented (`E45_V5_MULTI_WINDOW_PACK.md`) |
| V6 | Soft-Frozen KEEP | **PASS** | Clip unchanged |

**Stage gate:** V1 still FAIL ⇒ **no stitch PR**. V4/V5 PASS does **not** authorize live stitch.

## Stage progress

| Stage | Status | Artifact |
|---|---|---|
| 0 Charter ACCEPT | **DONE** | Decision pack + register #6c |
| 1 Verification recompute | **DONE** | `research/e45/E45_MDD_1316_VERIFICATION.*` |
| 2 Paper challenger memo | **DONE** | `research/e45/E45_STAGE2_PAPER_CHALLENGER_MEMO.md` |
| 3 Dual-paper observe design | **DONE** | `research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md` + checklist |
| 3b Operating observe | **NOT OPENED** | Needs `E45 OPEN dual-paper observe` |
| 4 Stitch checklist + human PR | **BLOCKED** | Needs V1 PASS + V2–V6 PASS + second ballot |
| 5 Post-QC / claim policy | **N/A** | Live unchanged |

## V4 snapshot (E45-named cost multiples)

| ×cost | MDD Δ vs BASE (pp) | CAGR giveback (pp) |
|---:|---:|---:|
| 0 | +1.89 | 2.92 |
| 1 | +1.88 | 2.99 |
| 2 | +1.90 | 3.03 |
| 3 | +1.92 | 3.11 |

## V5 snapshot (crisis-year MDD Δ vs BASE)

| Year | avail | MDD Δ (pp) | ret Δ (pp) |
|---:|---|---:|---:|
| 2008 | N/A | — | market starts 2011-12 |
| 2011 | N/A | — | post-warmup / no usable days |
| 2015 | yes | +0.85 | −0.66 |
| 2018 | yes | +0.84 | −1.58 |
| 2020 | yes | +1.88 | −1.25 |
| 2022 | yes | +0.19 | −2.09 |

## Next actions

1. Optional: `E45 OPEN dual-paper observe` (paper month-end; still not live)  
2. Optional: chase V1 with hash-pinned E45 NAV that either matches a real claim or permanently retires −13.16% narrative (no invention)  
3. **Do not** open live stitch PR while V1 FAIL

## Label

`E45_STAGE12_STATUS_2026-09-05__V4_V5_PASS__V1_FAIL__STITCH_FORBIDDEN`
