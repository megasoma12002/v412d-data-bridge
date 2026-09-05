# E45 Paper Feasibility Study (2026-09-05)

Generated: `2026-09-05T16:52:58.831143+00:00`
Charter: `research/e45/E45_FEASIBILITY_CHARTER.md`
Pack: `cost_stress_recovery_seal`
Provenance in_dir: `/workspace/repro/e45-feasibility-study-regen-20260905`

## Verdict: `FEASIBLE_READY_FOR_LIVE_BALLOT`

- Live ballot ready: `True`
- Official status **unchanged** until human ballot: NOT_VERIFIED / DEFERRED / SOFT_FROZEN_CRITICAL / live auth NO
- Historical −13.16%: **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** / interpretation **`EARLY_NON_RIGOROUS_RESEARCH_RESULT`** (not PASS)
- Seal on **fresh regen** with OUTPUT_MANIFEST **sha256 verified**; F8–F10 tightened (AND / strict majority / no +5d)

## Comparison (full sample)

| Arm | CAGR | MDD |
|---|---:|---:|
| Baseline | 13.30% | -22.64% |
| Challenger | 10.42% | -20.76% |
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

## F8 Cost (from regenerated fills)

| Arm | Fills | Fee sum | Fee bps/yr | Ann. turnover approx |
|---|---:|---:|---:|---:|
| Baseline | 6271 | 400790 | 46.6 | 2.24 |
| Challenger | 6931 | 394843 | 49.9 | 2.35 |

## F9 Named stress windows (from regenerated NAV)

| Window | Baseline MDD | Challenger MDD | Δ pp | Return Δ |
|---|---:|---:|---:|---:|
| 2015_china_shock | -10.24% | -9.39% | +0.85 | -0.12% |
| 2018_trade_war | -6.98% | -6.14% | +0.84 | -1.05% |
| 2020_covid | -22.36% | -20.76% | +1.60 | -1.41% |
| 2022_bear | -16.71% | -16.53% | +0.19 | -0.10% |

## F10 Recovery (from regenerated NAV)

| Arm | Trough date | Trough MDD | Days to recover | Longest underwater |
|---|---|---:|---:|---:|
| Baseline | 2020-03-19 | -22.64% | 392 | 465 |
| Challenger | 2020-03-19 | -20.76% | 403 | 466 |

- Mean E45 scale: **0.907** (min 0.501; frac<0.85 = 15.4%)

## Lineage honesty

- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45`
- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`

## Next steps

- Human may open a separate live-switch ballot; this pack does not flip live
- Keep DEFAULT_BOOKS_VERSION = E22_v2s_tw until ballot ACCEPT

## Artifacts

- `research/e45/E45_FEASIBILITY_STUDY_2026-09-05.json`
- `/workspace/repro/e45-feasibility-study-regen-20260905/`
- Scripts: `scripts/e45_feasibility_gates.py`, `scripts/e45_feasibility_seal_pack.py`

## Label

`E45_FEASIBILITY_STUDY_2026-09-05__FEASIBLE_READY_FOR_LIVE_BALLOT__FRESH_REGEN_HASH_VERIFIED`

