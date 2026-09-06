# E45 PAPER Blend-Alpha Fine Grid (step 0.05)

Generated: `2026-09-06T01:11:19.436309+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.

## Definition

- Profile: E45 `E3_VOLTARGET_WINNER` (frozen winner lock **not** retuned)
- Blend: `exposure_α = (1−α)·1 + α·E45_exposure`
- Alphas: 0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00
- α=0 → BASE; α=1 → full CHAL_E45_E3 (same as operating observe challenger)

## Window metrics

| Book | α | Window | CAGR | MDD | mean_exp | n_days |
|---|---:|---|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0.00 | full | 13.78% | -22.64% | 1.000 | 3351 |
| BASE_E16_E18_E22_v2s | 0.00 | oof_2011_2018 | 8.85% | -17.41% | 1.000 | 1495 |
| BASE_E16_E18_E22_v2s | 0.00 | validation_2019_2022 | 12.33% | -22.64% | 1.000 | 977 |
| BASE_E16_E18_E22_v2s | 0.00 | sealed_2023_plus | 24.93% | -14.46% | 1.000 | 879 |
| BASE_E16_E18_E22_v2s | 0.00 | heldout_2019_plus | 18.23% | -22.64% | 1.000 | 1856 |
| BLEND_E45_A05 | 0.05 | full | 13.31% | -21.79% | 0.995 | 3351 |
| BLEND_E45_A05 | 0.05 | oof_2011_2018 | 9.03% | -17.31% | 0.995 | 1495 |
| BLEND_E45_A05 | 0.05 | validation_2019_2022 | 11.64% | -21.79% | 0.995 | 977 |
| BLEND_E45_A05 | 0.05 | sealed_2023_plus | 23.42% | -11.39% | 0.995 | 879 |
| BLEND_E45_A05 | 0.05 | heldout_2019_plus | 17.17% | -21.79% | 0.995 | 1856 |
| BLEND_E45_A10 | 0.10 | full | 13.05% | -21.69% | 0.991 | 3351 |
| BLEND_E45_A10 | 0.10 | oof_2011_2018 | 9.09% | -17.29% | 0.991 | 1495 |
| BLEND_E45_A10 | 0.10 | validation_2019_2022 | 11.23% | -21.69% | 0.991 | 977 |
| BLEND_E45_A10 | 0.10 | sealed_2023_plus | 22.74% | -10.58% | 0.991 | 879 |
| BLEND_E45_A10 | 0.10 | heldout_2019_plus | 16.64% | -21.69% | 0.991 | 1856 |
| BLEND_E45_A15 | 0.15 | full | 12.82% | -21.85% | 0.986 | 3351 |
| BLEND_E45_A15 | 0.15 | oof_2011_2018 | 9.12% | -17.07% | 0.986 | 1495 |
| BLEND_E45_A15 | 0.15 | validation_2019_2022 | 11.03% | -21.85% | 0.986 | 977 |
| BLEND_E45_A15 | 0.15 | sealed_2023_plus | 21.98% | -9.81% | 0.986 | 879 |
| BLEND_E45_A15 | 0.15 | heldout_2019_plus | 16.17% | -21.85% | 0.986 | 1856 |
| BLEND_E45_A20 | 0.20 | full | 12.54% | -22.02% | 0.981 | 3351 |
| BLEND_E45_A20 | 0.20 | oof_2011_2018 | 9.11% | -16.84% | 0.981 | 1495 |
| BLEND_E45_A20 | 0.20 | validation_2019_2022 | 10.90% | -22.02% | 0.981 | 977 |
| BLEND_E45_A20 | 0.20 | sealed_2023_plus | 21.09% | -9.32% | 0.981 | 879 |
| BLEND_E45_A20 | 0.20 | heldout_2019_plus | 15.68% | -22.02% | 0.981 | 1856 |
| BLEND_E45_A25 | 0.25 | full | 12.40% | -22.01% | 0.977 | 3351 |
| BLEND_E45_A25 | 0.25 | oof_2011_2018 | 9.13% | -16.57% | 0.977 | 1495 |
| BLEND_E45_A25 | 0.25 | validation_2019_2022 | 10.85% | -22.01% | 0.977 | 977 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | 20.56% | -9.33% | 0.977 | 879 |
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | 15.41% | -22.01% | 0.977 | 1856 |
| BLEND_E45_A30 | 0.30 | full | 12.29% | -21.84% | 0.972 | 3351 |
| BLEND_E45_A30 | 0.30 | oof_2011_2018 | 9.15% | -16.43% | 0.972 | 1495 |
| BLEND_E45_A30 | 0.30 | validation_2019_2022 | 10.82% | -21.84% | 0.972 | 977 |
| BLEND_E45_A30 | 0.30 | sealed_2023_plus | 20.08% | -9.33% | 0.972 | 879 |
| BLEND_E45_A30 | 0.30 | heldout_2019_plus | 15.16% | -21.84% | 0.972 | 1856 |
| BLEND_E45_A35 | 0.35 | full | 12.18% | -21.82% | 0.967 | 3351 |
| BLEND_E45_A35 | 0.35 | oof_2011_2018 | 9.16% | -16.32% | 0.967 | 1495 |
| BLEND_E45_A35 | 0.35 | validation_2019_2022 | 10.83% | -21.82% | 0.967 | 977 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | 19.62% | -9.32% | 0.967 | 879 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | 14.96% | -21.82% | 0.967 | 1856 |
| BLEND_E45_A40 | 0.40 | full | 12.04% | -21.79% | 0.963 | 3351 |
| BLEND_E45_A40 | 0.40 | oof_2011_2018 | 9.17% | -16.23% | 0.963 | 1495 |
| BLEND_E45_A40 | 0.40 | validation_2019_2022 | 10.92% | -21.79% | 0.963 | 977 |
| BLEND_E45_A40 | 0.40 | sealed_2023_plus | 18.90% | -9.29% | 0.963 | 879 |
| BLEND_E45_A40 | 0.40 | heldout_2019_plus | 14.67% | -21.79% | 0.963 | 1856 |
| BLEND_E45_A45 | 0.45 | full | 11.92% | -21.74% | 0.958 | 3351 |
| BLEND_E45_A45 | 0.45 | oof_2011_2018 | 9.18% | -16.15% | 0.958 | 1495 |
| BLEND_E45_A45 | 0.45 | validation_2019_2022 | 10.94% | -21.74% | 0.958 | 977 |
| BLEND_E45_A45 | 0.45 | sealed_2023_plus | 18.38% | -9.26% | 0.958 | 879 |
| BLEND_E45_A45 | 0.45 | heldout_2019_plus | 14.44% | -21.74% | 0.958 | 1856 |
| BLEND_E45_A50 | 0.50 | full | 11.78% | -21.69% | 0.953 | 3351 |
| BLEND_E45_A50 | 0.50 | oof_2011_2018 | 9.18% | -16.08% | 0.953 | 1495 |
| BLEND_E45_A50 | 0.50 | validation_2019_2022 | 10.86% | -21.69% | 0.953 | 977 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | 17.95% | -9.25% | 0.953 | 879 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | 14.19% | -21.69% | 0.953 | 1856 |
| BLEND_E45_A55 | 0.55 | full | 11.68% | -21.60% | 0.949 | 3351 |
| BLEND_E45_A55 | 0.55 | oof_2011_2018 | 9.17% | -16.02% | 0.949 | 1495 |
| BLEND_E45_A55 | 0.55 | validation_2019_2022 | 10.83% | -21.60% | 0.949 | 977 |
| BLEND_E45_A55 | 0.55 | sealed_2023_plus | 17.59% | -9.28% | 0.949 | 879 |
| BLEND_E45_A55 | 0.55 | heldout_2019_plus | 14.01% | -21.60% | 0.949 | 1856 |
| BLEND_E45_A60 | 0.60 | full | 11.57% | -21.46% | 0.944 | 3351 |
| BLEND_E45_A60 | 0.60 | oof_2011_2018 | 9.15% | -15.94% | 0.944 | 1495 |
| BLEND_E45_A60 | 0.60 | validation_2019_2022 | 10.82% | -21.46% | 0.944 | 977 |
| BLEND_E45_A60 | 0.60 | sealed_2023_plus | 17.19% | -9.36% | 0.944 | 879 |
| BLEND_E45_A60 | 0.60 | heldout_2019_plus | 13.82% | -21.46% | 0.944 | 1856 |
| BLEND_E45_A65 | 0.65 | full | 11.47% | -21.37% | 0.939 | 3351 |
| BLEND_E45_A65 | 0.65 | oof_2011_2018 | 9.11% | -15.95% | 0.939 | 1495 |
| BLEND_E45_A65 | 0.65 | validation_2019_2022 | 10.76% | -21.37% | 0.939 | 977 |
| BLEND_E45_A65 | 0.65 | sealed_2023_plus | 16.94% | -9.39% | 0.939 | 879 |
| BLEND_E45_A65 | 0.65 | heldout_2019_plus | 13.67% | -21.37% | 0.939 | 1856 |
| BLEND_E45_A70 | 0.70 | full | 11.36% | -21.29% | 0.935 | 3351 |
| BLEND_E45_A70 | 0.70 | oof_2011_2018 | 9.08% | -15.93% | 0.935 | 1495 |
| BLEND_E45_A70 | 0.70 | validation_2019_2022 | 10.62% | -21.29% | 0.935 | 977 |
| BLEND_E45_A70 | 0.70 | sealed_2023_plus | 16.72% | -9.43% | 0.935 | 879 |
| BLEND_E45_A70 | 0.70 | heldout_2019_plus | 13.49% | -21.29% | 0.935 | 1856 |
| BLEND_E45_A75 | 0.75 | full | 11.28% | -21.20% | 0.930 | 3351 |
| BLEND_E45_A75 | 0.75 | oof_2011_2018 | 9.08% | -15.89% | 0.930 | 1495 |
| BLEND_E45_A75 | 0.75 | validation_2019_2022 | 10.55% | -21.20% | 0.930 | 977 |
| BLEND_E45_A75 | 0.75 | sealed_2023_plus | 16.50% | -9.46% | 0.930 | 879 |
| BLEND_E45_A75 | 0.75 | heldout_2019_plus | 13.35% | -21.20% | 0.930 | 1856 |
| BLEND_E45_A80 | 0.80 | full | 11.19% | -21.11% | 0.925 | 3351 |
| BLEND_E45_A80 | 0.80 | oof_2011_2018 | 9.06% | -15.78% | 0.925 | 1495 |
| BLEND_E45_A80 | 0.80 | validation_2019_2022 | 10.46% | -21.11% | 0.925 | 977 |
| BLEND_E45_A80 | 0.80 | sealed_2023_plus | 16.27% | -9.51% | 0.925 | 879 |
| BLEND_E45_A80 | 0.80 | heldout_2019_plus | 13.20% | -21.11% | 0.925 | 1856 |
| BLEND_E45_A85 | 0.85 | full | 11.09% | -21.02% | 0.921 | 3351 |
| BLEND_E45_A85 | 0.85 | oof_2011_2018 | 9.01% | -15.73% | 0.921 | 1495 |
| BLEND_E45_A85 | 0.85 | validation_2019_2022 | 10.34% | -21.02% | 0.921 | 977 |
| BLEND_E45_A85 | 0.85 | sealed_2023_plus | 16.09% | -9.53% | 0.921 | 879 |
| BLEND_E45_A85 | 0.85 | heldout_2019_plus | 13.05% | -21.02% | 0.921 | 1856 |
| BLEND_E45_A90 | 0.90 | full | 11.00% | -20.93% | 0.916 | 3351 |
| BLEND_E45_A90 | 0.90 | oof_2011_2018 | 8.98% | -15.68% | 0.916 | 1495 |
| BLEND_E45_A90 | 0.90 | validation_2019_2022 | 10.21% | -20.93% | 0.916 | 977 |
| BLEND_E45_A90 | 0.90 | sealed_2023_plus | 15.93% | -9.51% | 0.916 | 879 |
| BLEND_E45_A90 | 0.90 | heldout_2019_plus | 12.91% | -20.93% | 0.916 | 1856 |
| BLEND_E45_A95 | 0.95 | full | 10.90% | -20.85% | 0.911 | 3351 |
| BLEND_E45_A95 | 0.95 | oof_2011_2018 | 8.95% | -15.62% | 0.911 | 1495 |
| BLEND_E45_A95 | 0.95 | validation_2019_2022 | 10.08% | -20.85% | 0.911 | 977 |
| BLEND_E45_A95 | 0.95 | sealed_2023_plus | 15.72% | -9.52% | 0.911 | 879 |
| BLEND_E45_A95 | 0.95 | heldout_2019_plus | 12.74% | -20.85% | 0.911 | 1856 |
| CHAL_E45_E3_FULL | 1.00 | full | 10.79% | -20.76% | 0.907 | 3351 |
| CHAL_E45_E3_FULL | 1.00 | oof_2011_2018 | 8.91% | -15.57% | 0.907 | 1495 |
| CHAL_E45_E3_FULL | 1.00 | validation_2019_2022 | 9.97% | -20.76% | 0.907 | 977 |
| CHAL_E45_E3_FULL | 1.00 | sealed_2023_plus | 15.52% | -9.56% | 0.907 | 879 |
| CHAL_E45_E3_FULL | 1.00 | heldout_2019_plus | 12.59% | -20.76% | 0.907 | 1856 |

## Deltas vs BASE (focus windows)

| Book | α | Window | MDD improve pp | CAGR giveback pp | MDD/giveback |
|---|---:|---|---:|---:|---:|
| BLEND_E45_A05 | 0.05 | heldout_2019_plus | +0.85 | +1.07 | +0.80 |
| BLEND_E45_A05 | 0.05 | sealed_2023_plus | +3.07 | +1.50 | +2.04 |
| BLEND_E45_A05 | 0.05 | full | +0.85 | +0.47 | +1.81 |
| BLEND_E45_A10 | 0.10 | heldout_2019_plus | +0.95 | +1.60 | +0.60 |
| BLEND_E45_A10 | 0.10 | sealed_2023_plus | +3.88 | +2.19 | +1.77 |
| BLEND_E45_A10 | 0.10 | full | +0.95 | +0.73 | +1.30 |
| BLEND_E45_A15 | 0.15 | heldout_2019_plus | +0.79 | +2.06 | +0.38 |
| BLEND_E45_A15 | 0.15 | sealed_2023_plus | +4.65 | +2.94 | +1.58 |
| BLEND_E45_A15 | 0.15 | full | +0.79 | +0.97 | +0.82 |
| BLEND_E45_A20 | 0.20 | heldout_2019_plus | +0.62 | +2.55 | +0.24 |
| BLEND_E45_A20 | 0.20 | sealed_2023_plus | +5.14 | +3.84 | +1.34 |
| BLEND_E45_A20 | 0.20 | full | +0.62 | +1.24 | +0.50 |
| BLEND_E45_A25 | 0.25 | heldout_2019_plus | +0.63 | +2.83 | +0.22 |
| BLEND_E45_A25 | 0.25 | sealed_2023_plus | +5.13 | +4.36 | +1.18 |
| BLEND_E45_A25 | 0.25 | full | +0.63 | +1.38 | +0.46 |
| BLEND_E45_A30 | 0.30 | heldout_2019_plus | +0.79 | +3.07 | +0.26 |
| BLEND_E45_A30 | 0.30 | sealed_2023_plus | +5.12 | +4.85 | +1.06 |
| BLEND_E45_A30 | 0.30 | full | +0.79 | +1.49 | +0.53 |
| BLEND_E45_A35 | 0.35 | heldout_2019_plus | +0.82 | +3.28 | +0.25 |
| BLEND_E45_A35 | 0.35 | sealed_2023_plus | +5.14 | +5.31 | +0.97 |
| BLEND_E45_A35 | 0.35 | full | +0.82 | +1.60 | +0.51 |
| BLEND_E45_A40 | 0.40 | heldout_2019_plus | +0.85 | +3.57 | +0.24 |
| BLEND_E45_A40 | 0.40 | sealed_2023_plus | +5.17 | +6.02 | +0.86 |
| BLEND_E45_A40 | 0.40 | full | +0.85 | +1.75 | +0.49 |
| BLEND_E45_A45 | 0.45 | heldout_2019_plus | +0.90 | +3.80 | +0.24 |
| BLEND_E45_A45 | 0.45 | sealed_2023_plus | +5.20 | +6.54 | +0.79 |
| BLEND_E45_A45 | 0.45 | full | +0.90 | +1.87 | +0.48 |
| BLEND_E45_A50 | 0.50 | heldout_2019_plus | +0.95 | +4.04 | +0.24 |
| BLEND_E45_A50 | 0.50 | sealed_2023_plus | +5.21 | +6.98 | +0.75 |
| BLEND_E45_A50 | 0.50 | full | +0.95 | +2.00 | +0.48 |
| BLEND_E45_A55 | 0.55 | heldout_2019_plus | +1.03 | +4.22 | +0.24 |
| BLEND_E45_A55 | 0.55 | sealed_2023_plus | +5.18 | +7.34 | +0.71 |
| BLEND_E45_A55 | 0.55 | full | +1.03 | +2.10 | +0.49 |
| BLEND_E45_A60 | 0.60 | heldout_2019_plus | +1.18 | +4.42 | +0.27 |
| BLEND_E45_A60 | 0.60 | sealed_2023_plus | +5.09 | +7.73 | +0.66 |
| BLEND_E45_A60 | 0.60 | full | +1.18 | +2.21 | +0.53 |
| BLEND_E45_A65 | 0.65 | heldout_2019_plus | +1.27 | +4.56 | +0.28 |
| BLEND_E45_A65 | 0.65 | sealed_2023_plus | +5.07 | +7.98 | +0.63 |
| BLEND_E45_A65 | 0.65 | full | +1.27 | +2.31 | +0.55 |
| BLEND_E45_A70 | 0.70 | heldout_2019_plus | +1.35 | +4.74 | +0.28 |
| BLEND_E45_A70 | 0.70 | sealed_2023_plus | +5.03 | +8.21 | +0.61 |
| BLEND_E45_A70 | 0.70 | full | +1.35 | +2.42 | +0.56 |
| BLEND_E45_A75 | 0.75 | heldout_2019_plus | +1.44 | +4.88 | +0.29 |
| BLEND_E45_A75 | 0.75 | sealed_2023_plus | +5.00 | +8.42 | +0.59 |
| BLEND_E45_A75 | 0.75 | full | +1.44 | +2.50 | +0.58 |
| BLEND_E45_A80 | 0.80 | heldout_2019_plus | +1.53 | +5.03 | +0.30 |
| BLEND_E45_A80 | 0.80 | sealed_2023_plus | +4.94 | +8.65 | +0.57 |
| BLEND_E45_A80 | 0.80 | full | +1.53 | +2.59 | +0.59 |
| BLEND_E45_A85 | 0.85 | heldout_2019_plus | +1.62 | +5.19 | +0.31 |
| BLEND_E45_A85 | 0.85 | sealed_2023_plus | +4.93 | +8.84 | +0.56 |
| BLEND_E45_A85 | 0.85 | full | +1.62 | +2.69 | +0.60 |
| BLEND_E45_A90 | 0.90 | heldout_2019_plus | +1.70 | +5.33 | +0.32 |
| BLEND_E45_A90 | 0.90 | sealed_2023_plus | +4.95 | +8.99 | +0.55 |
| BLEND_E45_A90 | 0.90 | full | +1.70 | +2.78 | +0.61 |
| BLEND_E45_A95 | 0.95 | heldout_2019_plus | +1.79 | +5.50 | +0.33 |
| BLEND_E45_A95 | 0.95 | sealed_2023_plus | +4.94 | +9.21 | +0.54 |
| BLEND_E45_A95 | 0.95 | full | +1.79 | +2.89 | +0.62 |
| CHAL_E45_E3_FULL | 1.00 | heldout_2019_plus | +1.88 | +5.65 | +0.33 |
| CHAL_E45_E3_FULL | 1.00 | sealed_2023_plus | +4.90 | +9.40 | +0.52 |
| CHAL_E45_E3_FULL | 1.00 | full | +1.88 | +2.99 | +0.63 |

## Held-out heuristic pick (paper only)

- Preferred partial α on held-out score `MDD_improve − 0.5·|CAGR_giveback|`: **α=0.05** (`BLEND_E45_A05`)
- Held-out MDD improve **+0.85 pp**; CAGR giveback **+1.07 pp**
- This is a **screen hint**, not a stitch / Soft-Frozen license.

### Held-out top-5 by score

| α | Book | MDD improve pp | CAGR giveback pp | score |
|---:|---|---:|---:|---:|
| 0.05 | BLEND_E45_A05 | +0.85 | +1.07 | +0.32 |
| 0.10 | BLEND_E45_A10 | +0.95 | +1.60 | +0.15 |
| 0.15 | BLEND_E45_A15 | +0.79 | +2.06 | -0.24 |
| 0.20 | BLEND_E45_A20 | +0.62 | +2.55 | -0.66 |
| 0.30 | BLEND_E45_A30 | +0.79 | +3.07 | -0.74 |

### Held-out Pareto (higher MDD improve for given/lower giveback)

| α | MDD improve pp | CAGR giveback pp |
|---:|---:|---:|
| 0.05 | +0.85 | +1.07 |
| 0.10 | +0.95 | +1.60 |
| 0.50 | +0.95 | +4.04 |
| 0.55 | +1.03 | +4.22 |
| 0.60 | +1.18 | +4.42 |
| 0.65 | +1.27 | +4.56 |
| 0.70 | +1.35 | +4.74 |
| 0.75 | +1.44 | +4.88 |
| 0.80 | +1.53 | +5.03 |
| 0.85 | +1.62 | +5.19 |
| 0.90 | +1.70 | +5.33 |
| 0.95 | +1.79 | +5.50 |
| 1.00 | +1.88 | +5.65 |

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

`E45_BLEND_ALPHA_GRID_FINE_2026-09-06__STEP0P05__PAPER_ONLY__STITCH_FORBIDDEN`

Artifacts:
- `/workspace/repro/e45-blend-alpha-grid-fine/reports/e45_blend_alpha_grid_fine.json`
- `/workspace/repro/e45-blend-alpha-grid-fine/outputs/blend_alpha_window_metrics.csv`
- `/workspace/repro/e45-blend-alpha-grid-fine/outputs/blend_alpha_deltas_vs_base.csv`
