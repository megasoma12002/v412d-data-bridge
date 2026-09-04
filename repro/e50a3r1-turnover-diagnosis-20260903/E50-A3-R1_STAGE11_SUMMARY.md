# Stage-11 Summary — E45-C1 Monte Carlo Governance Package

Date: 2026-09-04  
Label: **`GOVERNANCE_REVIEW_READY_NO_AUTO_PROMOTE`**  
Suggested mixed overlay for human review: **S9A1** (FREEZE_REB × COMBO_VOL70_VAL03)

## What this stage is

Not another feature/controller grid. Per operating rules, after held-out comes **Stress / Monte Carlo → Governance review**.

Compared **locked** configs only:

| ID | Role |
|---|---|
| C4 | Bull sleeve reference (TECH2+C4) |
| S9A1 | Freeze-rebalance on S9A1 detector |
| S10R3 | Residual SAFE4 stress sleeve on same detector |

5000× block-21 path draws. No retune. No E45 in-place edit. No gate promotion.

## Headline MC (validation 2019–2022)

| vs C4 | P(better MDD) | P(better util) | P(better stress mean) | P(better stress compound) |
|---|---:|---:|---:|---:|
| **S9A1** | **0.73** | **0.66** | **0.94** | **0.95** |
| S10R3 | 0.29 | 0.50 | 0.73 | 0.72 |

S9A1 also has higher point CAGR/util/boot than C4 on validation (still **below** EXPERIMENTAL 0.70 boot gate → remains `MIXED`).

## Sealed caveat

On 2023–latest, S9A1 beats C4 on util/returns (MC util 0.89, mean_ret 0.97) but **loses** MDD/stress MC (stress regimes differ). S10R3 sealed stress MC ≈ 0 — not preferred.

## Governance options (human)

1. Keep **C4-only** as research reference; overlays stay EXPERIMENTAL documentation  
2. Paper/monitor **S9A1** as MIXED operational overlay — **not** frozen / not E45 replacement  
3. Block further work until a **new information set** exists  

## Stop line for agents

- Do not retune S9A1/S10R3/C4 after this package  
- Do not promote 0.70 / 2.5% gates  
- Do not edit E45 in place  
- Do not restart panel `pct_*` remix grids awaiting governance

Artifacts: `E50-A3-R1_STAGE11_E45C1_MONTE_CARLO.md`, `reports/stage11_e45c1_monte_carlo_summary.json`.
