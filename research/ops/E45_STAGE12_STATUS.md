# E45 Stage 1–3 Status (Post Charter ACCEPT + V1 narrative retirement + observe OPEN)

Date: 2026-09-05  
Ballot: **ACCEPT charter** + **RETIRE −13.16% narrative (path A)** + **OPEN dual-paper observe**  
Live stitch: **still FORBIDDEN** (needs second dedicated stitch ACCEPT)  
Soft-Frozen Financial clip: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
−13.16% claim: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement  
Dual-paper observe: **OPERATING** (paper month-end; first monitor may show YTD/1y PAUSE_REVIEW — expected for crisis overlay)

Authority: `HUMAN_DECISION_REGISTER.md` #6c · `E45_MDD_1316_NARRATIVE_RETIREMENT.md` · `E45_DUAL_PAPER_OBSERVE_OPEN.md` · `E45_LIVE_STITCH_CHARTER.md`

## Verification bars V1–V6

| # | Bar | Status | Notes |
|---|---|---|---|
| V1 | Artifact / claim gate | **PASS (narrative retired)** | Human path A retires −13.16%; stitch/paper must use dated lineage/challenger MDDs only |
| V2 | Lineage honesty | **PASS** | Primary comparable = E1.1 val **−15.81%**; challenger E45_E3 ≈ **−20.76%** |
| V3 | Exact T+1 | **PASS** | Shared early-stack fill clock |
| V4 | Cost / stress | **PASS** | E45-named 0–3× cost table |
| V5 | No single-year | **PASS** | Crisis-year attribution + Stage-3 multi-window |
| V6 | Soft-Frozen KEEP | **PASS** | Clip unchanged |

**Stage gate:** V1–V6 **all PASS** for research bars. Live stitch still **FORBIDDEN** until a **second** human stitch ACCEPT (+ checklist). Observe OPEN ≠ stitch license.

## Comparable MDD policy (binding)

| Use | Number | Status |
|---|---:|---|
| Spec/handoff −13.16% | −13.16% | **RETIRED_HISTORICAL_NARRATIVE** — do not cite as verified |
| Primary lineage comparable | **−15.81%** | E1.1 validation (dated) |
| E3 locked winner val | −18.49% | Dated lineage |
| Early-stack + E45_E3 challenger | ≈ −20.76% | Dated recompute / paper |

## Stage progress

| Stage | Status | Artifact |
|---|---|---|
| 0 Charter ACCEPT | **DONE** | Decision pack + register #6c |
| 1 Verification recompute | **DONE** | `E45_MDD_1316_VERIFICATION.*` |
| 1b Narrative retirement | **DONE** | `E45_MDD_1316_NARRATIVE_RETIREMENT.md` |
| 2 Paper challenger memo | **DONE** | `E45_STAGE2_PAPER_CHALLENGER_MEMO.md` |
| 3 Dual-paper observe design | **DONE** | design + checklist |
| 3b Operating observe | **OPEN / OPERATING** | ledgers + month-end + pack/alert wire |
| 4 Stitch checklist + human PR | **CHECKLIST DRAFTED / NOT AUTHORIZED** | `E45_STITCH_CHECKLIST.md`; **second ballot required** |
| 5 Post-QC / claim policy | **N/A** | Live unchanged |

## Next actions

1. Continue **both** observe sleeves on month-end cadence when market tip advances  
2. Compare full-E45 vs blend-α=0.25 PAUSE/trailing behavior over time  
3. Live stitch only after checklist gates clear + second human `E45 ACCEPT live stitch`


## Latest month-end refresh

- Ran: `2026-09-05T18:59:29Z` — `e45_dual_paper_ledgers.py` + `e45_month_end_monitor.py` + alert scan
- Asof: **2026-09-04** (market tip; unchanged vs prior open)
- Dynamic windows: YTD / trailing_1y still **PAUSE_REVIEW** (crisis CAGR giveback)
- Structural: heldout MDD improve ~1.88 pp / giveback ~5.65 pp; sealed ~4.90 / ~9.40 pp
- Soft-Frozen KEEP · stitch still **FORBIDDEN** · continue observe cadence

## PAPER blend-alpha screen (2026-09-06)

