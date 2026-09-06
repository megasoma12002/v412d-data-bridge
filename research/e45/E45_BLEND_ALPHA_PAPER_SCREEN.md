# E45 PAPER Blend-Alpha Screen

Generated: `2026-09-06T00:50:21.707417+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.

## Definition

- Profile: E45 `E3_VOLTARGET_WINNER` (frozen winner lock **not** retuned)
- Blend: `exposure_α = (1−α)·1 + α·E45_exposure`
- Alphas: 0.00, 0.25, 0.35, 0.50, 1.00
- α=0 → BASE; α=1 → full CHAL_E45_E3 (same as operating observe challenger)

## Window metrics

| Book | α | Window | CAGR | MDD | mean_exp | n_days |
|---|---:|---|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0.00 | full | 13.78% | -22.64% | 1.000 | 3351 |
| BASE_E16_E18_E22_v2s | 0.00 | oof_2011_2018 | 8.85% | -17.41% | 1.000 | 1495 |
| BASE_E16_E18_E22_v2s | 0.00 | validation_2019_2022 | 12.33% | -22.64% | 1.000 | 977 |
| BASE_E16_E18_E22_v2s | 0.00 | sealed_2023_plus | 24.93% | -14.46% | 1.000 | 879 |
| BASE_E16_E18_E22_v2s | 0.00 | heldout_2019_plus | 18.23% | -22.64% | 1.000 | 1856 |
| BLEND_E45_A25 | 0.25 | full | 12.40% | -22.01% | 0.977 | 3351 |
| BLEND_E45_A25 | 0.25 | oof_2011_2018 | 9.13% | -16.57% | 0.977 | 1495 |
| BLEND_E45_A25 | 0.25 | validation_2019_2022 | 10.85% | -22.01% | 0.977 | 977 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | 20.56% | -9.33% | 0.977 | 879 |
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | 15.41% | -22.01% | 0.977 | 1856 |
| BLEND_E45_A35 | 0.35 | full | 12.18% | -21.82% | 0.967 | 3351 |
| BLEND_E45_A35 | 0.35 | oof_2011_2018 | 9.16% | -16.32% | 0.967 | 1495 |
| BLEND_E45_A35 | 0.35 | validation_2019_2022 | 10.83% | -21.82% | 0.967 | 977 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | 19.62% | -9.32% | 0.967 | 879 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | 14.96% | -21.82% | 0.967 | 1856 |
| BLEND_E45_A50 | 0.50 | full | 11.78% | -21.69% | 0.953 | 3351 |
| BLEND_E45_A50 | 0.50 | oof_2011_2018 | 9.18% | -16.08% | 0.953 | 1495 |
| BLEND_E45_A50 | 0.50 | validation_2019_2022 | 10.86% | -21.69% | 0.953 | 977 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | 17.95% | -9.25% | 0.953 | 879 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | 14.19% | -21.69% | 0.953 | 1856 |
| CHAL_E45_E3_FULL | 1.00 | full | 10.79% | -20.76% | 0.907 | 3351 |
| CHAL_E45_E3_FULL | 1.00 | oof_2011_2018 | 8.91% | -15.57% | 0.907 | 1495 |
| CHAL_E45_E3_FULL | 1.00 | validation_2019_2022 | 9.97% | -20.76% | 0.907 | 977 |
| CHAL_E45_E3_FULL | 1.00 | sealed_2023_plus | 15.52% | -9.56% | 0.907 | 879 |
| CHAL_E45_E3_FULL | 1.00 | heldout_2019_plus | 12.59% | -20.76% | 0.907 | 1856 |

## Deltas vs BASE (focus windows)

| Book | α | Window | MDD improve pp | CAGR giveback pp | MDD/giveback |
|---|---:|---|---:|---:|---:|
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | +0.63 | +2.83 | +0.22 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | +5.13 | +4.36 | +1.18 |
| BLEND_E45_A25 | 0.25 | full | +0.63 | +1.38 | +0.46 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | +0.82 | +3.28 | +0.25 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | +5.14 | +5.31 | +0.97 |
| BLEND_E45_A35 | 0.35 | full | +0.82 | +1.60 | +0.51 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | +0.95 | +4.04 | +0.24 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | +5.21 | +6.98 | +0.75 |
| BLEND_E45_A50 | 0.50 | full | +0.95 | +2.00 | +0.48 |
| CHAL_E45_E3_FULL | 1.00 | heldout_2019_plus | +1.88 | +5.65 | +0.33 |
| CHAL_E45_E3_FULL | 1.00 | sealed_2023_plus | +4.90 | +9.40 | +0.52 |
| CHAL_E45_E3_FULL | 1.00 | full | +1.88 | +2.99 | +0.63 |

## Held-out heuristic pick (paper only)

- Preferred partial α on held-out score `MDD_improve − 0.5·|CAGR_giveback|`: **α=0.25** (`BLEND_E45_A25`)
- Held-out MDD improve **+0.63 pp**; CAGR giveback **+2.83 pp**
- This is a **screen hint**, not a stitch / Soft-Frozen license.

## Ops / governance

1. Soft-Frozen live default stays BASE until a separate stitch PR
2. Operating observe sleeve remains full CHAL_E45_E3 unless human opens a new blend observe
3. Do not silent-edit Soft-Frozen; do not rewrite `forward/e21` history
4. Screen ≠ stitch; second human stitch ACCEPT still required for any live attach
5. Never cite −13.16%; use dated lineage / challenger MDDs only

## Explicit non-goals

- Live stitch / Soft-Frozen flip / DEFAULT flip
- Retune frozen E3_VOLTARGET_WINNER lock in place
- Invent replacement for retired -13.16% narrative
- Treat screen winner as stitch license

## Label

`E45_BLEND_ALPHA_PAPER_SCREEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`

Artifacts:
- `/workspace/repro/e45-blend-alpha-screen/reports/e45_blend_alpha_screen.json`
- `/workspace/repro/e45-blend-alpha-screen/outputs/blend_alpha_window_metrics.csv`
- `/workspace/repro/e45-blend-alpha-screen/outputs/blend_alpha_deltas_vs_base.csv`
