# E50-A3-R1 Turnover / Held-Out Diagnosis — Closeout

Date: 2026-09-04  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049` (PR #19)  
Status: **DIAGNOSIS COMPLETE** — research only; no live wire; no gate promotion.

Answers the Gap #5 question: *can any candidate meet the turnover ceiling without sealed peeking, and what happens on held-out?*

---

## Executive verdict

| Question | Answer |
|---|---|
| Original R1 grid meet TO ≤2.5%? | **No** — `turnover_feasible_candidates = 0` (min OOF TO ~2.86%) |
| Any OOF challenger meet TO **without** sealed peeking? | **Yes** — extend `rebalance_every` to **42** (and similar slow books) |
| Both OOF gates (TO + bootstrap≥0.70)? | **Yes, exactly 1 / 61** at first screen: `top_k=20`, `reb=42`, `exit=2.0` |
| Held-out dual-gate pass (val **and** sealed)? | **No** — pattern is **`MIXED_HELDOUT`** across C1/C2/C4/C8 and later stages |
| Promote / live-wire? | **`STILL_NO` / `RESEARCH_ONLY`** |

Root cause of original R1 block: **calendar overtrading** (reb=5 vs high rank autocorr), not white-noise scores.  
Root cause of held-out failure after TO fix: **validation excess unstable** (bootstrap ~0.51–0.56), while sealed looks strong — classic sealed-cherry risk if promoted.

---

## 1. Turnover diagnosis (OOF 2011–2018 only)

Constraints: Exact T+1 unchanged; E45 untouched; selection never used 2019+.

### Original R1

| Item | Value |
|---|---|
| Selected cell | TECH2 / BREADTH_REGIME / λ=1 / top_k=20 / reb=5 / exit=2.0 |
| Train / OOF TO | ~5.8% |
| Current grid feasible | **0 / 72** |
| Decision | `RESEARCH_ONLY` |

### Challenger screen (`e50a3r1_turnover_diagnosis.py`)

| Metric | Result |
|---|---|
| Cells | 61 |
| TO ≤ 2.5% | **49** |
| Bootstrap ≥ 0.70 | **4** |
| **Both gates** | **1** |

**Both-gate winner (OOF):**

| Field | Value |
|---|---|
| Config | top_k=20, **reb=42**, exit=2.0 |
| OOF TO | **2.20%** |
| OOF bootstrap | **0.767** |
| OOF CAGR / MDD | 10.04% / −30.07% |

Binding lever: **rebalance frequency**. Min-hold / replace-gap / liq floors are secondary.

Artifact: `E50-A3-R1_TURNOVER_DIAGNOSIS.md`, `reports/oof_challenger_summary.json`

---

## 2. Held-out evaluation (locked; no retune)

Locked OOF winners → one-shot val (2019–2022) + sealed (2023–latest).

| Challenger | OOF both? | Val TO | Val boot | Sealed boot | Decision |
|---|---|---:|---:|---:|---|
| C1 (20/42/2.0) | Yes | 2.69% FAIL | 0.51 FAIL | 1.00 PASS | **MIXED_HELDOUT** |
| C2 | Yes | ~2.43% | 0.51 | 1.00 | **MIXED_HELDOUT** |
| C4 (research baseline) | Yes | ~2.19% | 0.56 | 0.998 | **MIXED_HELDOUT** |
| C8 | Yes | ~2.18% | 0.55 | 0.998 | **MIXED_HELDOUT** |

C1 detail (also beats proxy on both windows, but **val bootstrap fails**):

| Window | CAGR | MDD | TO | Boot | Beats proxy |
|---|---:|---:|---:|---:|---|
| Val | 21.5% | −28.5% | 2.69% | **0.514** | Yes |
| Sealed | 61.0% | −22.9% | 1.73% | **1.000** | Yes |

**Interpretation:** Clearing turnover on OOF is **necessary but not sufficient**. Validation excess is fragile; sealed strength must not drive promotion.

---

## 3. Later stages (saturation map)

| Stage | Result |
|---|---|
| TECH2 / feature / crisis cash grids | No lasting dual-gate held-out win |
| Failure mode | Bad months ≠ EW crisis flags (alpha underperformance in RISK_ON) |
| Option 2 governance | C4 research baseline; **S9A1** paper/monitor (`MIXED`); E45 unchanged |
| Stage-13 adversarial | Option-2 **kept with caveats** (WOUNDED) |
| Auto-iterate causal S9A1C | **STOPPED** at adv-lite (`STOP_ADV_FALSIFIED`) |

---

## 4. Gap #5 implications

1. Live overlay **correctly disconnected**.
2. Turnover block is **repairable on OOF** via slower rebalance — not by relaxing Exact T+1 / PIT.
3. Held-out still blocks promotion: **`MIXED_HELDOUT`** / val bootstrap.
4. Do **not** promote 2.5% or 0.70 gates to “make it pass.”
5. Next alpha work (if any): failure-signature / stress-sleeve track already opened (Stage-8+), not another reb micro-grid — and **not** live-wire.

---

## 5. Explicit non-goals (still)

- No `forward/e21` overlay allocation  
- No E45 in-place edit  
- No post-held-out cut retune  
- No PR merge as production strategy  

---

## Artifacts

| Path | Role |
|---|---|
| `E50-A3-R1_TURNOVER_DIAGNOSIS.md` | OOF root cause + challenger screen |
| `reports/oof_challenger_summary.json` | 61-cell OOF summary |
| `reports/heldout_decision.json` | C1 held-out |
| `reports/c2|c4|c8_heldout_decision.json` | MIXED_HELDOUT family |
| `E50-A3-R1_NEXT_STEP_PLAN.md` | Post Stage-7 plan |
| `E50-A3-R1_AUTO_ITERATE_CAUSAL_S9A1C.md` | Axis-0 stop |
| `reports/governance_decision_option2.json` | Option-2 accept |
| This file | Gap #5 diagnosis closeout |

## Decision label

`TURNOVER_HELDOUT_DIAGNOSIS_COMPLETE__RESEARCH_ONLY__NO_LIVE_WIRE`
