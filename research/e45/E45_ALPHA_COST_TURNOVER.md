# E45 PAPER Alpha Cost / Turnover Stress

Generated: `2026-09-06T01:45:24.801413+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; live stitch **FORBIDDEN**; observe unchanged.

## Setup

- Profile: frozen `E3_VOLTARGET_WINNER`
- Alphas: 0.0, 0.05, 0.1, 0.25, 1.0
- Cost multiples: 0×, 1×, 2×, 3× on `BUY_FEE, SELL_FEE, SLIP, TAX_STOCK, TAX_ETF`
- Turnover: annualized |gross traded| / mean NAV

## Held-out deltas vs BASE (by cost ×)

| Book | α | ×cost | MDD Δpp | Giveback pp | Score | TO/yr | fees |
|---|---:|---:|---:|---:|---:|---:|---:|
| BASE | 0.00 | 0 | +0.00 | +0.00 | +0.00 | 2.245 | 0 |
| BLEND_A05 | 0.05 | 0 | +0.84 | +1.04 | +0.32 | 2.279 | 0 |
| BLEND_A10 | 0.10 | 0 | +0.90 | +1.57 | +0.12 | 2.338 | 0 |
| BLEND_A25 | 0.25 | 0 | +0.65 | +2.74 | -0.72 | 2.358 | 0 |
| FULL_E45 | 1.00 | 0 | +1.89 | +5.53 | -0.88 | 2.354 | 0 |
| BASE | 0.00 | 1 | +0.00 | +0.00 | +0.00 | 2.240 | 400790 |
| BLEND_A05 | 0.05 | 1 | +0.85 | +1.07 | +0.32 | 2.280 | 407845 |
| BLEND_A10 | 0.10 | 1 | +0.95 | +1.60 | +0.15 | 2.323 | 413574 |
| BLEND_A25 | 0.25 | 1 | +0.63 | +2.83 | -0.78 | 2.354 | 413547 |
| FULL_E45 | 1.00 | 1 | +1.88 | +5.65 | -0.94 | 2.352 | 394843 |
| BASE | 0.00 | 2 | +0.00 | +0.00 | +0.00 | 2.236 | 764500 |
| BLEND_A05 | 0.05 | 2 | +0.87 | +1.01 | +0.36 | 2.274 | 777176 |
| BLEND_A10 | 0.10 | 2 | +1.05 | +1.59 | +0.26 | 2.322 | 789156 |
| BLEND_A25 | 0.25 | 2 | +0.68 | +2.87 | -0.76 | 2.349 | 786079 |
| FULL_E45 | 1.00 | 2 | +1.90 | +5.71 | -0.96 | 2.350 | 752828 |
| BASE | 0.00 | 3 | +0.00 | +0.00 | +0.00 | 2.224 | 1092641 |
| BLEND_A05 | 0.05 | 3 | +0.90 | +1.03 | +0.38 | 2.270 | 1112596 |
| BLEND_A10 | 0.10 | 3 | +1.14 | +1.62 | +0.33 | 2.316 | 1128260 |
| BLEND_A25 | 0.25 | 3 | +0.75 | +2.94 | -0.72 | 2.344 | 1122903 |
| FULL_E45 | 1.00 | 3 | +1.92 | +5.82 | -0.99 | 2.346 | 1076272 |

## Mild-α survival on held-out (score≥0 / MDD helps)

| α | ×cost | MDD Δpp | Giveback | Score | score≥0 | MDD>0 |
|---:|---:|---:|---:|---:|:---:|:---:|
| 0.05 | 0 | +0.84 | +1.04 | +0.32 | Y | Y |
| 0.05 | 1 | +0.85 | +1.07 | +0.32 | Y | Y |
| 0.05 | 2 | +0.87 | +1.01 | +0.36 | Y | Y |
| 0.05 | 3 | +0.90 | +1.03 | +0.38 | Y | Y |
| 0.10 | 0 | +0.90 | +1.57 | +0.12 | Y | Y |
| 0.10 | 1 | +0.95 | +1.60 | +0.15 | Y | Y |
| 0.10 | 2 | +1.05 | +1.59 | +0.26 | Y | Y |
| 0.10 | 3 | +1.14 | +1.62 | +0.33 | Y | Y |
| 0.25 | 0 | +0.65 | +2.74 | -0.72 | N | Y |
| 0.25 | 1 | +0.63 | +2.83 | -0.78 | N | Y |
| 0.25 | 2 | +0.68 | +2.87 | -0.76 | N | Y |
| 0.25 | 3 | +0.75 | +2.94 | -0.72 | N | Y |

## Turnover vs BASE at 1× (full sample)

| Book | α | TO/yr | ΔTO vs BASE | fills | fees@1× |
|---|---:|---:|---:|---:|---:|
| BASE | 0.00 | 2.240 | +0.00 | 6271 | 400790 |
| BLEND_A05 | 0.05 | 2.280 | +0.04 | 6295 | 407845 |
| BLEND_A10 | 0.10 | 2.323 | +0.08 | 6455 | 413574 |
| BLEND_A25 | 0.25 | 2.354 | +0.11 | 6603 | 413547 |
| FULL_E45 | 1.00 | 2.352 | +0.11 | 6931 | 394843 |

## Read-through (paper)

1. Held-out @1× preferred among α>0: **`BLEND_A05`**.
2. α=0.05 at 3× cost: score≥0=YES; MDD help=YES.
3. Compare turnover deltas — mild α should not explode trading vs BASE.
4. Does **not** open observe / authorize stitch.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED

## Reproduce

```bash
python3 scripts/e45_alpha_cost_turnover_paper.py
```

