# E50-A3-R1 Locked Challenger Held-Out Evaluation

Date: 2026-09-03  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049`  
Sandbox: `repro/e50a3r1-turnover-diagnosis-20260903/`

## Project status

- E50 Handoff: **COMPLETE** (`HANDOFF_COMPLETE_WITH_WARNINGS`)
- Current stage: **E50-A3-R1 repair and held-out validation**
- Frozen baselines: **UNCHANGED**
- This run is normal research continuation, not handoff work

## Locked challenger (selected on 2011–2018 OOF only)

```
TECH2 / BREADTH_REGIME / lambda=1.0
top_k=20
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
liquidity_floor=NT$20m
```

No retuning on 2019–2022 or 2023-latest.  
2.5% turnover and 0.70 bootstrap remain **EXPERIMENTAL**.

## Results

| Window | CAGR | MDD | Avg daily turnover | Total cost | vs PIT proxy | Bootstrap | Turnover gate | Bootstrap gate |
|---|---:|---:|---:|---:|---|---:|---|---|
| OOF 2011–2018 (reconfirm) | 10.04% | -30.07% | **2.20%** | 0.201 | — | **0.767** | PASS | PASS |
| Validation 2019–2022 | **21.46%** | -28.47% | 2.69% | 0.159 | beats 20.97% | 0.514 | FAIL | FAIL |
| Sealed 2023–latest | **60.95%** | -22.86% | **1.73%** | 0.110 | beats 20.99% | **1.000** | PASS | PASS |

R1 selected reference (reb=5, failed OOF turnover) for context:

| Window | CAGR | MDD | Turnover | Bootstrap | Beats proxy |
|---|---:|---:|---:|---:|---|
| Validation 2019–2022 | 14.95% | -33.50% | 7.05% | 0.261 | NO |
| Sealed 2023–latest | 48.01% | -32.51% | 4.68% | 0.999 | YES |

## Research decision

**EXPERIMENTAL_HELDOUT_FAIL_OR_INCOMPLETE**

Why:

1. Validation turnover **2.69% > 2.5%** (narrow miss).
2. Validation bootstrap **0.514 < 0.70** (does not clear the experimental acceptance threshold).
3. Sealed window clears turnover, bootstrap, and beats proxy — but sealed strength alone cannot promote under the existing experimental R1 discipline.
4. MDD remains far from the long-term ~10–15% band (OOF -30%, validation -28%, sealed -23%).

Positive research signal (not a promotion):

- Locked challenger improves validation vs the old R1 selected reference: higher CAGR, better MDD, much lower turnover, and beats the PIT proxy where R1 selected did not.
- Sealed remains strong after the turnover repair.

## What was not done

- No freeze / promotion
- No E45 integration
- No edit to E16 / E18 / E22 / E44 / E45
- No A0/A1/A2 rebuild
- No held-out retuning

## Smallest safe next research step

Do **not** retune on 2019–2022.

Next challenger should target validation turnover stability and/or validation excess robustness while keeping OOF dual-gate discipline, for example:

1. Keep reb=42 locked from OOF, test a slightly wider exit buffer or mild min-hold **selected only on OOF**, then re-check held-out once.
2. Or diagnose why validation name churn (one-way ≈ 0.54) exceeds OOF/sealed churn, without reading sealed results into selection.
3. MDD repair remains a later separate challenger after experimental turnover/bootstrap gates are stable.

Artifacts:

- `outputs/heldout_period_metrics.csv`
- `outputs/locked_validation_2019_2022_*.csv`
- `outputs/locked_sealed_2023_latest_*.csv`
- `reports/heldout_decision.json`
