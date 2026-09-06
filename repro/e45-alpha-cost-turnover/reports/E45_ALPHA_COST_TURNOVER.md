# E45 PAPER Alpha Cost / Turnover Stress

Generated: `2026-09-06T04:33:04.078827+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; live stitch **FORBIDDEN**; observe unchanged.

## Setup

- Profile: frozen `E3_VOLTARGET_WINNER`
- Alphas: 0.0, 0.05, 0.1, 0.25, 1.0
- Cost multiples: 0×, 1×, 2×, 3× on `BUY_FEE, SELL_FEE, SLIP, TAX_STOCK, TAX_ETF`
- Turnover: annualized |gross traded| / mean NAV

## Held-out deltas vs BASE (by cost ×)

| Book | α | ×cost | MDD Δpp | Giveback pp | Score | TO/yr | fees |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0.00 | 0 | +0.00 | +0.00 | +0.00 | 2.195 | 0 |
| BLEND_E45_A05 | 0.05 | 0 | +0.69 | +0.94 | +0.22 | 2.234 | 0 |
| BLEND_E45_A10 | 0.10 | 0 | +0.74 | +1.48 | -0.00 | 2.270 | 0 |
| BLEND_E45_A25 | 0.25 | 0 | +0.45 | +2.66 | -0.88 | 2.310 | 0 |
| CHAL_E45_E3 | 1.00 | 0 | +1.74 | +5.29 | -0.91 | 2.312 | 0 |
| BASE_E16_E18_E22_v2s | 0.00 | 1 | +0.00 | +0.00 | +0.00 | 2.186 | 391685 |
| BLEND_E45_A05 | 0.05 | 1 | +0.70 | +0.96 | +0.22 | 2.233 | 400184 |
| BLEND_E45_A10 | 0.10 | 1 | +0.80 | +1.51 | +0.04 | 2.260 | 402717 |
| BLEND_E45_A25 | 0.25 | 1 | +0.45 | +2.72 | -0.91 | 2.305 | 405460 |
| CHAL_E45_E3 | 1.00 | 1 | +1.71 | +5.41 | -1.00 | 2.309 | 388996 |
| BASE_E16_E18_E22_v2s | 0.00 | 2 | +0.00 | +0.00 | +0.00 | 2.178 | 746243 |
| BLEND_E45_A05 | 0.05 | 2 | +0.74 | +0.97 | +0.25 | 2.226 | 763092 |
| BLEND_E45_A10 | 0.10 | 2 | +0.88 | +1.53 | +0.12 | 2.263 | 770959 |
| BLEND_E45_A25 | 0.25 | 2 | +0.47 | +2.80 | -0.93 | 2.297 | 771034 |
| CHAL_E45_E3 | 1.00 | 2 | +1.71 | +5.52 | -1.05 | 2.310 | 742769 |
| BASE_E16_E18_E22_v2s | 0.00 | 3 | +0.00 | +0.00 | +0.00 | 2.176 | 1071122 |
| BLEND_E45_A05 | 0.05 | 3 | +0.76 | +0.99 | +0.26 | 2.216 | 1090071 |
| BLEND_E45_A10 | 0.10 | 3 | +0.98 | +1.55 | +0.20 | 2.249 | 1100550 |
| BLEND_E45_A25 | 0.25 | 3 | +0.56 | +2.89 | -0.88 | 2.289 | 1099956 |
| CHAL_E45_E3 | 1.00 | 3 | +1.75 | +5.64 | -1.08 | 2.309 | 1062782 |

## Mild-α survival on held-out (score≥0 / MDD helps)

| α | ×cost | MDD Δpp | Giveback | Score | score≥0 | MDD>0 |
|---:|---:|---:|---:|---:|:---:|:---:|
| 0.05 | 0 | +0.69 | +0.94 | +0.22 | Y | Y |
| 0.05 | 1 | +0.70 | +0.96 | +0.22 | Y | Y |
| 0.05 | 2 | +0.74 | +0.97 | +0.25 | Y | Y |
| 0.05 | 3 | +0.76 | +0.99 | +0.26 | Y | Y |
| 0.10 | 0 | +0.74 | +1.48 | -0.00 | N | Y |
| 0.10 | 1 | +0.80 | +1.51 | +0.04 | Y | Y |
| 0.10 | 2 | +0.88 | +1.53 | +0.12 | Y | Y |
| 0.10 | 3 | +0.98 | +1.55 | +0.20 | Y | Y |
| 0.25 | 0 | +0.45 | +2.66 | -0.88 | N | Y |
| 0.25 | 1 | +0.45 | +2.72 | -0.91 | N | Y |
| 0.25 | 2 | +0.47 | +2.80 | -0.93 | N | Y |
| 0.25 | 3 | +0.56 | +2.89 | -0.88 | N | Y |

## Turnover vs BASE at 1× (full sample)

| Book | α | TO/yr | ΔTO vs BASE | fills | fees@1× |
|---|---:|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0.00 | 2.186 | +0.00 | 6104 | 391685 |
| BLEND_E45_A05 | 0.05 | 2.233 | +0.05 | 6175 | 400184 |
| BLEND_E45_A10 | 0.10 | 2.260 | +0.07 | 6230 | 402717 |
| BLEND_E45_A25 | 0.25 | 2.305 | +0.12 | 6410 | 405460 |
| CHAL_E45_E3 | 1.00 | 2.309 | +0.12 | 6835 | 388996 |

## Read-through (paper)

1. Held-out @1× preferred among α>0: **`BLEND_E45_A05`**.
2. α=0.05 at 3× cost: score≥0=YES; MDD help=YES.
3. Compare turnover deltas — mild α should not explode trading vs BASE.
4. Does **not** open observe / authorize stitch.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · retired MDD narrative

## Reproduce

```bash
python3 scripts/e45_alpha_cost_turnover_paper.py
```

