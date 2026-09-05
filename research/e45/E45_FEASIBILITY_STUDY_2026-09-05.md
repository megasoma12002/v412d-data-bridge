# E45 Paper Feasibility Study (2026-09-05)

Generated: `2026-09-05T15:42:42.223453+00:00`
Charter: `research/e45/E45_FEASIBILITY_CHARTER.md`

## Verdict: `FEASIBLE_CONTINUE_PAPER`

- Live ballot ready: `False`
- Official status **unchanged**: NOT_VERIFIED / DEFERRED / SOFT_FROZEN_CRITICAL / live auth NO
- Historical −13.16%: **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** (not used as PASS)

## Comparison

| Arm | Definition | CAGR | MDD |
|---|---|---:|---:|
| Baseline | `E16_E18_E22_v2s` | 13.30% | -22.64% |
| Challenger | `E16_E18_E22_v2s_E45_E3` | 10.42% | -20.76% |
| Delta | challenger − baseline | **-2.88 pp** | **+1.88 pp** |

- CAGR giveback: **2.88 pp** (gate max 2.0 pp unless crisis dominance)
- Crisis-path MDD improvement: **+2.08 pp** (baseline -14.04% → challenger -11.95%)
- Mean E45 equity scale (challenger): **0.907**

## Gates

| Gate | Pass | Detail |
|---|---|---|
| `F1_artifact_honesty` | **True** | `{"note": "Dated early-stack recompute; -13.16% not used as PASS"}` |
| `F2_exact_t1` | **True** | `{"same_bar_fills_baseline": 0, "same_bar_fills_challenger": 0}` |
| `F3_crisis_mdd` | **True** | `{"baseline_crisis_path_mdd": -0.14035729376243833, "challenger_crisis_path_mdd": -0.11951885085638458, "improvement_pp": 2.0838442906053745}` |
| `F4_full_sample_mdd` | **True** | `{"baseline_mdd": -0.2263873534222821, "challenger_mdd": -0.2075836624984907, "improvement_pp": 1.8803690923791416}` |
| `F5_cagr_giveback` | **True** | `{"giveback_pp": 2.878051207719068, "max_pp": 2.0, "crisis_dominates_exception": true, "crisis_years_better": 9, "crisis_years_worse": 0}` |
| `F6_no_retune` | **True** | `{"note": "Locked E3 winner only"}` |
| `F7_live_untouched` | **True** | `{"note": "Paper repro only; live DEFAULT / forward path not edited"}` |

## Crisis-year windows

| Year | Crisis days | Baseline MDD | Challenger MDD | Δ pp |
|---:|---:|---:|---:|---:|
| 2015 | 77 | -13.65% | -12.80% | +0.85 |
| 2016 | 50 | -5.00% | -3.96% | +1.03 |
| 2018 | 6 | -6.98% | -6.14% | +0.84 |
| 2020 | 27 | -22.64% | -20.76% | +1.88 |
| 2022 | 140 | -16.71% | -16.53% | +0.19 |
| 2023 | 27 | -6.97% | -6.58% | +0.39 |
| 2024 | 20 | -6.88% | -5.91% | +0.97 |
| 2025 | 24 | -9.19% | -8.96% | +0.24 |
| 2026 | 48 | -14.46% | -7.23% | +7.23 |

## Lineage honesty

- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45`
- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`

## Interpretation

Paper research may **continue** (cost/stress/recovery sealing).
This is **not** live-switch authorization.

## Next steps

- If CONTINUE_PAPER: seal cost/stress/recovery KPI pack (still paper)
- Do not open live-switch ballot until FEASIBLE_READY_FOR_LIVE_BALLOT
- Keep live DEFAULT_BOOKS_VERSION = E22_v2s_tw

## Artifacts

- `research/e45/E45_FEASIBILITY_STUDY_2026-09-05.json`
- `repro/e45-feasibility-study/`
- Script: `scripts/e45_feasibility_gates.py`

## Label

`E45_FEASIBILITY_STUDY_2026-09-05__FEASIBLE_CONTINUE_PAPER`

