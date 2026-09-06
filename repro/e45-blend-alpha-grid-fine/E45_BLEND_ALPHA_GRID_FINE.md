# E45 PAPER Blend-Alpha Fine Grid (step 0.05)

Generated: `2026-09-06T05:13:46.211307+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.

## Definition

- Profile: E45 `E3_VOLTARGET_WINNER` (frozen winner lock **not** retuned)
- Blend: `exposure_α = (1−α)·1 + α·E45_exposure`
- Alphas: 0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00
- α=0 → BASE; α=1 → full CHAL_E45_E3 (same as operating observe challenger)

## Window metrics

| Book | α | Window | CAGR | MDD | mean_exp | n_days |
|---|---:|---|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0.00 | full | 13.79% | -22.54% | 1.000 | 3351 |
| BASE_E16_E18_E22_v2s | 0.00 | oof_2011_2018 | 8.89% | -17.55% | 1.000 | 1495 |
| BASE_E16_E18_E22_v2s | 0.00 | validation_2019_2022 | 12.30% | -22.54% | 1.000 | 977 |
| BASE_E16_E18_E22_v2s | 0.00 | sealed_2023_plus | 24.89% | -14.09% | 1.000 | 879 |
| BASE_E16_E18_E22_v2s | 0.00 | heldout_2019_plus | 18.20% | -22.54% | 1.000 | 1856 |
| BLEND_E45_A05 | 0.05 | full | 13.37% | -21.84% | 0.995 | 3351 |
| BLEND_E45_A05 | 0.05 | oof_2011_2018 | 9.06% | -17.40% | 0.995 | 1495 |
| BLEND_E45_A05 | 0.05 | validation_2019_2022 | 11.73% | -21.84% | 0.995 | 977 |
| BLEND_E45_A05 | 0.05 | sealed_2023_plus | 23.47% | -11.31% | 0.995 | 879 |
| BLEND_E45_A05 | 0.05 | heldout_2019_plus | 17.24% | -21.84% | 0.995 | 1856 |
| BLEND_E45_A10 | 0.10 | full | 13.09% | -21.74% | 0.991 | 3351 |
| BLEND_E45_A10 | 0.10 | oof_2011_2018 | 9.10% | -17.37% | 0.991 | 1495 |
| BLEND_E45_A10 | 0.10 | validation_2019_2022 | 11.30% | -21.74% | 0.991 | 977 |
| BLEND_E45_A10 | 0.10 | sealed_2023_plus | 22.77% | -10.43% | 0.991 | 879 |
| BLEND_E45_A10 | 0.10 | heldout_2019_plus | 16.69% | -21.74% | 0.991 | 1856 |
| BLEND_E45_A15 | 0.15 | full | 12.85% | -21.91% | 0.986 | 3351 |
| BLEND_E45_A15 | 0.15 | oof_2011_2018 | 9.12% | -17.17% | 0.986 | 1495 |
| BLEND_E45_A15 | 0.15 | validation_2019_2022 | 11.16% | -21.91% | 0.986 | 977 |
| BLEND_E45_A15 | 0.15 | sealed_2023_plus | 21.97% | -9.78% | 0.986 | 879 |
| BLEND_E45_A15 | 0.15 | heldout_2019_plus | 16.24% | -21.91% | 0.986 | 1856 |
| BLEND_E45_A20 | 0.20 | full | 12.63% | -22.14% | 0.981 | 3351 |
| BLEND_E45_A20 | 0.20 | oof_2011_2018 | 9.13% | -16.93% | 0.981 | 1495 |
| BLEND_E45_A20 | 0.20 | validation_2019_2022 | 11.07% | -22.14% | 0.981 | 977 |
| BLEND_E45_A20 | 0.20 | sealed_2023_plus | 21.18% | -9.32% | 0.981 | 879 |
| BLEND_E45_A20 | 0.20 | heldout_2019_plus | 15.82% | -22.14% | 0.981 | 1856 |
| BLEND_E45_A25 | 0.25 | full | 12.46% | -22.09% | 0.977 | 3351 |
| BLEND_E45_A25 | 0.25 | oof_2011_2018 | 9.15% | -16.71% | 0.977 | 1495 |
| BLEND_E45_A25 | 0.25 | validation_2019_2022 | 10.98% | -22.09% | 0.977 | 977 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | 20.57% | -9.33% | 0.977 | 879 |
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | 15.48% | -22.09% | 0.977 | 1856 |
| BLEND_E45_A30 | 0.30 | full | 12.35% | -21.92% | 0.972 | 3351 |
| BLEND_E45_A30 | 0.30 | oof_2011_2018 | 9.18% | -16.51% | 0.972 | 1495 |
| BLEND_E45_A30 | 0.30 | validation_2019_2022 | 10.93% | -21.92% | 0.972 | 977 |
| BLEND_E45_A30 | 0.30 | sealed_2023_plus | 20.13% | -9.33% | 0.972 | 879 |
| BLEND_E45_A30 | 0.30 | heldout_2019_plus | 15.25% | -21.92% | 0.972 | 1856 |
| BLEND_E45_A35 | 0.35 | full | 12.26% | -21.89% | 0.967 | 3351 |
| BLEND_E45_A35 | 0.35 | oof_2011_2018 | 9.19% | -16.40% | 0.967 | 1495 |
| BLEND_E45_A35 | 0.35 | validation_2019_2022 | 10.98% | -21.89% | 0.967 | 977 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | 19.66% | -9.32% | 0.967 | 879 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | 15.06% | -21.89% | 0.967 | 1856 |
| BLEND_E45_A40 | 0.40 | full | 12.09% | -21.86% | 0.963 | 3351 |
| BLEND_E45_A40 | 0.40 | oof_2011_2018 | 9.18% | -16.37% | 0.963 | 1495 |
| BLEND_E45_A40 | 0.40 | validation_2019_2022 | 11.05% | -21.86% | 0.963 | 977 |
| BLEND_E45_A40 | 0.40 | sealed_2023_plus | 18.95% | -9.28% | 0.963 | 879 |
| BLEND_E45_A40 | 0.40 | heldout_2019_plus | 14.76% | -21.86% | 0.963 | 1856 |
| BLEND_E45_A45 | 0.45 | full | 11.97% | -21.83% | 0.958 | 3351 |
| BLEND_E45_A45 | 0.45 | oof_2011_2018 | 9.22% | -16.28% | 0.958 | 1495 |
| BLEND_E45_A45 | 0.45 | validation_2019_2022 | 11.04% | -21.83% | 0.958 | 977 |
| BLEND_E45_A45 | 0.45 | sealed_2023_plus | 18.42% | -9.25% | 0.958 | 879 |
| BLEND_E45_A45 | 0.45 | heldout_2019_plus | 14.51% | -21.83% | 0.958 | 1856 |
| BLEND_E45_A50 | 0.50 | full | 11.85% | -21.77% | 0.953 | 3351 |
| BLEND_E45_A50 | 0.50 | oof_2011_2018 | 9.20% | -16.22% | 0.953 | 1495 |
| BLEND_E45_A50 | 0.50 | validation_2019_2022 | 11.02% | -21.77% | 0.953 | 977 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | 17.96% | -9.26% | 0.953 | 879 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | 14.29% | -21.77% | 0.953 | 1856 |
| BLEND_E45_A55 | 0.55 | full | 11.73% | -21.69% | 0.949 | 3351 |
| BLEND_E45_A55 | 0.55 | oof_2011_2018 | 9.19% | -16.17% | 0.949 | 1495 |
| BLEND_E45_A55 | 0.55 | validation_2019_2022 | 10.99% | -21.69% | 0.949 | 977 |
| BLEND_E45_A55 | 0.55 | sealed_2023_plus | 17.58% | -9.29% | 0.949 | 879 |
| BLEND_E45_A55 | 0.55 | heldout_2019_plus | 14.09% | -21.69% | 0.949 | 1856 |
| BLEND_E45_A60 | 0.60 | full | 11.61% | -21.54% | 0.944 | 3351 |
| BLEND_E45_A60 | 0.60 | oof_2011_2018 | 9.15% | -16.15% | 0.944 | 1495 |
| BLEND_E45_A60 | 0.60 | validation_2019_2022 | 10.96% | -21.54% | 0.944 | 977 |
| BLEND_E45_A60 | 0.60 | sealed_2023_plus | 17.18% | -9.37% | 0.944 | 879 |
| BLEND_E45_A60 | 0.60 | heldout_2019_plus | 13.89% | -21.54% | 0.944 | 1856 |
| BLEND_E45_A65 | 0.65 | full | 11.53% | -21.45% | 0.939 | 3351 |
| BLEND_E45_A65 | 0.65 | oof_2011_2018 | 9.12% | -16.12% | 0.939 | 1495 |
| BLEND_E45_A65 | 0.65 | validation_2019_2022 | 10.88% | -21.45% | 0.939 | 977 |
| BLEND_E45_A65 | 0.65 | sealed_2023_plus | 17.00% | -9.41% | 0.939 | 879 |
| BLEND_E45_A65 | 0.65 | heldout_2019_plus | 13.77% | -21.45% | 0.939 | 1856 |
| BLEND_E45_A70 | 0.70 | full | 11.42% | -21.37% | 0.935 | 3351 |
| BLEND_E45_A70 | 0.70 | oof_2011_2018 | 9.09% | -16.09% | 0.935 | 1495 |
| BLEND_E45_A70 | 0.70 | validation_2019_2022 | 10.76% | -21.37% | 0.935 | 977 |
| BLEND_E45_A70 | 0.70 | sealed_2023_plus | 16.76% | -9.44% | 0.935 | 879 |
| BLEND_E45_A70 | 0.70 | heldout_2019_plus | 13.59% | -21.37% | 0.935 | 1856 |
| BLEND_E45_A75 | 0.75 | full | 11.36% | -21.28% | 0.930 | 3351 |
| BLEND_E45_A75 | 0.75 | oof_2011_2018 | 9.08% | -16.05% | 0.930 | 1495 |
| BLEND_E45_A75 | 0.75 | validation_2019_2022 | 10.73% | -21.28% | 0.930 | 977 |
| BLEND_E45_A75 | 0.75 | sealed_2023_plus | 16.57% | -9.50% | 0.930 | 879 |
| BLEND_E45_A75 | 0.75 | heldout_2019_plus | 13.49% | -21.28% | 0.930 | 1856 |
| BLEND_E45_A80 | 0.80 | full | 11.23% | -21.19% | 0.925 | 3351 |
| BLEND_E45_A80 | 0.80 | oof_2011_2018 | 9.05% | -16.02% | 0.925 | 1495 |
| BLEND_E45_A80 | 0.80 | validation_2019_2022 | 10.58% | -21.19% | 0.925 | 977 |
| BLEND_E45_A80 | 0.80 | sealed_2023_plus | 16.30% | -9.52% | 0.925 | 879 |
| BLEND_E45_A80 | 0.80 | heldout_2019_plus | 13.28% | -21.19% | 0.925 | 1856 |
| BLEND_E45_A85 | 0.85 | full | 11.15% | -21.10% | 0.921 | 3351 |
| BLEND_E45_A85 | 0.85 | oof_2011_2018 | 9.01% | -15.92% | 0.921 | 1495 |
| BLEND_E45_A85 | 0.85 | validation_2019_2022 | 10.46% | -21.10% | 0.921 | 977 |
| BLEND_E45_A85 | 0.85 | sealed_2023_plus | 16.16% | -9.50% | 0.921 | 879 |
| BLEND_E45_A85 | 0.85 | heldout_2019_plus | 13.15% | -21.10% | 0.921 | 1856 |
| BLEND_E45_A90 | 0.90 | full | 11.04% | -21.01% | 0.916 | 3351 |
| BLEND_E45_A90 | 0.90 | oof_2011_2018 | 8.99% | -15.85% | 0.916 | 1495 |
| BLEND_E45_A90 | 0.90 | validation_2019_2022 | 10.33% | -21.01% | 0.916 | 977 |
| BLEND_E45_A90 | 0.90 | sealed_2023_plus | 15.93% | -9.52% | 0.916 | 879 |
| BLEND_E45_A90 | 0.90 | heldout_2019_plus | 12.97% | -21.01% | 0.916 | 1856 |
| BLEND_E45_A95 | 0.95 | full | 10.94% | -20.92% | 0.911 | 3351 |
| BLEND_E45_A95 | 0.95 | oof_2011_2018 | 8.96% | -15.73% | 0.911 | 1495 |
| BLEND_E45_A95 | 0.95 | validation_2019_2022 | 10.18% | -20.92% | 0.911 | 977 |
| BLEND_E45_A95 | 0.95 | sealed_2023_plus | 15.76% | -9.53% | 0.911 | 879 |
| BLEND_E45_A95 | 0.95 | heldout_2019_plus | 12.81% | -20.92% | 0.911 | 1856 |
| CHAL_E45_E3 | 1.00 | full | 10.91% | -20.83% | 0.907 | 3351 |
| CHAL_E45_E3 | 1.00 | oof_2011_2018 | 8.92% | -15.72% | 0.907 | 1495 |
| CHAL_E45_E3 | 1.00 | validation_2019_2022 | 10.07% | -20.83% | 0.907 | 977 |
| CHAL_E45_E3 | 1.00 | sealed_2023_plus | 15.86% | -9.55% | 0.907 | 879 |
| CHAL_E45_E3 | 1.00 | heldout_2019_plus | 12.79% | -20.83% | 0.907 | 1856 |

## Deltas vs BASE (focus windows)

| Book | α | Window | MDD improve pp | CAGR giveback pp | MDD/giveback |
|---|---:|---|---:|---:|---:|
| BLEND_E45_A05 | 0.05 | heldout_2019_plus | +0.70 | +0.96 | +0.73 |
| BLEND_E45_A05 | 0.05 | sealed_2023_plus | +2.78 | +1.42 | +1.96 |
| BLEND_E45_A05 | 0.05 | full | +0.70 | +0.42 | +1.66 |
| BLEND_E45_A10 | 0.10 | heldout_2019_plus | +0.80 | +1.51 | +0.53 |
| BLEND_E45_A10 | 0.10 | sealed_2023_plus | +3.65 | +2.12 | +1.73 |
| BLEND_E45_A10 | 0.10 | full | +0.80 | +0.70 | +1.14 |
| BLEND_E45_A15 | 0.15 | heldout_2019_plus | +0.64 | +1.96 | +0.32 |
| BLEND_E45_A15 | 0.15 | sealed_2023_plus | +4.30 | +2.92 | +1.47 |
| BLEND_E45_A15 | 0.15 | full | +0.64 | +0.94 | +0.68 |
| BLEND_E45_A20 | 0.20 | heldout_2019_plus | +0.41 | +2.39 | +0.17 |
| BLEND_E45_A20 | 0.20 | sealed_2023_plus | +4.77 | +3.71 | +1.29 |
| BLEND_E45_A20 | 0.20 | full | +0.41 | +1.16 | +0.35 |
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | +0.45 | +2.72 | +0.17 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | +4.75 | +4.32 | +1.10 |
| BLEND_E45_A25 | 0.25 | full | +0.45 | +1.33 | +0.34 |
| BLEND_E45_A30 | 0.30 | heldout_2019_plus | +0.62 | +2.95 | +0.21 |
| BLEND_E45_A30 | 0.30 | sealed_2023_plus | +4.76 | +4.76 | +1.00 |
| BLEND_E45_A30 | 0.30 | full | +0.62 | +1.44 | +0.43 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | +0.65 | +3.14 | +0.21 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | +4.76 | +5.23 | +0.91 |
| BLEND_E45_A35 | 0.35 | full | +0.65 | +1.53 | +0.43 |
| BLEND_E45_A40 | 0.40 | heldout_2019_plus | +0.68 | +3.44 | +0.20 |
| BLEND_E45_A40 | 0.40 | sealed_2023_plus | +4.81 | +5.94 | +0.81 |
| BLEND_E45_A40 | 0.40 | full | +0.68 | +1.69 | +0.40 |
| BLEND_E45_A45 | 0.45 | heldout_2019_plus | +0.72 | +3.69 | +0.19 |
| BLEND_E45_A45 | 0.45 | sealed_2023_plus | +4.83 | +6.47 | +0.75 |
| BLEND_E45_A45 | 0.45 | full | +0.72 | +1.82 | +0.40 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | +0.78 | +3.91 | +0.20 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | +4.83 | +6.93 | +0.70 |
| BLEND_E45_A50 | 0.50 | full | +0.78 | +1.94 | +0.40 |
| BLEND_E45_A55 | 0.55 | heldout_2019_plus | +0.86 | +4.11 | +0.21 |
| BLEND_E45_A55 | 0.55 | sealed_2023_plus | +4.80 | +7.31 | +0.66 |
| BLEND_E45_A55 | 0.55 | full | +0.86 | +2.05 | +0.42 |
| BLEND_E45_A60 | 0.60 | heldout_2019_plus | +1.00 | +4.31 | +0.23 |
| BLEND_E45_A60 | 0.60 | sealed_2023_plus | +4.72 | +7.70 | +0.61 |
| BLEND_E45_A60 | 0.60 | full | +1.00 | +2.18 | +0.46 |
| BLEND_E45_A65 | 0.65 | heldout_2019_plus | +1.09 | +4.44 | +0.25 |
| BLEND_E45_A65 | 0.65 | sealed_2023_plus | +4.68 | +7.89 | +0.59 |
| BLEND_E45_A65 | 0.65 | full | +1.09 | +2.26 | +0.48 |
| BLEND_E45_A70 | 0.70 | heldout_2019_plus | +1.17 | +4.61 | +0.25 |
| BLEND_E45_A70 | 0.70 | sealed_2023_plus | +4.64 | +8.13 | +0.57 |
| BLEND_E45_A70 | 0.70 | full | +1.17 | +2.37 | +0.50 |
| BLEND_E45_A75 | 0.75 | heldout_2019_plus | +1.26 | +4.72 | +0.27 |
| BLEND_E45_A75 | 0.75 | sealed_2023_plus | +4.58 | +8.32 | +0.55 |
| BLEND_E45_A75 | 0.75 | full | +1.26 | +2.43 | +0.52 |
| BLEND_E45_A80 | 0.80 | heldout_2019_plus | +1.35 | +4.93 | +0.27 |
| BLEND_E45_A80 | 0.80 | sealed_2023_plus | +4.56 | +8.59 | +0.53 |
| BLEND_E45_A80 | 0.80 | full | +1.35 | +2.56 | +0.53 |
| BLEND_E45_A85 | 0.85 | heldout_2019_plus | +1.44 | +5.06 | +0.29 |
| BLEND_E45_A85 | 0.85 | sealed_2023_plus | +4.59 | +8.73 | +0.53 |
| BLEND_E45_A85 | 0.85 | full | +1.44 | +2.64 | +0.55 |
| BLEND_E45_A90 | 0.90 | heldout_2019_plus | +1.53 | +5.23 | +0.29 |
| BLEND_E45_A90 | 0.90 | sealed_2023_plus | +4.57 | +8.96 | +0.51 |
| BLEND_E45_A90 | 0.90 | full | +1.53 | +2.75 | +0.56 |
| BLEND_E45_A95 | 0.95 | heldout_2019_plus | +1.62 | +5.39 | +0.30 |
| BLEND_E45_A95 | 0.95 | sealed_2023_plus | +4.56 | +9.13 | +0.50 |
| BLEND_E45_A95 | 0.95 | full | +1.62 | +2.85 | +0.57 |
| CHAL_E45_E3 | 1.00 | heldout_2019_plus | +1.71 | +5.41 | +0.32 |
| CHAL_E45_E3 | 1.00 | sealed_2023_plus | +4.54 | +9.03 | +0.50 |
| CHAL_E45_E3 | 1.00 | full | +1.71 | +2.88 | +0.59 |

## Held-out heuristic pick (paper only)

- Preferred partial α on held-out score `MDD_improve − 0.5·|CAGR_giveback|`: **α=0.05** (`BLEND_E45_A05`)
- Held-out MDD improve **+0.70 pp**; CAGR giveback **+0.96 pp**
- This is a **screen hint**, not a stitch / Soft-Frozen license.

### Held-out top-5 by score

| α | Book | MDD improve pp | CAGR giveback pp | score |
|---:|---|---:|---:|---:|
| 0.05 | BLEND_E45_A05 | +0.70 | +0.96 | +0.22 |
| 0.10 | BLEND_E45_A10 | +0.80 | +1.51 | +0.04 |
| 0.15 | BLEND_E45_A15 | +0.64 | +1.96 | -0.34 |
| 0.20 | BLEND_E45_A20 | +0.41 | +2.39 | -0.79 |
| 0.30 | BLEND_E45_A30 | +0.62 | +2.95 | -0.85 |

### Held-out Pareto (higher MDD improve for given/lower giveback)

| α | MDD improve pp | CAGR giveback pp |
|---:|---:|---:|
| 0.05 | +0.70 | +0.96 |
| 0.10 | +0.80 | +1.51 |
| 0.55 | +0.86 | +4.11 |
| 0.60 | +1.00 | +4.31 |
| 0.65 | +1.09 | +4.44 |
| 0.70 | +1.17 | +4.61 |
| 0.75 | +1.26 | +4.72 |
| 0.80 | +1.35 | +4.93 |
| 0.85 | +1.44 | +5.06 |
| 0.90 | +1.53 | +5.23 |
| 0.95 | +1.62 | +5.39 |
| 1.00 | +1.71 | +5.41 |

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

`E45_BLEND_ALPHA_GRID_FINE_2026-09-06__STEP0P05__PAPER_ONLY__STITCH_FORBIDDEN`

Artifacts:
- `/workspace/repro/e45-blend-alpha-grid-fine/reports/e45_blend_alpha_grid_fine.json`
- `/workspace/repro/e45-blend-alpha-grid-fine/outputs/blend_alpha_window_metrics.csv`
- `/workspace/repro/e45-blend-alpha-grid-fine/outputs/blend_alpha_deltas_vs_base.csv`
