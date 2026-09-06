# E45 PAPER Cheap-Protect × Cost Realism × Data-Clean

Generated: `2026-09-06T10:28:26.329801+00:00`
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
| BASE_E16_E18_E22_v2s | — | 0.00 | 0 | +0.00 | +0.00 | +0.00 | 2.195 | 0 |
| BLEND_E45_A05 | ALL | 0.05 | 0 | +0.69 | +0.94 | +0.22 | 2.234 | 0 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 0 | +0.66 | +0.87 | +0.23 | 2.230 | 0 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 0 | +0.64 | +0.78 | +0.25 | 2.227 | 0 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 0 | +0.86 | +1.23 | +0.25 | 2.274 | 0 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 1 | +0.00 | +0.00 | +0.00 | 2.186 | 391685 |
| BLEND_E45_A05 | ALL | 0.05 | 1 | +0.70 | +0.96 | +0.22 | 2.233 | 400184 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 1 | +0.66 | +0.85 | +0.23 | 2.220 | 398096 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 1 | +0.64 | +0.76 | +0.26 | 2.217 | 397542 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 1 | +0.91 | +1.25 | +0.29 | 2.266 | 405612 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 2 | +0.00 | +0.00 | +0.00 | 2.178 | 746243 |
| BLEND_E45_A05 | ALL | 0.05 | 2 | +0.74 | +0.97 | +0.25 | 2.226 | 763092 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 2 | +0.67 | +0.85 | +0.25 | 2.219 | 760999 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 2 | +0.65 | +0.80 | +0.25 | 2.220 | 760834 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 2 | +0.96 | +1.29 | +0.32 | 2.258 | 772298 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 3 | +0.00 | +0.00 | +0.00 | 2.176 | 1071122 |
| BLEND_E45_A05 | ALL | 0.05 | 3 | +0.76 | +0.99 | +0.26 | 2.216 | 1090071 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 3 | +0.71 | +0.86 | +0.28 | 2.214 | 1089017 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 3 | +0.69 | +0.80 | +0.29 | 2.212 | 1087895 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 3 | +1.03 | +1.34 | +0.37 | 2.256 | 1106138 |

## Sealed deltas vs BASE (cheap forms × cost)

| Book | Scope | α | ×cost | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|---:|
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 0 | +3.29 | +1.77 | +2.40 |
| BLEND_E45_A05 | ALL | 0.05 | 0 | +2.68 | +1.38 | +1.99 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 0 | +2.54 | +1.27 | +1.91 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 0 | +2.33 | +1.15 | +1.75 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 0 | +0.00 | +0.00 | +0.00 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 1 | +3.42 | +1.80 | +2.52 |
| BLEND_E45_A05 | ALL | 0.05 | 1 | +2.78 | +1.42 | +2.07 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 1 | +2.58 | +1.27 | +1.95 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 1 | +2.36 | +1.14 | +1.79 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 1 | +0.00 | +0.00 | +0.00 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 2 | +3.40 | +1.87 | +2.47 |
| BLEND_E45_A05 | ALL | 0.05 | 2 | +2.68 | +1.42 | +1.97 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 2 | +2.48 | +1.27 | +1.84 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 2 | +2.32 | +1.20 | +1.72 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 2 | +0.00 | +0.00 | +0.00 |
| SLEEVE_FIN_ONLY_A10 | FIN_ONLY | 0.10 | 3 | +3.56 | +1.89 | +2.62 |
| BLEND_E45_A05 | ALL | 0.05 | 3 | +2.77 | +1.48 | +2.03 |
| FIN_0050_A05 | FIN_0050 | 0.05 | 3 | +2.52 | +1.26 | +1.90 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | 3 | +2.34 | +1.17 | +1.76 |
| BASE_E16_E18_E22_v2s | — | 0.00 | 3 | +0.00 | +0.00 | +0.00 |

## FIN_ONLY_A05 vs BLEND_E45_A05 (held-out, by cost ×)

| ×cost | ALL score | FIN_ONLY score | FIN beats ALL? | ALL giveback | FIN giveback |
|---:|---:|---:|:---:|---:|---:|
| 0 | +0.22 | +0.25 | Y | +0.94 | +0.78 |
| 1 | +0.22 | +0.26 | Y | +0.96 | +0.76 |
| 2 | +0.25 | +0.25 | Y | +0.97 | +0.80 |
| 3 | +0.26 | +0.29 | Y | +0.99 | +0.80 |

## Survival (held-out): score≥0 and MDD helps

| Book | α | ×cost | MDD Δpp | Giveback | Score | score≥0 | MDD>0 |
|---|---:|---:|---:|---:|---:|:---:|:---:|
| BLEND_E45_A05 | 0.05 | 0 | +0.69 | +0.94 | +0.22 | Y | Y |
| BLEND_E45_A05 | 0.05 | 1 | +0.70 | +0.96 | +0.22 | Y | Y |
| BLEND_E45_A05 | 0.05 | 2 | +0.74 | +0.97 | +0.25 | Y | Y |
| BLEND_E45_A05 | 0.05 | 3 | +0.76 | +0.99 | +0.26 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 0 | +0.64 | +0.78 | +0.25 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 1 | +0.64 | +0.76 | +0.26 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 2 | +0.65 | +0.80 | +0.25 | Y | Y |
| FIN_ONLY_A05 | 0.05 | 3 | +0.69 | +0.80 | +0.29 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 0 | +0.86 | +1.23 | +0.25 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 1 | +0.91 | +1.25 | +0.29 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 2 | +0.96 | +1.29 | +0.32 | Y | Y |
| SLEEVE_FIN_ONLY_A10 | 0.10 | 3 | +1.03 | +1.34 | +0.37 | Y | Y |
| FIN_0050_A05 | 0.05 | 0 | +0.66 | +0.87 | +0.23 | Y | Y |
| FIN_0050_A05 | 0.05 | 1 | +0.66 | +0.85 | +0.23 | Y | Y |
| FIN_0050_A05 | 0.05 | 2 | +0.67 | +0.85 | +0.25 | Y | Y |
| FIN_0050_A05 | 0.05 | 3 | +0.71 | +0.86 | +0.28 | Y | Y |

## Read-through (paper)

1. Held-out @1× preferred among protect books: **`SLEEVE_FIN_ONLY_A10`** (score +0.29; scope=FIN_ONLY).
2. Cheap forms survive held-out @3× (score≥0 & MDD>0 for A05/sleeve set): **YES**.
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

