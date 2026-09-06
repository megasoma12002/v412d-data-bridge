# E45 PAPER Blend-Alpha Screen

Generated: `2026-09-06T05:13:50.625603+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.

## Definition

- Profile: E45 `E3_VOLTARGET_WINNER` (frozen winner lock **not** retuned)
- Blend: `exposure_α = (1−α)·1 + α·E45_exposure`
- Alphas: 0.00, 0.25, 0.35, 0.50, 1.00
- α=0 → BASE; α=1 → full CHAL_E45_E3 (same as operating observe challenger)

## Window metrics

| Book | α | Window | CAGR | MDD | mean_exp | n_days |
|---|---:|---|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0.00 | full | 13.79% | -22.54% | 1.000 | 3351 |
| BASE_E16_E18_E22_v2s | 0.00 | oof_2011_2018 | 8.89% | -17.55% | 1.000 | 1495 |
| BASE_E16_E18_E22_v2s | 0.00 | validation_2019_2022 | 12.30% | -22.54% | 1.000 | 977 |
| BASE_E16_E18_E22_v2s | 0.00 | sealed_2023_plus | 24.89% | -14.09% | 1.000 | 879 |
| BASE_E16_E18_E22_v2s | 0.00 | heldout_2019_plus | 18.20% | -22.54% | 1.000 | 1856 |
| BLEND_E45_A25 | 0.25 | full | 12.46% | -22.09% | 0.977 | 3351 |
| BLEND_E45_A25 | 0.25 | oof_2011_2018 | 9.15% | -16.71% | 0.977 | 1495 |
| BLEND_E45_A25 | 0.25 | validation_2019_2022 | 10.98% | -22.09% | 0.977 | 977 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | 20.57% | -9.33% | 0.977 | 879 |
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | 15.48% | -22.09% | 0.977 | 1856 |
| BLEND_E45_A35 | 0.35 | full | 12.26% | -21.89% | 0.967 | 3351 |
| BLEND_E45_A35 | 0.35 | oof_2011_2018 | 9.19% | -16.40% | 0.967 | 1495 |
| BLEND_E45_A35 | 0.35 | validation_2019_2022 | 10.98% | -21.89% | 0.967 | 977 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | 19.66% | -9.32% | 0.967 | 879 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | 15.06% | -21.89% | 0.967 | 1856 |
| BLEND_E45_A50 | 0.50 | full | 11.85% | -21.77% | 0.953 | 3351 |
| BLEND_E45_A50 | 0.50 | oof_2011_2018 | 9.20% | -16.22% | 0.953 | 1495 |
| BLEND_E45_A50 | 0.50 | validation_2019_2022 | 11.02% | -21.77% | 0.953 | 977 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | 17.96% | -9.26% | 0.953 | 879 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | 14.29% | -21.77% | 0.953 | 1856 |
| CHAL_E45_E3 | 1.00 | full | 10.91% | -20.83% | 0.907 | 3351 |
| CHAL_E45_E3 | 1.00 | oof_2011_2018 | 8.92% | -15.72% | 0.907 | 1495 |
| CHAL_E45_E3 | 1.00 | validation_2019_2022 | 10.07% | -20.83% | 0.907 | 977 |
| CHAL_E45_E3 | 1.00 | sealed_2023_plus | 15.86% | -9.55% | 0.907 | 879 |
| CHAL_E45_E3 | 1.00 | heldout_2019_plus | 12.79% | -20.83% | 0.907 | 1856 |

## Deltas vs BASE (focus windows)

| Book | α | Window | MDD improve pp | CAGR giveback pp | MDD/giveback |
|---|---:|---|---:|---:|---:|
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | +0.45 | +2.72 | +0.17 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | +4.75 | +4.32 | +1.10 |
| BLEND_E45_A25 | 0.25 | full | +0.45 | +1.33 | +0.34 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | +0.65 | +3.14 | +0.21 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | +4.76 | +5.23 | +0.91 |
| BLEND_E45_A35 | 0.35 | full | +0.65 | +1.53 | +0.43 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | +0.78 | +3.91 | +0.20 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | +4.83 | +6.93 | +0.70 |
| BLEND_E45_A50 | 0.50 | full | +0.78 | +1.94 | +0.40 |
| CHAL_E45_E3 | 1.00 | heldout_2019_plus | +1.71 | +5.41 | +0.32 |
| CHAL_E45_E3 | 1.00 | sealed_2023_plus | +4.54 | +9.03 | +0.50 |
| CHAL_E45_E3 | 1.00 | full | +1.71 | +2.88 | +0.59 |

## Held-out heuristic pick (paper only)

- Preferred partial α on held-out score `MDD_improve − 0.5·|CAGR_giveback|`: **α=0.25** (`BLEND_E45_A25`)
- Held-out MDD improve **+0.45 pp**; CAGR giveback **+2.72 pp**
- This is a **screen hint**, not a stitch / Soft-Frozen license.

## Ops / governance

1. Soft-Frozen live default stays BASE until a separate stitch PR
2. Operating observe sleeve remains full CHAL_E45_E3 unless human opens a new blend observe
3. Do not silent-edit Soft-Frozen; do not rewrite `forward/e21` history
4. Screen ≠ stitch; second human stitch ACCEPT still required for any live attach
5. Never cite the retired handoff MDD narrative; use dated lineage / challenger MDDs only

## Explicit non-goals

- Live stitch / Soft-Frozen flip / DEFAULT flip
- Retune frozen E3_VOLTARGET_WINNER lock in place
- Invent replacement for retired MDD narrative
- Treat screen winner as stitch license

## Label

`E45_BLEND_ALPHA_PAPER_SCREEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`

Artifacts:
- `/workspace/repro/e45-blend-alpha-screen/reports/e45_blend_alpha_screen.json`
- `/workspace/repro/e45-blend-alpha-screen/outputs/blend_alpha_window_metrics.csv`
- `/workspace/repro/e45-blend-alpha-screen/outputs/blend_alpha_deltas_vs_base.csv`
