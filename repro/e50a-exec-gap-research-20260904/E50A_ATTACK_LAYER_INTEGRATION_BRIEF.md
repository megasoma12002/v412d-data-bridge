# E50-A Attack Layer Integration Brief

Date: 2026-09-04  
Branch: `cursor/e50a-exec-gap-research-d049` (based on `main`)  
Question: how to handle **“E50-A attack layer not connected”** when architecture expects overlay to raise portfolio returns toward **CAGR ≥ 20%**, while E16 alone sits ~**11–14%** and E50-A remains research/not promoted.

---

## Current state

Architecture in `FROZEN_STRATEGY_SPEC.md` defines four roles — **E16 core → E18/E22 execution → E50-A alpha overlay → E45 crisis** — but on `main` / this branch the **live production path is E16+E18 only** (`scripts/e21_forward_pipeline.py` / `forward/e21/`); E50-A is a **standalone Exact-T+1 sleeve** (`scripts/e50a3*_*.py`) marked `RESEARCH_ONLY`, and E45 is a **named challenger module** (`scripts/e45_crisis_core.py`, `CHALLENGER_CANDIDATE_NOT_PROMOTED`) not a promoted SOFT_FROZEN_CRITICAL controller with verified MDD −13.16%. Handoff decision is **`HANDOFF_COMPLETE_WITH_WARNINGS`**: roles verified, **four-layer combined engine not wired into live**. Sibling branch `cursor/early-stack-combined-nav-d049` later built an **EXPERIMENTAL challenger sandbox** (80/20 core/alpha NAV stitch + paper `forward/e50_stack/`) that reaches ~**14.9–16.8%** combined CAGR on 2019–2026 overlap — still below the 20% target and **not** merged to `main` as an official engine. E50-A3-R1 remains blocked from A4/promotion by experimental gates (original grid: **0** turnover-feasible candidates; validation loses to PIT proxy; bootstrap 0.26). Expanded turnover challengers on `cursor/e50a3r1-turnover-diagnosis-d049` get OOF turnover under 2.5% but still **`MIXED_HELDOUT`** (validation bootstrap ~0.51–0.56 < 0.70).

---

## Hard blockers vs soft gaps

### Hard blockers (must clear before any honest “connected / promoted” claim)

1. **E50-A promotion gates fail (EXPERIMENTAL, but binding in code)**  
   - A3 / A3-R1 both `decision: RESEARCH_ONLY` (not `ELIGIBLE_FOR_E50_A4`).  
   - R1 original grid: `turnover_feasible_candidates=0` (min OOF turnover ~2.86% > **2.5%** ceiling).  
   - R1 validation CAGR **14.95%** < PIT proxy **20.97%**; validation bootstrap **0.2614** < **0.70**.  
   - Sealed alone looks strong (CAGR **48.01%**, bootstrap **0.9986**) — sealed strength does **not** auto-promote.

2. **Governance: E50-A is EXPERIMENTAL, not an official strategy version**  
   - `FROZEN_GOVERNANCE.md`: E50-A models/grids/thresholds/weights/rebalancing = EXPERIMENTAL; no SOFT_FROZEN class for overlay.  
   - Live-wiring A3-R1 into E21 and calling it the frozen portfolio would violate promotion path.

3. **E45 handoff gate missing / incomplete**  
   - Spec: Alpha must obey E45; R1 README / handoff: **do not integrate E45 until approved overlay-to-crisis handoff**.  
   - Claimed MDD **−13.16%** = `UNVERIFIED_TEXT_ONLY` / **NOT FOUND** in artifacts.  
   - Closest verified lineage MDDs: E1 −17.21%, E1.1 −15.81%, E3 −18.49%, V4.12-D −18.91%.  
   - E45-C1 (sibling): keep **V4.12-D** as crisis baseline; named module = API packaging only (`B_KEEP_D_AS_BASELINE_E45_API_ONLY`).

4. **No production four-layer engine on `main`**  
   - Handoff §2 / §10: combined portfolio (overlay on core, Alpha-off before crisis, E45 handoff) **not implemented as one engine**.  
   - Phase 10 of `E50-A3-R1_TODO.md` (Portfolio Integration) still unchecked.

### Soft gaps (architecture / ops incompleteness; do not by themselves authorize promotion)

1. E16 full-history official NAV missing; live E21 ledger short (~9 signal days at audit).  
2. E22 dividends exist as dataset; not applied inside live E21 NAV (challenger early-stack wires them).  
3. E44 principle implemented inside E18/A3; no isolated `e44` package.  
4. Cash / short-bond sleeve incomplete.  
5. Alpha-weak ≠ crisis is **spec-only** on `main`; state machine only exists in sibling paper stack.  
6. Core alone ~**11–14%** CAGR (E16+E18+E22 early-stack / stock-div challenger) — expected; gap to ≥20% is the overlay’s job, not a bug in E16.

---

## Handling options

