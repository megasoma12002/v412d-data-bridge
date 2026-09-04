# Stage-12 Summary — All Open Optimization Options

Date: 2026-09-04  
Detector locked: S9A1 `COMBO_VOL70_VAL03` (no retune)  
**No E45 in-place edit. No gate promotion.**

## Tracks

| Track | Idea | OOF dual-gate winner | Held-out |
|---|---|---|---|
| **A** Asymmetric freeze | EXIT_ONLY / SOFT_GAP / HALF_ADD / FULL_FREEZE | **HALF_ADD** | `MIXED_HELDOUT` — val ≈ **identical to C4** |
| **B** Dual-account | cash / DEF / sleeve capital splits | **DUAL_80_20_SLEEVE** | `MIXED_HELDOUT` — val boot 0.560 ≈ C4; stress slightly ↑ |
| **C** Stress-weighted TECH2 | fit weights ×2/3/5 on stress days ± EXIT_ONLY | **none** (all boot fail) | — |
| **D** New-info features | amihud velocity, turn collapse, rev vs industry, micro | **none** (no stress-beating dual-gate) | — |
| **E** Governance | update recommendation after A–D | — | see below |

## Detail notes

### A — Asymmetric freeze
- `HALF_ADD` barely beats BASE on OOF (stress_ex 6.0e-5 vs 3.6e-5; util almost equal).
- On validation it **collapses to C4** (same CAGR/MDD/boot/stress) → stress rebalance days too sparse for the asymmetry to matter held-out.
- Full freeze OOF boot 0.69 (fail) under this score path; prior S9A1 walk-forward path remains the freeze reference.

### B — Dual-account
- Cash splits help util on OOF but kill bootstrap or stress.
- Fixed 80/20 with sleeve-B passes OOF gates marginally; held-out still MIXED and nearly C4-like.

### C — Stress-weighted training
- Higher stress loss weight **hurts** OOF bootstrap across the board.
- Not a viable TECH2 repair under current gates.

### D — New-info
- Full new-info books are toxic (boot ≈ 0.01–0.26).
- As stress sleeves, some pass gates but **do not beat BASE stress PnL**.
- Velocity / industry-relative constructions from the same panel are not enough “new information.”

## Ranking after Stage-12

| Rank | Object | Why |
|---|---|---|
| 1 | **S9A1** (prior) | Best MIXED overlay; Stage-11 val stress MC ≈ 0.95 vs C4 |
| 2 | C4 bull sleeve | Reference engine |
| 3 | S12B dual / S10R3 | Marginal / fragile |
| — | S12A HALF_ADD, Track C/D | No held-out edge |

## Track E — Governance update

Label remains: **`GOVERNANCE_REVIEW_READY_NO_AUTO_PROMOTE`**

Human options unchanged, with stronger evidence:

1. **C4-only** research reference  
2. **Paper/monitor S9A1** as MIXED operational overlay (still best after open-option search)  
3. **Require information outside current A2 panel** before more alpha work  

Agents should not restart remix / asymmetric / dual / stress-weight grids on this panel pending (2) or (3).

Artifacts: `E50-A3-R1_STAGE12_OPEN_OPTIONS.md`, `reports/stage12_open_options_summary.json`, `outputs/stage12_open_options_oof_grid.csv`.
