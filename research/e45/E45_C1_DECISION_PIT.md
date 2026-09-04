# E45-C1 Decision Package

Date: 2026-09-04  
Panel: reconstructed 12-stock raw OHLCV from E50-A0 PIT (**not** original v412e0 artifact)  
Signal: FormalRouter locks family=1, reb=21, top_n=2, lock=75

## Recommendation: `B_KEEP_D_AS_BASELINE_E45_API_ONLY`

E3 helps drawdown in places but fails return/Sharpe floor vs D on this panel. Keep V4.12-D as formal crisis baseline; named E45 remains API packaging.

## Verified MDDs (this panel)

| Strategy | Validation MDD | Full MDD |
|---|---:|---:|
| D_FORMAL_ROUTER | -0.24420344363544344 | -0.6125073766138477 |
| E45_E3_VOLTARGET_WINNER | -0.20215011369699898 | -0.39507836803120067 |
| E45_E1_BINARY | -0.23556478105543432 | -0.43676731525700685 |

Handoff claim MDD ≈ −13.16%: still **`UNVERIFIED_TEXT_ONLY`** (not found as matching artifact).

## Checks vs D

```json
{
  "e3_val_mdd_better": true,
  "e3_val_ret_ge_80pct_d": false,
  "e3_val_sharpe_ge_d": false,
  "e3_full_mdd_better": true,
  "e3_crisis_mdd_better": true,
  "e1_val_mdd_better": true,
  "mc_e3_p_better_mdd_val": 0.9925,
  "mc_e3_p_better_mdd_full": 0.997
}
```

## Monte Carlo P(better MDD vs D)

```json
{
  "E45_E3_VOLTARGET_WINNER": {
    "p_better_mdd_full": 0.997,
    "p_better_mdd_validation": 0.9925
  },
  "E45_E1_BINARY": {
    "p_better_mdd_full": 0.9265,
    "p_better_mdd_validation": 0.647
  }
}
```

## Options

- **A** — Promote E3 profile as `E45_v1` after explicit approval; retire −13.16% text; publish verified MDD from this (or original) panel.
- **B** — Keep **V4.12-D** as crisis baseline; named `e45_crisis_core.py` stays API / packaging only.
- **C** — Reject promotion; leave `CHALLENGER_CANDIDATE_NOT_PROMOTED`.

## Explicit non-actions

- No in-place SOFT_FROZEN_CRITICAL edit
- No retune of E3 winner parameters
- No claim that reconstructed PIT panel equals the original E3 research panel

Artifacts: `reports/e45_verified_baseline.json`, `outputs/e45c1_window_metrics.csv`