### Option A — Docs-only: treat “not connected” as an accepted research status
**Invasiveness:** docs-only  

Keep messaging: attack layer is **ACTIVE RESEARCH / FROZEN ROLE**, not live capital. Do not imply CAGR≥20% is currently attainable from E16 alone. Point operators to handoff warnings and R1 `RESEARCH_ONLY`.  

**Use when:** you need a truthful status answer without changing code.  
**Does not:** raise returns; does not close the architectural gap.

### Option B — Challenger sandbox: NAV-stitch / paper four-layer (already prototyped off-main)
**Invasiveness:** challenger sandbox  

Reuse / land (as EXPERIMENTAL, separate folder) the sibling work:
- `scripts/e50_early_stack_combined_nav.py` — E16+E18+E22(+named E45) historical NAV  
- `scripts/e50_four_layer_combined_nav.py` — 80/20 core + A3-R1 alpha, alpha-cut-first  
- `scripts/e50_stack_forward_pipeline.py` + `forward/e50_stack/` — paper ledger beside E21  

Measured sibling results (overlap 2019-01-02→2026-08-28): static 80/20 **16.80%** CAGR / MDD −23.6%; alpha-cut-first **15.54%**; paper stack **14.88%**. Full core+E45+alpha-cut **11.64%**.  

**Use when:** you need a measurable “connected architecture” without promoting alpha or editing E21.  
**Does not:** clear R1 promotion gates or hit ≥20% with current locked A3-R1 sleeve.

### Option C — Continue alpha research until `ELIGIBLE_FOR_E50_A4`, then sandbox-wire
**Invasiveness:** challenger sandbox (research) → later live wire only after approval  

Clear blockers in order: (1) OOF turnover feasibility, (2) dual held-out beat-proxy + bootstrap≥0.70, (3) MDD toward 10–15% target or explicit risk acceptance, (4) approved EXPERIMENTAL overlay↔E45 handoff gate, (5) combined OOS/cost/stress report, (6) governance review + explicit approval.  

Turnover diagnosis (sibling) shows portfolio-rule search around TECH2 saturates at **`MIXED_HELDOUT`**; next leverage is **failure-regime / stress-sleeve** research (Stage-8A/B), not more reb/exit micro-tunes, and **not** relaxing HARD_FROZEN clock/PIT.

### Option D — Live wire into E21 now
**Invasiveness:** live wire  

**Not recommended.** Would mix EXPERIMENTAL alpha + unverified E45 handoff into SOFT_FROZEN path without promotion evidence; handoff explicitly forbids performance tuning / E45 integrate until overlay gate exists; sealed-window strength would look like a fake “fix.”

---

## Recommended path (technical steps only)

1. **Freeze the status language:** “E50-A attack layer not connected” = correct for `main`; architecture roles exist; capital book does not.  
2. **Do not live-wire.** Prefer Option B sandbox if a combined NAV demonstration is required.  
3. **Finish / land turnover + held-out diagnosis artifacts** from `cursor/e50a3r1-turnover-diagnosis-d049` into a readable challenger folder (C2/C4/C8 `MIXED_HELDOUT`; validation bootstrap remains the hard experimental blocker).  
4. **Run Stage-8A failure-signature diagnosis** (bad months ≠ EW crisis flags) before another portfolio-rule grid.  
5. **Only after an OOF dual-gate stress winner:** one held-out evaluation; still no E45 retune.  
6. **Define EXPERIMENTAL overlay↔E45 handoff** as a separate challenger (numeric gates remain EXPERIMENTAL until approved); keep E45-C1 decision B (D baseline, E45 API-only).  
7. **Combined book experiment** (Option B metrics): report incremental benefit vs E16+E18+E22 core, TC impact, Alpha-off/Core-on behavior — required by TODO Phase 10 / promotion path.  
8. **Promotion to live** only after: `ELIGIBLE_FOR_E50_A4` (or successor) + OOS/cost/stress + governance review + explicit approval → new frozen version beside prior baseline.

---

## Key file paths and numbers

### Governance / roles
| Path | Role |
|---|---|
| `/workspace/FROZEN_STRATEGY_SPEC.md` | E50-A = Alpha Overlay; status ACTIVE RESEARCH / FROZEN ROLE; current research E50-A3-R1; target CAGR≥20%, MDD~10–15% |
| `/workspace/FROZEN_GOVERNANCE.md` | E16/E18/E22/E45 SOFT_FROZEN; E45 SOFT_FROZEN_CRITICAL; E50-A3/R1 + all numeric gates EXPERIMENTAL |
| `/workspace/E50_HANDOFF_VERIFICATION.md` | `HANDOFF_COMPLETE_WITH_WARNINGS`; four-layer not wired |
| `/workspace/E50-A3-R1_TODO.md` | Phase 6–10 open; Phase 10 Portfolio Integration unchecked |
| `/workspace/HANDOFF.md` | Architecture + research order |

