# E45 Paper Feasibility Study (2026-09-05)

Generated: `2026-09-05T15:48:06.060417+00:00`
Charter: `research/e45/E45_FEASIBILITY_CHARTER.md`
Pack: `cost_stress_recovery_seal`

## Verdict: `FEASIBLE_READY_FOR_LIVE_BALLOT`

- Live ballot ready: `True`
- Official status **unchanged** until human ballot: NOT_VERIFIED / DEFERRED / SOFT_FROZEN_CRITICAL / live auth NO
- Historical −13.16%: **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** (not PASS; early-data incompleteness is hypothesis only)

## Comparison (full sample)

| Arm | CAGR | MDD |
|---|---:|---:|
| Baseline `E16_E18_E22_v2s` | 13.30% | -22.64% |
| Challenger `E16_E18_E22_v2s_E45_E3` | 10.42% | -20.76% |
| Delta | **-2.88 pp** | **+1.88 pp** |

## Gates F1–F10

| Gate | Pass |
|---|---|
| `F1_artifact_honesty` | **True** |
| `F2_exact_t1` | **True** |
| `F3_crisis_mdd` | **True** |
| `F4_full_sample_mdd` | **True** |
| `F5_cagr_giveback` | **True** |
| `F6_no_retune` | **True** |
| `F7_live_untouched` | **True** |
| `F8_cost` | **True** |
| `F9_stress` | **True** |
| `F10_recovery` | **True** |

## F8 Cost

| Arm | Fills | Fee sum | Fee bps/yr (vs avg NAV) | Ann. turnover approx |
|---|---:|---:|---:|---:|
| Baseline | 6271 | 400790 | 46.6 | 2.24 |
| Challenger | 6931 | 394843 | 49.9 | 2.35 |

## F9 Named stress windows

| Window | Baseline MDD | Challenger MDD | Δ pp | Return Δ |
|---|---:|---:|---:|---:|
| 2015_china_shock | -10.24% | -9.39% | +0.85 | -0.12% |
| 2018_trade_war | -6.98% | -6.14% | +0.84 | -1.05% |
| 2020_covid | -22.36% | -20.76% | +1.60 | -1.41% |
| 2022_bear | -16.71% | -16.53% | +0.19 | -0.10% |

## F10 Recovery

| Arm | Trough date | Trough MDD | Days to recover | Longest underwater (days) |
|---|---|---:|---:|---:|
| Baseline | 2020-03-19 | -22.64% | 392 | 465 |
| Challenger | 2020-03-19 | -20.76% | 403 | 466 |

- Mean E45 scale: **0.907** (min 0.501; frac<0.85 = 15.4%)

## Lineage honesty

- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45`
- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`

## Interpretation

Paper gates F1–F10 pass. Humans **may** open a separate live-switch ballot.
This study does **not** change live wiring or DEFAULT books.

## Next steps

- Human may open a live-switch ballot (separate PR); this pack does not flip live
- Keep DEFAULT_BOOKS_VERSION = E22_v2s_tw until ballot ACCEPT

## Artifacts

- `research/e45/E45_FEASIBILITY_STUDY_2026-09-05.json`
- `repro/e45-feasibility-study/`
- Scripts: `scripts/e45_feasibility_gates.py`, `scripts/e45_feasibility_seal_pack.py`

## Label

`E45_FEASIBILITY_STUDY_2026-09-05__FEASIBLE_READY_FOR_LIVE_BALLOT`

