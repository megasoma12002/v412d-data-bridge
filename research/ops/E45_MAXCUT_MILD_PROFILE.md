# E45 PAPER Mild max_cut Profile Screen

Generated: `2026-09-06T05:13:58.122429+00:00`
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
| BLEND_E45_A05 | REF_BLEND | 0.50 | 0.05 | +0.70 | +0.96 | 0.222 | 0.995 |
| BLEND_E45_A25 | REF_BLEND | 0.50 | 0.25 | +0.45 | +2.72 | -0.908 | 0.977 |
| REF_WINNER_MC50_FULL | REF_WINNER | 0.50 | 1.00 | +1.71 | +5.41 | -0.996 | 0.907 |
| MILD_MC25_A50 | MILD_BLEND | 0.25 | 0.50 | +0.56 | +3.13 | -1.003 | 0.969 |
| MILD_MC35_A50 | MILD_BLEND | 0.35 | 0.50 | +0.68 | +3.47 | -1.062 | 0.962 |
| MILD_MC40_FULL | MILD | 0.40 | 1.00 | +1.40 | +5.24 | -1.216 | 0.919 |
| MILD_MC35_FULL | MILD | 0.35 | 1.00 | +1.24 | +5.04 | -1.277 | 0.925 |
| MILD_MC25_FULL | MILD | 0.25 | 1.00 | +0.89 | +4.62 | -1.424 | 0.939 |

## Sealed top (same score)

| Book | Family | max_cut | α | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|---:|
| BLEND_E45_A25 | REF_BLEND | 0.50 | 0.25 | +4.75 | +4.32 | 2.595 |
| MILD_MC25_A50 | MILD_BLEND | 0.25 | 0.50 | +4.83 | +5.07 | 2.300 |
| BLEND_E45_A05 | REF_BLEND | 0.50 | 0.05 | +2.78 | +1.42 | 2.069 |
| MILD_MC35_A50 | MILD_BLEND | 0.35 | 0.50 | +4.84 | +5.89 | 1.891 |
| MILD_MC25_FULL | MILD | 0.25 | 1.00 | +4.75 | +8.19 | 0.657 |
| MILD_MC35_FULL | MILD | 0.35 | 1.00 | +4.59 | +8.90 | 0.134 |

**Held-out preferred:** `BLEND_E45_A05` (family=REF_BLEND, max_cut=0.5, α=0.05) — MDD +0.70 / giveback +0.96

### Best by family (held-out)

- **REF_BLEND**: `BLEND_E45_A05` — MDD +0.70 / giveback +0.96 / score 0.222
- **REF_WINNER**: `REF_WINNER_MC50_FULL` — MDD +1.71 / giveback +5.41 / score -0.996
- **MILD**: `MILD_MC40_FULL` — MDD +1.40 / giveback +5.24 / score -1.216
- **MILD_BLEND**: `MILD_MC25_A50` — MDD +0.56 / giveback +3.13 / score -1.003

## Month-end PAUSE sensitivity (asof 2026-09-04)

Policy: ALERT >3pp / PAUSE_REVIEW >5pp on YTD / trailing_1y.

| Book | Family | Window | MDD Δpp | Giveback pp | Flag |
|---|---|---|---:|---:|---|
| BASE_E16_E18_E22_v2s | BASE | trailing_1y | +0.00 | +0.00 | **OK** |
| BASE_E16_E18_E22_v2s | BASE | ytd | +0.00 | +0.00 | **OK** |
| MILD_MC25_FULL | MILD | trailing_1y | +6.65 | +18.60 | **PAUSE_REVIEW** |
| MILD_MC25_FULL | MILD | ytd | +6.65 | +21.25 | **PAUSE_REVIEW** |
| MILD_MC35_FULL | MILD | trailing_1y | +6.80 | +19.61 | **PAUSE_REVIEW** |
| MILD_MC35_FULL | MILD | ytd | +6.80 | +22.40 | **PAUSE_REVIEW** |
| MILD_MC40_FULL | MILD | trailing_1y | +6.83 | +19.83 | **PAUSE_REVIEW** |
| MILD_MC40_FULL | MILD | ytd | +6.83 | +22.71 | **PAUSE_REVIEW** |
| MILD_MC25_A50 | MILD_BLEND | trailing_1y | +5.83 | +13.11 | **PAUSE_REVIEW** |
| MILD_MC25_A50 | MILD_BLEND | ytd | +5.83 | +13.65 | **PAUSE_REVIEW** |
| MILD_MC35_A50 | MILD_BLEND | trailing_1y | +6.07 | +14.42 | **PAUSE_REVIEW** |
| MILD_MC35_A50 | MILD_BLEND | ytd | +6.07 | +15.26 | **PAUSE_REVIEW** |
| BLEND_E45_A05 | REF_BLEND | trailing_1y | +2.78 | +5.17 | **PAUSE_REVIEW** |
| BLEND_E45_A05 | REF_BLEND | ytd | +2.78 | +4.87 | **ALERT** |
| BLEND_E45_A25 | REF_BLEND | trailing_1y | +5.59 | +11.25 | **PAUSE_REVIEW** |
| BLEND_E45_A25 | REF_BLEND | ytd | +5.59 | +11.36 | **PAUSE_REVIEW** |
| REF_WINNER_MC50_FULL | REF_WINNER | trailing_1y | +6.86 | +20.12 | **PAUSE_REVIEW** |
| REF_WINNER_MC50_FULL | REF_WINNER | ytd | +6.86 | +23.08 | **PAUSE_REVIEW** |

## Read-through (paper)

1. Mild max_cut profiles are **new paper challengers**, not edits to frozen winner.
2. Compare best `MILD` / `MILD_BLEND` vs `BLEND_E45_A05` / `BLEND_E45_A25` on held-out score.
3. Held-out preferred this screen: **`BLEND_E45_A05`** (score 0.222).
4. Best mild (`MILD_MC40_FULL`) does **not** beat BLEND_E45_A05 on held-out score (-1.216 vs 0.222) — blend-α remains stronger paper path.
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

