# E45 PAPER Mild max_cut Profile Screen

Generated: `2026-09-06T01:40:57.395013+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.
Observe sleeves (full-E45 + blend-α=0.25) **unchanged**.
Frozen `E3_WINNER.max_cut` untouched: **True** (still 0.5).

## Roadmap context

- Priority **#3**: milder defense via **new paper profile** (lower max_cut), not in-place winner retune.
- Compare mild profiles vs blend-α refs from #1/#2 lineage.

## Definitions

| Family | Rule |
|---|---|
| `REF_WINNER` | frozen `E3_VOLTARGET_WINNER` (max_cut=0.50) full |
| `REF_BLEND` | `(1−α)·1 + α·winner` |
| `MILD` | E3 voltarget math with max_cut ∈ {0.25,0.35,0.40}, α=1 |
| `MILD_BLEND` | `(1−α)·1 + α·mild_exposure` |

Winner vs direct mc=0.50 series corr: **1.000000** (sanity).

## Held-out deltas vs BASE

| Book | Family | max_cut | α | MDD Δpp | Giveback pp | Score | mean_exp |
|---|---|---:|---:|---:|---:|---:|---:|
| REF_BLEND_A05 | REF_BLEND | 0.50 | 0.05 | +0.85 | +1.07 | 0.320 | 0.995 |
| REF_BLEND_A25 | REF_BLEND | 0.50 | 0.25 | +0.63 | +2.83 | -0.783 | 0.977 |
| MILD_MC25_A50 | MILD_BLEND | 0.25 | 0.50 | +0.73 | +3.22 | -0.874 | 0.969 |
| REF_WINNER_MC50_FULL | REF_WINNER | 0.50 | 1.00 | +1.88 | +5.65 | -0.943 | 0.907 |
| MILD_MC35_A50 | MILD_BLEND | 0.35 | 0.50 | +0.84 | +3.57 | -0.945 | 0.962 |
| MILD_MC40_FULL | MILD | 0.40 | 1.00 | +1.57 | +5.36 | -1.106 | 0.919 |
| MILD_MC35_FULL | MILD | 0.35 | 1.00 | +1.42 | +5.19 | -1.177 | 0.925 |
| MILD_MC25_FULL | MILD | 0.25 | 1.00 | +1.06 | +4.71 | -1.290 | 0.939 |

## Sealed top (same score)

| Book | Family | max_cut | α | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|---:|
| REF_BLEND_A25 | REF_BLEND | 0.50 | 0.25 | +5.13 | +4.36 | 2.944 |
| MILD_MC25_A50 | MILD_BLEND | 0.25 | 0.50 | +5.20 | +5.14 | 2.634 |
| REF_BLEND_A05 | REF_BLEND | 0.50 | 0.05 | +3.07 | +1.50 | 2.317 |
| MILD_MC35_A50 | MILD_BLEND | 0.35 | 0.50 | +5.20 | +5.89 | 2.253 |
| MILD_MC25_FULL | MILD | 0.25 | 1.00 | +5.11 | +8.21 | 1.010 |
| MILD_MC35_FULL | MILD | 0.35 | 1.00 | +4.96 | +9.00 | 0.465 |

**Held-out preferred:** `REF_BLEND_A05` (family=REF_BLEND, max_cut=0.5, α=0.05) — MDD +0.85 / giveback +1.07

### Best by family (held-out)

- **REF_BLEND**: `REF_BLEND_A05` — MDD +0.85 / giveback +1.07 / score 0.320
- **REF_WINNER**: `REF_WINNER_MC50_FULL` — MDD +1.88 / giveback +5.65 / score -0.943
- **MILD**: `MILD_MC40_FULL` — MDD +1.57 / giveback +5.36 / score -1.106
- **MILD_BLEND**: `MILD_MC25_A50` — MDD +0.73 / giveback +3.22 / score -0.874

## Month-end PAUSE sensitivity (asof 2026-09-04)

Policy: ALERT >3pp / PAUSE_REVIEW >5pp on YTD / trailing_1y.

| Book | Family | Window | MDD Δpp | Giveback pp | Flag |
|---|---|---|---:|---:|---|
| BASE_E16_E18_E22_v2s | BASE | trailing_1y | +0.00 | +0.00 | **OK** |
| BASE_E16_E18_E22_v2s | BASE | ytd | +0.00 | +0.00 | **OK** |
| MILD_MC25_FULL | MILD | trailing_1y | +7.04 | +19.04 | **PAUSE_REVIEW** |
| MILD_MC25_FULL | MILD | ytd | +7.04 | +21.46 | **PAUSE_REVIEW** |
| MILD_MC35_FULL | MILD | trailing_1y | +7.17 | +19.96 | **PAUSE_REVIEW** |
| MILD_MC35_FULL | MILD | ytd | +7.17 | +22.64 | **PAUSE_REVIEW** |
| MILD_MC40_FULL | MILD | trailing_1y | +7.20 | +20.27 | **PAUSE_REVIEW** |
| MILD_MC40_FULL | MILD | ytd | +7.20 | +22.93 | **PAUSE_REVIEW** |
| MILD_MC25_A50 | MILD_BLEND | trailing_1y | +6.23 | +13.51 | **PAUSE_REVIEW** |
| MILD_MC25_A50 | MILD_BLEND | ytd | +6.23 | +13.91 | **PAUSE_REVIEW** |
| MILD_MC35_A50 | MILD_BLEND | trailing_1y | +6.44 | +14.68 | **PAUSE_REVIEW** |
| MILD_MC35_A50 | MILD_BLEND | ytd | +6.44 | +15.28 | **PAUSE_REVIEW** |
| REF_BLEND_A05 | REF_BLEND | trailing_1y | +3.07 | +5.62 | **PAUSE_REVIEW** |
| REF_BLEND_A05 | REF_BLEND | ytd | +3.07 | +5.00 | **PAUSE_REVIEW** |
| REF_BLEND_A25 | REF_BLEND | trailing_1y | +5.94 | +11.69 | **PAUSE_REVIEW** |
| REF_BLEND_A25 | REF_BLEND | ytd | +5.94 | +11.55 | **PAUSE_REVIEW** |
| REF_WINNER_MC50_FULL | REF_WINNER | trailing_1y | +7.23 | +20.49 | **PAUSE_REVIEW** |
| REF_WINNER_MC50_FULL | REF_WINNER | ytd | +7.23 | +23.23 | **PAUSE_REVIEW** |

## Read-through (paper)

1. Mild max_cut profiles are **new paper challengers**, not edits to frozen winner.
2. Compare best `MILD` / `MILD_BLEND` vs `REF_BLEND_A05` / `REF_BLEND_A25` on held-out score.
3. Held-out preferred this screen: **`REF_BLEND_A05`** (score 0.320).
4. Best mild (`MILD_MC40_FULL`) does **not** beat REF_BLEND_A05 on held-out score (-1.106 vs 0.320) — blend-α remains stronger paper path.
5. This screen does **not** open a new observe sleeve or authorize stitch.

## Governance

- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**
- Live DEFAULT **`E22_v2s_tw` KEEP**
- Live E45 stitch **FORBIDDEN**
- Frozen `E3_WINNER.max_cut=0.5` **untouched**
- −13.16% remains **RETIRED_HISTORICAL_NARRATIVE**

## Artifacts

- `/workspace/repro/e45-maxcut-mild-profile/reports/e45_maxcut_mild_profile.json`
- `/workspace/repro/e45-maxcut-mild-profile/outputs/maxcut_mild_window_metrics.csv`
- `/workspace/repro/e45-maxcut-mild-profile/outputs/maxcut_mild_deltas_vs_base.csv`
- `/workspace/repro/e45-maxcut-mild-profile/outputs/maxcut_mild_pause_sensitivity.csv`
- `/workspace/research/e45/E45_MAXCUT_MILD_PROFILE.md`

## Reproduce

```bash
python3 scripts/e45_maxcut_mild_profile_paper.py
```

