# Four-Layer Combined NAV Challenger

**EXPERIMENTAL.** Roles → one capital book. No SOFT_FROZEN edits. No promotion.

```
E16 + E18 + E22   core sleeve
E45 (named cand.) optional on core / alpha-cut signal
E50-A (A3-R1)     alpha sleeve (separate capital)
Rule              cut Alpha before Core when E45 exposure < 1
```

Overlap window: `2019-01-02` → `2026-08-28` (1851 days). Split `80%` core / `20%` alpha.

| Book | CAGR | MDD | Util | Vol |
|---|---:|---:|---:|---:|
| CORE_ONLY | 15.04% | -22.11% | 0.0399 | 14.93% |
| CORE_E45_ONLY | 10.28% | -20.53% | 0.0002 | 11.75% |
| ALPHA_ONLY | 19.62% | -50.25% | -0.0551 | 27.81% |
| MIX_STATIC_80_20 | 16.80% | -23.62% | 0.0499 | 14.32% |
| MIX_ALPHA_CUT_FIRST | 15.54% | -23.13% | 0.0397 | 13.84% |
| FULL_CORE_E45_PLUS_ALPHA_CUT | 11.64% | -21.75% | 0.0076 | 11.58% |

## Decisions

- `four_layer_engine`: IMPLEMENTED_IN_CHALLENGER_SANDBOX
- `alpha_is_separate_sleeve`: True
- `alpha_cut_before_core`: True
- `e45_promoted`: False
- `alpha_promoted`: False
- `note`: Combined book exists for the overlap window where A3-R1 alpha NAV is available (2019-01-02 → 2026-08-28). Core-only history remains longer (from early-stack sandbox). Do not treat this as a frozen four-layer production engine.
- `compare`: `{"full_minus_core_util": -0.03226109930820498, "cut_minus_static_util": -0.010187747963804727, "cut_minus_static_mdd": 0.004897466363328773, "alpha_only_util": -0.05505731383790685}`

## Explicit non-actions

- Does not promote E45 or A3-R1
- Does not overwrite `forward/e21/`
- Does not retune sleeve weights as a new frozen router

Artifact: `reports/four_layer_combined_nav_summary.json`
