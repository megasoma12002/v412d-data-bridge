# E45 PAPER Cheap-Protect × Cost Realism × Data-Clean

Generated: `2026-09-08T03:25:47.135377+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; HIGH_BETA observe **DRAFT / NOT OPEN**; observe sleeves unchanged.

## Thesis

Remaining E45 research lever is **cheaper protection** (mild A05 / sleeve-local), not denser mild-α grids or crisis gates. Stress those forms under **realistic cost ×** and keep **0050 history QC** on adj_close with C1 quarantine.

## Setup

- Profile: frozen `E3_VOLTARGET_WINNER`
- Books: `BASE_E16_E18_E22_v2s, BLEND_E45_A05, FIN_ONLY_A05, SLEEVE_FIN_ONLY_A10, FIN_0050_A05`
- Cost multiples: 0×, 1×, 2×, 3× on `BUY_FEE, SELL_FEE, SLIP, TAX_STOCK, TAX_ETF`
- Score: `mdd_improve_pp − 0.5·|cagr_giveback_pp|` vs BASE at same cost ×

## Data clean — 0050 C1 quarantine + adj_close QC

- QC status: **`PASS_QUARANTINE_COVERS_C1`**
- Prefer path: `adj_close_or_C2` (raw-close C1 is spike-sensitive)
- Quarantine dates: `2014-01-02, 2025-06-18`
- Spikes vs adj (|Δret|>5%): **1** (on quarantine: 1; extra: 0)
- Phase C root class: `UNADJUSTED_CLOSE_SPIKE` — **no e21 primary rewrite**

| Date | close | adj_close | close_ret | adj_ret |
|---|---:|---:|---:|---:|
| 2014-01-02 | 58.55 | 10.0245 | -0.26% | -0.26% |
| 2025-06-18 | 47.57 | 46.2980 | -74.78% | +0.87% |

## Held-out deltas vs BASE (cheap forms × cost)

| Book | Scope | α | ×cost | MDD Δpp | Giveback pp | Score | TO/yr | fees |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | — | 0.00 | 0 | +0.00 | +0.00 | +0.00 | 1.293 | 0 |
| BLEND_E45_A05 | ALL | 0.05 | 0 | +0.28 | +0.57 | -0.01 | 1.394 | 0 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 0 | +0.32 | +0.10 | +0.28 | 1.361 | 0 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 0 | +0.01 | +0.02 | +0.01 | 1.359 | 0 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 0 | -0.34 | +0.26 | -0.48 | 1.390 | 0 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 1 | +0.00 | +0.00 | +0.00 | 1.296 | 236270 |
| BLEND_E45_A05 | ALL | 0.05 | 1 | +0.14 | +0.09 | +0.10 | 1.348 | 246526 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 1 | +0.20 | +0.24 | +0.08 | 1.334 | 243888 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 1 | +0.17 | -0.06 | +0.15 | 1.354 | 249366 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 1 | +0.47 | +0.31 | +0.32 | 1.348 | 245820 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 2 | +0.00 | +0.00 | +0.00 | 1.302 | 467043 |
| BLEND_E45_A05 | ALL | 0.05 | 2 | +0.25 | +0.51 | -0.00 | 1.331 | 472964 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 2 | +0.19 | +0.52 | -0.07 | 1.338 | 478898 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 2 | +0.21 | +0.05 | +0.19 | 1.336 | 477745 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 2 | +0.35 | +0.49 | +0.11 | 1.377 | 492919 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 3 | +0.00 | +0.00 | +0.00 | 1.282 | 670969 |
| BLEND_E45_A05 | ALL | 0.05 | 3 | -0.09 | +0.30 | -0.24 | 1.323 | 691690 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 3 | -0.19 | +0.16 | -0.27 | 1.302 | 679913 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 3 | +0.30 | +0.22 | +0.20 | 1.299 | 680202 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 3 | +0.20 | +0.32 | +0.04 | 1.335 | 701061 |

## Sealed deltas vs BASE (cheap forms × cost)

| Book | Scope | α | ×cost | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|---:|
| BLEND_E45_A05 | ALL | 0.05 | 0 | +1.17 | +1.22 | +0.56 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 0 | +0.48 | +0.24 | +0.35 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 0 | +0.54 | +0.44 | +0.32 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 0 | +0.00 | +0.00 | +0.00 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 0 | +0.34 | +1.02 | -0.16 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 1 | +1.26 | +0.90 | +0.81 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 1 | +1.09 | +0.62 | +0.78 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 1 | +0.86 | +0.39 | +0.67 |
| BLEND_E45_A05 | ALL | 0.05 | 1 | +0.79 | +0.69 | +0.45 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 1 | +0.00 | +0.00 | +0.00 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 2 | +1.89 | +1.02 | +1.38 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 2 | +1.53 | +0.91 | +1.08 |
| BLEND_E45_A05 | ALL | 0.05 | 2 | +1.40 | +0.92 | +0.94 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 2 | +0.61 | +0.38 | +0.42 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 2 | +0.00 | +0.00 | +0.00 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 3 | +1.82 | +1.13 | +1.26 |
| BLEND_E45_A05 | ALL | 0.05 | 3 | +1.08 | +0.83 | +0.67 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 3 | +0.77 | +0.58 | +0.48 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 3 | +0.67 | +0.61 | +0.36 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 3 | +0.00 | +0.00 | +0.00 |

## FIN_ONLY_A05 vs BLEND_E45_A05 (held-out, by cost ×)

| ×cost | ALL score | FIN_ONLY score | FIN beats ALL? | ALL giveback | FIN giveback |
|---:|---:|---:|:---:|---:|---:|
| 0 | -0.01 | +0.01 | Y | +0.57 | +0.02 |
| 1 | +0.10 | +0.15 | Y | +0.09 | -0.06 |
| 2 | -0.00 | +0.19 | Y | +0.51 | +0.05 |
| 3 | -0.24 | +0.20 | Y | +0.30 | +0.22 |

## Survival (held-out): score≥0 and MDD helps

| Book | α | ×cost | MDD Δpp | Giveback | Score | score≥0 | MDD>0 |
|---|---:|---:|---:|---:|---:|:---:|:---:|
| BLEND_E45_A05 | 0.05 | 0 | +0.28 | +0.57 | -0.01 | N | Y |
| BLEND_E45_A05 | 0.05 | 1 | +0.14 | +0.09 | +0.10 | Y | Y |
| BLEND_E45_A05 | 0.05 | 2 | +0.25 | +0.51 | -0.00 | N | Y |
| BLEND_E45_A05 | 0.05 | 3 | -0.09 | +0.30 | -0.24 | N | N |
| FIN_ONLY_A05 | 0.05 | 0 | +0.01 | +0.02 | +0.01 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 1 | +0.17 | -0.06 | +0.15 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 2 | +0.21 | +0.05 | +0.19 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 3 | +0.30 | +0.22 | +0.20 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 0 | -0.34 | +0.26 | -0.48 | N | N |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 1 | +0.47 | +0.31 | +0.32 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 2 | +0.35 | +0.49 | +0.11 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 3 | +0.20 | +0.32 | +0.04 | Y | Y |
| FIN_0050_A05 | 0.05 | 0 | +0.32 | +0.10 | +0.28 | Y | Y |
| FIN_0050_A05 | 0.05 | 1 | +0.20 | +0.24 | +0.08 | Y | Y |
| FIN_0050_A05 | 0.05 | 2 | +0.19 | +0.52 | -0.07 | N | Y |
| FIN_0050_A05 | 0.05 | 3 | -0.19 | +0.16 | -0.27 | N | N |

## Read-through (paper)

1. Held-out @1× preferred among protect books: **`SLEEVE_FIN_ONLY_A10`** (score +0.32; scope=FIN_ONLY).
2. Cheap forms survive held-out @3× (score≥0 & MDD>0 for A05/sleeve set): **NO**.
3. **FIN_ONLY_A05 beats BLEND_E45_A05** on held-out score at every cost × (Y) — prefer sleeve-local over whole-book mild α for giveback control.
4. Data QC `PASS_QUARANTINE_COVERS_C1` — keep C1 quarantine + adj_close preference; do not rewrite e21 primary.
5. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN
- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement

## Reproduce

```bash
python3 scripts/e45_cheap_protect_cost_data_paper.py
```

Repro: `repro/e45-cheap-protect-cost-data/` · Market: `forward/e21/live_market.csv`

