# E45 M2 PAPER — Cash / DEF Sleeve Relocate (Actuator)

Generated: `2026-09-06T13:11:19.088441+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; HIGH_BETA **DRAFT / NOT OPEN**.

DEF freeze: **`E45_M2_DEF_SLEEVE_V0_FROZEN_2026-09-06`** (frozen before metrics).
Honesty: `DEF_TEL=Telecom equity proxy only; no cash/duration ETF in live_market; DEF_CASH0 shrink control yields 0%`

## Verdict: **PASS**

## Setup

- Books: `BASE_E16_E18_E22_v2s, BLEND_E45_A05, SLEEVE_FIN_ONLY_A10, M2_SHRINK_C50, M2_SHRINK_C75, M2_RELOC_TEL_C50, M2_RELOC_TEL_C75, M2_HYBRID_TEL_C50, M2_HYBRID_TEL_C75`
- Sensor: M1 frozen intensity `s_{t-1}` (Exact T+1 actuator lag)
- Modes: SHRINK (cash@0) · RELOC_TEL · HYBRID_TEL; cuts 0.50 / 0.75
- Cost multiples: 0x, 1x, 2x, 3x on BUY_FEE/SELL_FEE/SLIP/TAX_STOCK/TAX_ETF
- Score: `mdd_improve_pp - 0.5*|cagr_giveback_pp|` vs BASE at same cost x
- Year help threshold: MDD improve > **0.25 pp** in [2015, 2018, 2020, 2022]

## Held-out deltas @1x (incl. COVID-ex score)

| Book | Kind | Mode | MDD dpp | Giveback | Score | COVID-ex score | Years helped |
|---|---|---|---:|---:|---:|---:|---|
| M2_SHRINK_C75 | m2_shrink | SHRINK | +8.08 | +7.73 | +4.21 | -0.16 | 2015,2018,2020,2022 |
| M2_HYBRID_TEL_C75 | m2_hybrid | HYBRID_TEL | +7.00 | +6.95 | +3.53 | -1.84 | 2015,2018,2020,2022 |
| M2_SHRINK_C50 | m2_shrink | SHRINK | +5.35 | +6.00 | +2.35 | -0.70 | 2015,2018,2020,2022 |
| M2_HYBRID_TEL_C50 | m2_hybrid | HYBRID_TEL | +4.63 | +5.40 | +1.93 | -1.81 | 2015,2018,2020,2022 |
| M2_RELOC_TEL_C75 | m2_reloc | RELOC_TEL | +3.31 | +3.76 | +1.43 | -1.09 | 2015,2018,2020,2022 |
| M2_RELOC_TEL_C50 | m2_reloc | RELOC_TEL | +1.61 | +2.26 | +0.48 | +0.16 | 2015,2018,2020,2022 |
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | — | +0.91 | +1.25 | +0.29 | -2.41 | 2020 |
| BLEND_E45_A05 | ref_e45 | — | +0.70 | +0.96 | +0.22 | -2.05 | 2020 |
| BASE_E16_E18_E22_v2s | ref | — | +0.00 | +0.00 | +0.00 | +0.00 | — |

## Sealed deltas @1x

| Book | Kind | Mode | MDD dpp | Giveback | Score |
|---|---|---|---:|---:|---:|
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | — | +3.42 | +1.80 | +2.52 |
| BLEND_E45_A05 | ref_e45 | — | +2.78 | +1.42 | +2.07 |
| M2_HYBRID_TEL_C50 | m2_hybrid | HYBRID_TEL | +5.86 | +9.17 | +1.27 |
| M2_HYBRID_TEL_C75 | m2_hybrid | HYBRID_TEL | +6.48 | +11.03 | +0.97 |
| M2_SHRINK_C50 | m2_shrink | SHRINK | +6.23 | +10.65 | +0.91 |
| M2_RELOC_TEL_C75 | m2_reloc | RELOC_TEL | +3.28 | +4.88 | +0.84 |
| M2_SHRINK_C75 | m2_shrink | SHRINK | +7.06 | +12.94 | +0.59 |
| M2_RELOC_TEL_C50 | m2_reloc | RELOC_TEL | +1.60 | +2.88 | +0.17 |
| BASE_E16_E18_E22_v2s | ref | — | +0.00 | +0.00 | +0.00 |

## M2 stage gate vs matched SHRINK (COVID-ex held-out @1x)

| Book | Beats shrink COVID-ex | Rule4∨5 | Stage PASS | §2 PASS |
|---|:---:|:---:|:---:|:---:|
| M2_RELOC_TEL_C50 | Y | Y | Y | Y |
| M2_HYBRID_TEL_C50 | N | Y | N | N |
| M2_RELOC_TEL_C75 | N | Y | N | N |
| M2_HYBRID_TEL_C75 | N | Y | N | N |

## Section-2 qualification (binding)

| Book | Multi≥2 | Strict non-COVID≥2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BASE_E16_E18_E22_v2s | N | N | N | Y | N | N | NO |
| BLEND_E45_A05 | N | N | Y | Y | N | Y | NO |
| SLEEVE_FIN_ONLY_A10 | N | N | Y | Y | N | Y | NO |
| M2_SHRINK_C50 | Y | Y | Y | Y | N | Y | NO |
| M2_SHRINK_C75 | Y | Y | Y | Y | N | Y | NO |
| M2_RELOC_TEL_C50 | Y | Y | Y | Y | Y | Y | YES |
| M2_RELOC_TEL_C75 | Y | Y | Y | Y | N | Y | NO |
| M2_HYBRID_TEL_C50 | Y | Y | Y | Y | N | Y | NO |
| M2_HYBRID_TEL_C75 | Y | Y | Y | Y | N | Y | NO |

## Read-through (paper)

1. Best M2 on held-out @1x: **`M2_SHRINK_C75`** (score +4.21; COVID-ex -0.16; years `2015,2018,2020,2022`).
2. Any M2 clears full Section-2? **YES: M2_RELOC_TEL_C50**.
3. M2 stage pass (relocate/hybrid beats shrink on COVID-ex and rule 4∨5)? **YES**.
4. If NO: autopsy — DEF_TEL equity proxy may be too weak without cash/duration ingest; do **not** densify E45 alpha; M3 stays blocked pending charter amendment or stronger DEF data.
5. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN
- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement
- Freeze doc: `research/e45/E45_M2_DEF_SLEEVE_V0_FROZEN.md`

## Reproduce

```bash
python3 scripts/e45_m2_def_sleeve_relocate_paper.py
```

Repro: `repro/e45-m2-def-sleeve-relocate/` · Market: `forward/e21/live_market.csv`

