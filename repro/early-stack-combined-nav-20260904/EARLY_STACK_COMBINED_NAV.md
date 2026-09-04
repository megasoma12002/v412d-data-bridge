# Early-Stack Combined NAV Challenger

**EXPERIMENTAL sandbox.** Does not edit E16 / E18 / E22 / E45 SOFT_FROZEN baselines.

## What this closes

1. **E16 full-history causal reconstruction** from `forward/e21/live_market.csv`
2. **E18 Exact T+1** open fills on the reconstructed book
3. **E22 dividends** credited on `cash_ex_date` into a NAV *copy*
4. **E45 verification** of the −13.16% MDD claim + lineage inventory
5. **E45PROXY** (challenger only): scale equity sleeve weights on E16 `Crisis` days

## Results

| Variant | CAGR | MDD | Util | Vol | Div cash |
|---|---:|---:|---:|---:|---:|
| E16_E18 | 7.22% | -22.77% | -0.0417 | 14.01% | 0 |
| E16_E18_E22 | 11.19% | -22.11% | 0.0013 | 13.30% | 2,611,581 |
| E16_E18_E22_E45PROXY | 10.39% | -20.13% | 0.0032 | 12.18% | 2,354,240 |

- E22 CAGR lift vs E16+E18: `3.9681%`
- E45PROXY MDD change vs E16+E18+E22: `1.9813%`

## E45 verification

- Official `e45` module paths: **none**
- Handoff claim MDD ≈ −13.16%: **`NOT_FOUND_IN_ARTIFACTS`**
- Lineage MDDs: E1 `-17.21%`, E1.1 `-15.81%`, E3 `-18.49%`
- Research decision: `{'formal_strategy': 'V4.12-D', 'E2': 'validation_fail', 'E2.1': 'validation_fail', 'E3': 'validation_pass_but_not_promoted', 'reason': 'E3 improves volatility and some drawdowns, but later OOS return and Sharpe superiority over frozen D are inconsistent and transaction-cost drag remains material', 'blind_opened_after_E3_validation_pass': True, 'parameter_selection_used_2023_2026': False}`

## Decisions

- `e16_full_history_reconstruction`: DONE_IN_CHALLENGER
- `e22_wired_into_nav_copy`: DONE_IN_CHALLENGER
- `e45_official_module`: STILL_MISSING
- `e45_mdd_claim_13_16`: NOT_FOUND_IN_ARTIFACTS
- `combined_four_layer_engine`: PARTIAL_CORE_EXEC_DIV_PLUS_PROXY
- `next`: Keep this sandbox as the Phase-10 integration baseline. Do not promote E45PROXY. Official E45 still requires a named module and verified baseline artifact before any SOFT_FROZEN_CRITICAL challenger.

## Explicit non-actions

- No in-place edit of E21 ledgers or `e21_forward_pipeline.py`
- No promotion of E45PROXY to SOFT_FROZEN_CRITICAL
- No A3-R1 overlay merge in this pass (core stack first)

Artifact: `reports/early_stack_combined_nav_summary.json`