- Ballot: `E45 PAPER blend-alpha screen` — **PAPER ONLY**
- Artifact: `research/e45/E45_BLEND_ALPHA_PAPER_SCREEN.md`
- Held-out heuristic pick: **α=0.25** (`BLEND_E45_A25`) — MDD improve ~**+0.63 pp**, CAGR giveback ~**2.83 pp**
- Full E45 (α=1) remains operating observe challenger; this screen does **not** open a new observe sleeve or authorize stitch
- Soft-Frozen / DEFAULT **KEEP**; live stitch **FORBIDDEN**


## Blend-α=0.25 observe OPEN (2026-09-06)

- Ballot: `E45 OPEN blend-α=0.25 observe` — **OPERATING** (paper only)
- Books: `BASE_E16_E18_E22_v2s` vs `BLEND_E45_A25` (`exposure=0.75·1+0.25·E45`)
- Artifacts: `E45_BLEND025_OBSERVE_OPEN.md` · `repro/e45-blend025-dual-paper-observe/` · `E45_BLEND025_MONTH_END_MONITOR.*`
- Held-out vs BASE: MDD improve ~**+0.63 pp**; CAGR giveback ~**2.83 pp**
- First month-end asof **2026-09-04**: YTD / trailing_1y still **PAUSE_REVIEW** (near-window giveback)
- Full-E45 observe sleeve remains **OPERATING** in parallel
- Soft-Frozen / DEFAULT **KEEP**; live stitch **FORBIDDEN**


## PAPER alpha fine grid (2026-09-06)

- Ballot: `E45 PAPER alpha grid fine` — step **0.05** (α=0.00…1.00) — **PAPER ONLY**
- Artifact: `research/e45/E45_BLEND_ALPHA_GRID_FINE.md` · `repro/e45-blend-alpha-grid-fine/`
- Held-out score pick: **α=0.05** (~+0.85pp MDD / ~1.07pp CAGR giveback)
- Operating observe sleeves unchanged: full-E45 + blend-α=0.25 remain **OPERATING**
- Soft-Frozen / DEFAULT **KEEP**; live stitch **FORBIDDEN**


## PAPER crisis-triggered alpha (2026-09-06)

- Ballot: `E45 PAPER crisis-triggered alpha` — **PAPER ONLY** (chose over low-alpha deep-dive)
- Artifact: `research/e45/E45_CRISIS_TRIGGERED_ALPHA.md` · `repro/e45-crisis-triggered-alpha/`
- Modes: `CONST` refs + `GATE` (E3_exp &lt; 0.90/0.85/0.80) + `E1BIN` (~1.2% days)
- Held-out: **`CONST_A05` still preferred**; best gate `GATE_09_A25` weaker (~+0.26 / ~1.23); E1BIN MDD≈0 on held-out
- Verdict: crisis-gating α does **not** beat mild continuous low-α on held-out
- Observe sleeves unchanged; Soft-Frozen / DEFAULT **KEEP**; live stitch **FORBIDDEN**


## PAPER low-alpha deep-dive (2026-09-06)

- Ballot: `E45 PAPER low-alpha deep-dive` — roadmap priority **#1** — **PAPER ONLY**
- Artifact: `research/e45/E45_LOW_ALPHA_DEEP_DIVE.md` · `repro/e45-low-alpha-deep-dive/`
- Dense α: **0.05 / 0.08 / 0.10 / 0.12 / 0.15** (+ 0.25 observe ref)
- Held-out preferred: still **α=0.05** (~+0.85 / ~1.07); α=0.08 close 2nd (~+0.96 / ~1.33, score slightly lower)
- Adjacent steps smooth on MDD, but giveback rises ~0.21–0.27pp per step
- Month-end asof **2026-09-04**: **no** dense α clears YTD/1y PAUSE (even α=0.05)
- Observe sleeves unchanged; Soft-Frozen / DEFAULT **KEEP**; live stitch **FORBIDDEN**
- Roadmap map: `E45_PAPER_RESEARCH_ROADMAP.md` (P1–P3 done; P4–P6 open / partial)


## PAPER mild max_cut profile (2026-09-06)

- Ballot: `E45 PAPER max_cut mild profile` — roadmap priority **#3** — **PAPER ONLY**
- Artifact: `research/e45/E45_MAXCUT_MILD_PROFILE.md` · `repro/e45-maxcut-mild-profile/`
- New paper profiles: max_cut **0.25 / 0.35 / 0.40** (+ mild×α=0.50); frozen winner **max_cut=0.5 untouched**
- Held-out: still **`REF_BLEND_A05`**; best mild `MILD_MC40_FULL` weaker on score (−1.11 vs +0.32)
- Mild full / mild-blend do **not** beat low constant blend-α on held-out
- Observe sleeves unchanged; Soft-Frozen / DEFAULT **KEEP**; live stitch **FORBIDDEN**
- Roadmap: P1–P7 paper queue **DONE**; stitch still **FORBIDDEN**


