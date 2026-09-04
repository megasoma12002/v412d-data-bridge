# Early-Stack Combined NAV + Named E45 Module

**EXPERIMENTAL.** Named E45 exists but is **not** promoted to SOFT_FROZEN_CRITICAL.

Module: `scripts/e45_crisis_core.py` — `CHALLENGER_CANDIDATE_NOT_PROMOTED`

## Results

| Variant | CAGR | MDD | Util | Mean E45 exp |
|---|---:|---:|---:|---:|
| E16_E18 | 7.22% | -22.77% | -0.0417 | 1.0 |
| E16_E18_E22 | 11.19% | -22.11% | 0.0013 | 1.0 |
| E16_E18_E22_E45LEGACY | 10.39% | -20.13% | 0.0032 | 0.9621194029850746 |
| E16_E18_E22_E45_E3 | 8.59% | -20.53% | -0.0168 | 0.9068070573269436 |
| E16_E18_E22_E45_E1 | 10.67% | -22.11% | -0.0039 | 0.9935820895522388 |

- E22 CAGR lift: `3.9681%`
- E45-E3 MDD delta vs E22: `1.5799%`
- Claimed MDD -13.16%: `UNVERIFIED_TEXT_ONLY`

## Decisions

- `e16_full_history_reconstruction`: DONE_IN_CHALLENGER
- `e22_wired_into_nav_copy`: DONE_IN_CHALLENGER
- `e45_named_module`: CREATED_CHALLENGER_CANDIDATE
- `e45_promoted_to_soft_frozen_critical`: False
- `e45_mdd_claim_13_16`: NOT_FOUND_IN_ARTIFACTS
- `combined_four_layer_engine`: CORE_EXEC_DIV_PLUS_NAMED_E45_CANDIDATE
- `next`: Named module scripts/e45_crisis_core.py exists and is wired. Still NOT promoted. Promote only via higher-bar challenger vs V4.12-D + explicit governance approval.

See `research/e45/E45_MODULE_STATUS.md`.