### E50-A research (this branch / main artifacts)
| Path | Key numbers |
|---|---|
| `/workspace/research/e50a3/README.md` | A3 baseline; E45 deliberately not applied; next gate A4 under E45 multiplier |
| `/workspace/research/e50a3r1/README.md` | 2.5% turnover ceiling; beat proxy + bootstrap 0.70; E45 untouched until overlay handoff |
| `/workspace/scripts/e50a3_train_exact_open.py` | A3 trainer; promotion → `ELIGIBLE_FOR_E50_A4` |
| `/workspace/scripts/e50a3r1_repair.py` | R1 repair; `turnover_feasible <= 0.025`; dual beat-proxy + bootstrap≥0.70 |
| `/workspace/repro/e50a3r1-audit-20260903/outputs/a3r1/qc_status.json` | `RESEARCH_ONLY`; turnover_feasible_candidates=0 |
| R1 VALIDATION | CAGR **14.95%**, MDD **−33.50%**, turnover **7.05%**, bootstrap **0.2614** |
| R1 SEALED | CAGR **48.01%**, MDD **−32.51%**, turnover **4.68%**, bootstrap **0.9986** |
| R1 vs proxy (val) | 14.95% vs **20.97%** (fails beat-proxy) |
| A3 VALIDATION / SEALED | CAGR **1.44%** / **22.26%**; MDDs −27.94% / −21.37% |
| Train grid (72 cells) | min OOF turnover **2.86%**; feasible **0** |
| Exposure summary | mean daily turnover **5.93%**; max day **1.99** |

### Core CAGR reference (~11–14%)
| Path | Numbers |
|---|---|
| Early-stack sibling `E16_E18` | CAGR **7.22%**, MDD −22.8% (no E22) |
| Early-stack `E16_E18_E22` | CAGR **11.19%**, MDD −22.1% |
| `/workspace/repro/e22-stock-div-nav-compare/summary.json` | cash-only **11.25%**; cash+stock **13.78%** |

### Combined engine status
| Location | Status |
|---|---|
| `main` / this branch | `e50_early_stack_combined_nav.py` + `e45_crisis_core.py` present; **no** `e50_four_layer_*`, **no** `forward/e50_stack/` |
| Sibling `cursor/early-stack-combined-nav-d049` | Four-layer sandbox + paper stack; `IMPLEMENTED_IN_CHALLENGER_SANDBOX` only |
| Four-layer MIX_STATIC_80_20 | CAGR **16.80%**, MDD −23.62% |
| Four-layer MIX_ALPHA_CUT_FIRST | CAGR **15.54%**, MDD −23.13% |
| Paper `forward/e50_stack/` | CAGR **14.88%**, MDD −23.13%; states ALPHA_WEAK 926 / NORMAL 470 / CRISIS 455 |

### Turnover diagnosis sibling (not fully on this branch)
| Path (on `cursor/e50a3r1-turnover-diagnosis-d049`) | Result |
|---|---|
| Locked C1 `reb42 exit2.0` | Val turn FAIL, boot 0.514 → `MIXED_HELDOUT` |
| C2 / C4 / C8 | Val turn often PASS; val boot ~0.55–0.56 → still `MIXED_HELDOUT` |
| Stage-10 stress sleeves | Repeated `MIXED_HELDOUT`; portfolio-rule search saturated |
| Next plan | Stage-8A failure signature (alpha stress ≠ EW crisis) |

### Scripts needed to wire overlay (inventory)
| Script | On this branch? | Purpose |
|---|---|---|
| `scripts/e50a0_*` … `e50a2_*` | Yes | PIT / causal / factors (HARD contracts) |
| `scripts/e50a3_train_exact_open.py` | Yes | Alpha sleeve train/sim |
| `scripts/e50a3r1_repair.py` | Yes | Repair + promotion gates |
| `scripts/e50_early_stack_combined_nav.py` | Yes | Core+exec(+E45 cand.) historical NAV |
| `scripts/e45_crisis_core.py` | Yes | Named E45 API (not promoted) |
| `scripts/e50_four_layer_combined_nav.py` | **No** (sibling) | Stitch core+alpha NAV books |
| `scripts/e50_stack_forward_pipeline.py` | **No** (sibling) | Paper forward four-layer ledger |
| `scripts/e21_forward_pipeline.py` | Yes | Live SOFT_FROZEN core — **do not edit in place for overlay** |

---

## Bottom line

“E50-A attack layer not connected” is the **correct operational fact** on `main`: overlay role is frozen in docs; the **model is unpromoted research** and the **combined capital book is absent from live**. Connecting it for real return lift requires clearing experimental alpha gates (turnover + validation excess stability), defining an approved E45 handoff without inventing −13.16%, and running a challenger combined book — **not** patching E21. Sibling sandboxes already show a connected 80/20 book tops out ~**15–17%** CAGR with current A3-R1; the ≥20% / MDD 10–15% target remains unmet.