## PAPER roadmap #4–#7 batch (2026-09-06)

- **#4 cost/turnover:** `E45_ALPHA_COST_TURNOVER.md` — α=0.05 survives 0–3× (MDD help ~+0.85–0.90pp)
- **#5 crisis-year attribution:** `E45_CRISIS_YEAR_ATTRIBUTION.md` — α=0.05 help **~98.7% in 2020**
- **#6 sleeve-local:** `E45_SLEEVE_LOCAL.md` — FIN+0050/high-β @α=0.05 **beats** whole-book α=0.05 on held-out score
- **#7 dual-sleeve dashboard:** `E45_DUAL_SLEEVE_MONITOR_DASHBOARD.md` — FULL+A25 observe + paper A10 companion (not OPEN)
- Roadmap map: `E45_PAPER_RESEARCH_ROADMAP.md` — **P1–P7 DONE (paper)**; stitch still **FORBIDDEN**
- Soft-Frozen / DEFAULT **KEEP**; observe OPEN sleeves unchanged



## PAPER landmine code review + coding standards (2026-09-06)

- Ballot: `E45 PAPER landmine code review` — engineering hygiene (not Soft-Frozen / stitch)
- Review: `research/ops/E45_PAPER_LANDMINE_CODE_REVIEW.md`
- Standards: `research/ops/CODING_STANDARDS.md`
- Harness: `scripts/e45_paper_harness.py` · hygiene: `scripts/check_e45_paper_hygiene.py`
- Hardening: first-class `cost_multiple` / `e45_sleeve_names`; claim emitters → `CLAIMED_MDD_STATUS`; canonical book IDs
- Soft-Frozen / DEFAULT **KEEP**; observe OPEN sleeves unchanged; live stitch **FORBIDDEN**

## Project coding-standards sweep (2026-09-06)

- Prior E45 landmine pass expanded to **project `scripts/`** actionable violations
- Coverage: `research/ops/CODING_STANDARDS_COVERAGE.md`
- Hygiene: `scripts/check_project_coding_hygiene.py` (**PASS**)
- Soft-Frozen / DEFAULT **KEEP**; stitch **FORBIDDEN**

## Project code review (2026-09-06)

- Report: `research/ops/PROJECT_CODE_REVIEW_2026-09-06.md`
- Live P0 Soft-Frozen renormalize + Exact T+1 schema fail-open **fixed**
- Research debt (harness adoption / book-ID aliases) tracked open
- Soft-Frozen / DEFAULT **KEEP**; stitch **FORBIDDEN**

## PAPER P1–P7 integrated analysis (2026-09-06)

- Write-up: `research/ops/E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`
- Cross-cut: best simple intensity **α≈0.05**; crisis-gate / mild max_cut lose; cost-robust; MDD help **~98.7% in 2020**; sleeve-local FIN/high-β slight edge (future ballot)
- Observe FULL+A25 still PAUSE; Soft-Frozen / DEFAULT **KEEP**; stitch **FORBIDDEN**

## Label

`E45_STAGE12_STATUS_2026-09-05__OBSERVE_OPERATING__V1_V6_PASS__STITCH_STILL_FORBIDDEN`

## Post-P7 next steps — ALL EXECUTED (2026-09-06)

- **Sleeve-local deep-dive (PAPER):** `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md` — denser α∈{0.05,0.08,0.10}×cost 1–2×; held-out preferred **FIN_ONLY@α=0.10** (score ~0.285) > ALL@0.05; crisis help still ~84% in 2020; does **not** open sleeve-local observe
- **OPEN blend-α=0.05 observe:** `research/ops/E45_BLEND005_OBSERVE_OPEN.md` — **OPERATING** (paper only); tip PAUSE_REVIEW on YTD/1y; Soft-Frozen KEEP; stitch FORBIDDEN
- **FULL + A25 observe cadence:** remains **OPERATING** in parallel (unchanged)
- Soft-Frozen FIN **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · live stitch **FORBIDDEN**

