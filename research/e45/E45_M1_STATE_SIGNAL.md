# E45 M1 PAPER — New State-Signal Family (Sensor)

Generated: `2026-09-06T11:20:28.545560+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; HIGH_BETA **DRAFT / NOT OPEN**.

State vector: **`E45_M1_STATE_VECTOR_V0_FROZEN_2026-09-06`** (frozen before metrics).
Honesty: `equity_taiex_proxy_sensor__no_rates_fx_credit_in_repo` — not a true macro sensor.

## Setup

- Books: `BASE_E16_E18_E22_v2s, BLEND_E45_A05, SLEEVE_FIN_ONLY_A10, M1_EQW_C25, M1_EQW_C50, M1_EQW_C75, M1_EQW_C50_FIN`
- Cost multiples: 0x, 1x, 2x, 3x on `BUY_FEE, SELL_FEE, SLIP, TAX_STOCK, TAX_ETF`
- Score: `mdd_improve_pp - 0.5*|cagr_giveback_pp|` vs BASE at same cost x
- Year help threshold: MDD improve > **0.25 pp** in {2015,2018,2020,2022}
- Exposure lag: 1 trading day (`s_{t-1}`)

## Held-out deltas @1x (incl. COVID-ex score)

| Book | Kind | MDD dpp | Giveback | Score | COVID-ex score | Years helped |
|---|---|---:|---:|---:|---:|---|
| M1_EQW_C75 | m1 | +8.08 | +7.73 | +4.21 | -0.16 | 2015,2018,2020,2022 |
| M1_EQW_C50 | m1 | +5.35 | +6.00 | +2.35 | -0.70 | 2015,2018,2020,2022 |
| M1_EQW_C50_FIN | m1_sleeve | +4.99 | +5.44 | +2.27 | -1.21 | 2015,2018,2020,2022 |
| M1_EQW_C25 | m1 | +2.72 | +4.28 | +0.58 | -1.31 | 2015,2018,2020,2022 |
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | +0.91 | +1.25 | +0.29 | -2.41 | 2020 |
| BLEND_E45_A05 | ref_e45 | +0.70 | +0.96 | +0.22 | -2.05 | 2020 |
| BASE_E16_E18_E22_v2s | ref | +0.00 | +0.00 | +0.00 | +0.00 | — |

## Sealed deltas @1x

| Book | Kind | MDD dpp | Giveback | Score |
|---|---|---:|---:|---:|
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | +3.42 | +1.80 | +2.52 |
| BLEND_E45_A05 | ref_e45 | +2.78 | +1.42 | +2.07 |
| M1_EQW_C25 | m1 | +5.32 | +8.29 | +1.18 |
| M1_EQW_C50_FIN | m1_sleeve | +5.90 | +9.80 | +1.00 |
| M1_EQW_C50 | m1 | +6.23 | +10.65 | +0.91 |
| M1_EQW_C75 | m1 | +7.06 | +12.94 | +0.59 |
| BASE_E16_E18_E22_v2s | ref | +0.00 | +0.00 | +0.00 |

## Cost stress — held-out scores by x

| Book | 0x | 1x | 2x | 3x |
|---|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | +0.00 | +0.00 | +0.00 | +0.00 |
| BLEND_E45_A05 | +0.22 | +0.22 | +0.25 | +0.26 |
| SLEEVE_FIN_ONLY_A10 | +0.25 | +0.29 | +0.32 | +0.37 |
| M1_EQW_C25 | +0.71 | +0.58 | +0.49 | +0.41 |
| M1_EQW_C50 | +2.68 | +2.35 | +2.06 | +1.80 |
| M1_EQW_C75 | +4.78 | +4.21 | +3.68 | +3.19 |
| M1_EQW_C50_FIN | +2.62 | +2.27 | +1.95 | +1.66 |

## Section-2 qualification (binding)

| Book | Multi>=2 | Strict non-COVID>=2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BASE_E16_E18_E22_v2s | N | N | N | Y | N | N | NO |
| BLEND_E45_A05 | N | N | Y | Y | N | Y | NO |
| SLEEVE_FIN_ONLY_A10 | N | N | Y | Y | N | Y | NO |
| M1_EQW_C25 | Y | Y | Y | Y | N | Y | NO |
| M1_EQW_C50 | Y | Y | Y | Y | N | Y | NO |
| M1_EQW_C75 | Y | Y | Y | Y | N | Y | NO |
| M1_EQW_C50_FIN | Y | Y | Y | Y | N | Y | NO |

## Read-through (paper)

1. Best M1 on held-out @1x: **`M1_EQW_C75`** (score +4.21; COVID-ex -0.16; years `2015,2018,2020,2022`).
2. Any M1 clears full Section-2 (incl. strict non-COVID + COVID-ex>0 + cost 1-2x)? **NO**.
3. If NO: this is an **autopsy**, not a license to densify E45 alpha. Charter allows M2 (DEF sleeve relocate) even after M1 fail.
4. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN
- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement
- Freeze doc: `research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md`

## Reproduce

```bash
python3 scripts/e45_m1_state_signal_paper.py
```

Repro: `repro/e45-m1-state-signal/` · Market: `forward/e21/live_market.csv`

