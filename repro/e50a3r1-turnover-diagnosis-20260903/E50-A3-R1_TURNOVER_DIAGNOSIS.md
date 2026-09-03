# E50-A3-R1 Turnover Diagnosis

Date: 2026-09-03  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049`  
PR: https://github.com/megasoma12002/v412d-data-bridge/pull/19  
Sandbox: `repro/e50a3r1-turnover-diagnosis-20260903/`

Constraints kept:

- E16 / E18 / E22 / E44 / E45 unchanged
- A0 / A1 / A2 pinned (not rebuilt)
- Exact T+1 simulator unchanged (`e50a3_train_exact_open.simulate`)
- 2.5% OOF turnover ceiling = **EXPERIMENTAL**
- 0.70 bootstrap cutoff = **EXPERIMENTAL**
- Selection / diagnosis window = **2011–2018 OOF only**
- 2019–2022 and 2023-latest were **not** used to select parameters

Model under diagnosis: pre-selected R1 family `TECH2` / `BREADTH_REGIME` / `lambda=1.0` (train CV only).

---

## Root Causes

1. **Rebalance frequency is the binding constraint.**  
   On the current R1 grid, mean OOF turnover falls from 8.76% (reb=5) → 6.04% (reb=10) → 4.13% (reb=21). The lowest current-grid cell is still **2.86%** (`top_k=30`, `rebalance_every=21`, `exit_multiple=2.0`).  
   Approximate identity: `avg_daily_turnover ≈ (two-way rebalance-day turnover) / rebalance_every`.  
   At reb=21 that requires average rebalance-day two-way turnover ≲ 52.5% to clear 2.5%. The best current cell still spends ~60% NAV two-way per rebalance day.

2. **The selected utility cell over-trades relative to signal persistence.**  
   Selected R1 config (`top_k=20`, reb=5, exit=2.0) has OOF turnover **5.77%**, total cost **0.528**, bootstrap **0.851** (already above 0.70). It fails only the turnover gate.  
   Score rank autocorr every 5 sessions ≈ **0.84** median ~0.95, so rebalancing every 5 sessions repeatedly pays costs against a slowly changing signal.

3. **Rank-buffer width inside the current grid is insufficient at monthly cadence.**  
   Wider exit multiples cut turnover (mean 7.31% at 1.25x → 5.17% at 2.0x), but even exit=2.0 at reb=21 leaves **640 forced rank exits** and one-way name churn ≈ **0.31**. Exit multiples stop at 2.0 in the frozen R1 search grid.

4. **Universe / liquidity churn is not the main driver.**  
   Eligible-universe Jaccard at NT$20m ≈ **0.88** (stable). Liquidity/missing exits exist, but forced rank exits dominate at the current-grid low-turnover corner (640 rank exits vs 215 liquidity/missing).

5. **Equal-weight top-k mechanics amplify name swaps into turnover.**  
   Every replaced name moves weight `1/top_k` out and another `1/top_k` in (two-way). At top_k=20 that is 10% two-way NAV per replaced name before costs.

6. **Transaction-cost interaction.**  
   Current selected cell total cost 0.528 over 2011–2018 vs 0.230 for the lowest-turnover current-grid cell. High turnover is not free alpha on OOF; it is the reason the experimental feasibility gate blocks promotion even when OOF bootstrap looks strong.

7. **Not primarily score white-noise.**  
   5-session rank autocorr is high. The failure mode is **calendar overtrading + insufficient buffer span inside the current grid**, not random score flicker.

---

## Candidate Fixes

All EXPERIMENTAL. Implemented only inside `scripts/e50a3r1_turnover_diagnosis.py` (challenger tooling). No frozen baseline edited.

| Family | What changed | Causal? | Exact T+1 preserved? |
|---|---|---|---|
| `reb_buffer_expand` | `rebalance_every` ∈ {21,42,63}; `exit_multiple` ∈ {2,3,4,5}; `top_k` ∈ {20,30,40} | Yes — still T-close signal → next open | Yes |
| `min_hold` | Require N rebalance cycles before rank-exit | Yes — uses only past hold age | Yes |
| `liquidity_floor` | NT$50m / NT$100m filters | Yes — T trading_money only | Yes |
| `replace_rank_gap` | Admit new names only with rank advantage | Yes — T ranks only | Yes |
| `neutralization` | INDUSTRY_LIQUIDITY at low-turnover corners | Yes — T industry/liquidity | Yes |

Current-grid references were re-measured on the same OOF scores for calibration.

---

## 2011-2018 OOF Results

Challenger screen: **61** unique cells.

| Metric | Result |
|---|---|
| Turnover ≤ 2.5% | **49 / 61** |
| Bootstrap ≥ 0.70 | **4 / 61** |
| Both gates | **1 / 61** |

Selected-model OOF references:

| Cell | Turnover | CAGR | MDD | Total cost | Bootstrap | Gates |
|---|---:|---:|---:|---:|---:|---|
| Selected utility (20/5/2.0) | 5.77% | 10.96% | -32.55% | 0.528 | 0.851 | turnover FAIL / boot PASS |
| Lowest current-grid (30/21/2.0) | 2.86% | 6.61% | -33.60% | 0.230 | 0.476 | both FAIL |

---

## Turnover Results

- Current R1 grid: **0 / 72** feasible (`turnover_feasible=false` for every cell).
- Extending rebalance to **42** is the first structural move that clears 2.5% while retaining usable OOF return.
- Extremely slow books (reb=63, exit=5.0) can push turnover to ~0.28%, but destroy excess (bootstrap ~0.01).
- Min-hold and replace-gap helped little beyond what reb=42 already provides; they mostly duplicated the reb=42/exit=2.0 turnover profile.
- Higher liquidity floors reduced turnover modestly but did not create an additional both-gate winner.

Passing turnover examples (OOF):

| top_k | reb | exit | Turnover | Bootstrap | Both? |
|---:|---:|---:|---:|---:|---|
| 20 | 42 | 2.0 | **2.20%** | **0.767** | **YES** |
| 30 | 42 | 2.0 | 1.97% | 0.572 | no |
| 20 | 42 | 3.0 | 1.76% | 0.590 | no |
| 30 | 21 | 3.0 + 100m liq | 1.60% | 0.402 | no |
| 30 | 63 | 5.0 | 0.28% | 0.011 | no |

---

## Cost Impact

| Cell | Total cost (OOF) | Trades | Notes |
|---|---:|---:|---|
| Selected utility 20/5/2.0 | 0.528 | 8996 | blocked by turnover |
| Lowest current-grid 30/21/2.0 | 0.230 | 3670 | still above 2.5% |
| Recommended 20/42/2.0 | **0.201** | 1385 | clears turnover; cost ≈ 38% of selected cell |

Lower turnover mechanically reduces commission/tax/slippage drag inside the unchanged Exact T+1 cost contract (14.25bp / 30bp tax / 5bp slip).

---

## Bootstrap Results

Block bootstrap = 21-session blocks, positive mean excess vs PIT market proxy (same helper as A3/R1).

- Selected high-turnover cell already has OOF bootstrap **0.851** — alpha signal is not absent; it is too expensive under the turnover ceiling.
- Stretching rebalance/buffer too far kills excess (many turnover-pass cells have bootstrap 0.01–0.60).
- Only **4** challenger cells cleared bootstrap ≥ 0.70; only **1** also cleared turnover.

---

## Candidates Passing Both Gates

Exactly one OOF candidate:

| Field | Value |
|---|---|
| family | `reb_buffer_expand` |
| top_k | 20 |
| rebalance_every | **42** |
| exit_multiple | 2.0 |
| neutralization | NONE |
| industry_cap | 5 |
| min_hold_cycles | 0 |
| liquidity_floor | 20,000,000 |
| replace_rank_gap | 0 |
| OOF avg daily turnover | **2.195%** ≤ 2.5% |
| OOF bootstrap | **0.767** ≥ 0.70 |
| OOF CAGR | 10.04% |
| OOF MDD | -30.07% |
| OOF total cost | 0.201 |
| OOF utility | -0.050 |

Governance: this configuration is **EXPERIMENTAL**. It is not frozen. It was not selected using 2019+ data.

---

## Recommended Challenger

**Recommended next challenger (EXPERIMENTAL):**

`top_k=20`, `rebalance_every=42`, `exit_multiple=2.0`, `neutralization=NONE`, `industry_cap=5`, liquidity floor NT$20m, no min-hold, no replace-gap.

Why:

1. Only cell that passes **both** experimental OOF gates.
2. Cuts OOF turnover from 5.77% (selected) / 2.86% (best current-grid) to 2.20%.
3. Cuts OOF total cost from 0.528 to 0.201.
4. Keeps causal clock, pinned datasets, and Exact T+1 unchanged.
5. Does not touch E16 / E18 / E22 / E45.

Admissible next step (not executed in this PR):

- Evaluate this single frozen-at-selection challenger on 2019–2022 and 2023-latest **after** OOF selection is locked.
- Do not retune on those windows.
- Keep 2.5% and 0.70 EXPERIMENTAL unless explicitly promoted later.

Artifacts:

- `reports/root_cause_diagnostics.json`
- `outputs/oof_challenger_grid.csv`
- `reports/oof_challenger_summary.json`
- `outputs/oof_scores_selected_model.parquet`
