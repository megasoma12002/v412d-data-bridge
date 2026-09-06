# E45 M2 PAPER — Cash / DEF Sleeve Relocate (Actuator)

Generated: `2026-09-06T14:12:27.086430+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; HIGH_BETA **DRAFT / NOT OPEN**.

DEF freeze: **`E45_M2_DEF_SLEEVE_V1_FROZEN_2026-09-06`** (frozen before metrics).
Honesty: `DEF_719B_SW=BIL_FX pre-2018-02-01 then 00719B TR; BIL_FX=BIL adj*USDTWD mid (FX risk; mid optimistic); not merged into live_market; DEF_TEL rebuild is equity proxy ref only`

## Verdict: **PASS**

## Setup

- Books: `BASE_E16_E18_E22_v2s, BLEND_E45_A05, SLEEVE_FIN_ONLY_A10, M2_SHRINK_C50, M2_RELOC_TEL_C50, M2_RELOC_719B_C50, M2_RELOC_719B_C75, M2_RELOC_BIL_FX_C50, M2_RELOC_BIL_FX_C75, M2_HYBRID_719B_C50, M2_HYBRID_719B_C75`
- Sensor: M1 frozen intensity `s_{{t-1}}` (Exact T+1 actuator lag)
- Modes: SHRINK · RELOC_TEL (rebuild) · RELOC_719B · RELOC_BIL_FX · HYBRID_719B
- Cost multiples: 0x, 1x, 2x, 3x on BUY_FEE/SELL_FEE/SLIP/TAX_STOCK/TAX_ETF
- Score: `mdd_improve_pp - 0.5*|cagr_giveback_pp|` vs BASE at same cost x
- Year help threshold: MDD improve > **0.25 pp** in [2015, 2018, 2020, 2022]

## Held-out deltas @1x (incl. COVID-ex score)

| Book | Kind | Mode | MDD dpp | Giveback | Score | COVID-ex score | Years helped |
|---|---|---|---:|---:|---:|---:|---|
| M2_HYBRID_719B_C75 | m2_hybrid_719b | HYBRID_719B | +8.16 | +8.77 | +3.77 | -1.45 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_C75 | m2_reloc_bil_fx | RELOC_BIL_FX | +5.40 | +5.46 | +2.67 | +3.41 | 2015,2018,2020,2022 |
| M2_SHRINK_C50 | m2_shrink | SHRINK | +5.35 | +6.00 | +2.35 | -0.70 | 2015,2018,2020,2022 |
| M2_HYBRID_719B_C50 | m2_hybrid_719b | HYBRID_719B | +5.50 | +6.77 | +2.11 | -1.63 | 2015,2018,2020,2022 |
| M2_RELOC_BIL_FX_C50 | m2_reloc_bil_fx | RELOC_BIL_FX | +2.96 | +3.43 | +1.24 | +3.20 | 2015,2018,2020,2022 |
| M2_RELOC_719B_C75 | m2_reloc_719b | RELOC_719B | +5.24 | +8.40 | +1.04 | -5.35 | 2015,2018,2020,2022 |
| M2_RELOC_TEL_C50 | m2_reloc_tel | RELOC_TEL | +1.61 | +2.26 | +0.48 | +0.16 | 2015,2018,2020,2022 |
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | — | +0.91 | +1.25 | +0.29 | -2.41 | 2020 |
| BLEND_E45_A05 | ref_e45 | — | +0.70 | +0.96 | +0.22 | -2.05 | 2020 |
| M2_RELOC_719B_C50 | m2_reloc_719b | RELOC_719B | +3.06 | +5.75 | +0.19 | -0.16 | 2015,2018,2020,2022 |
| BASE_E16_E18_E22_v2s | ref | — | +0.00 | +0.00 | +0.00 | +0.00 | — |

## Sealed deltas @1x

| Book | Kind | Mode | MDD dpp | Giveback | Score |
|---|---|---|---:|---:|---:|
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | — | +3.42 | +1.80 | +2.52 |
| BLEND_E45_A05 | ref_e45 | — | +2.78 | +1.42 | +2.07 |
| M2_SHRINK_C50 | m2_shrink | SHRINK | +6.23 | +10.65 | +0.91 |
| M2_HYBRID_719B_C50 | m2_hybrid_719b | HYBRID_719B | +6.11 | +10.43 | +0.89 |
| M2_RELOC_BIL_FX_C75 | m2_reloc_bil_fx | RELOC_BIL_FX | +4.33 | +7.36 | +0.65 |
| M2_RELOC_719B_C75 | m2_reloc_719b | RELOC_719B | +5.29 | +9.47 | +0.56 |
| M2_HYBRID_719B_C75 | m2_hybrid_719b | HYBRID_719B | +6.68 | +12.56 | +0.41 |
| M2_RELOC_BIL_FX_C50 | m2_reloc_bil_fx | RELOC_BIL_FX | +2.65 | +4.76 | +0.28 |
| M2_RELOC_719B_C50 | m2_reloc_719b | RELOC_719B | +3.69 | +6.91 | +0.23 |
| M2_RELOC_TEL_C50 | m2_reloc_tel | RELOC_TEL | +1.60 | +2.88 | +0.17 |
| BASE_E16_E18_E22_v2s | ref | — | +0.00 | +0.00 | +0.00 |

## M2 v1 stage gate vs SHRINK_C50 / RELOC_TEL_C50 (COVID-ex held-out @1x)

| Book | Beats shrink | Beats TEL | Rule4∨5 | Stage PASS | §2 PASS |
|---|:---:|:---:|:---:|:---:|
| M2_RELOC_719B_C50 | Y | N | Y | Y | N |
| M2_RELOC_719B_C75 | N | N | Y | N | N |
| M2_RELOC_BIL_FX_C50 | Y | Y | Y | Y | Y |
| M2_RELOC_BIL_FX_C75 | Y | Y | Y | Y | Y |
| M2_HYBRID_719B_C50 | N | N | Y | N | N |
| M2_HYBRID_719B_C75 | N | N | Y | N | N |

## Section-2 qualification (binding)

| Book | Multi≥2 | Strict non-COVID≥2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BASE_E16_E18_E22_v2s | N | N | N | Y | N | N | NO |
| BLEND_E45_A05 | N | N | Y | Y | N | Y | NO |
| SLEEVE_FIN_ONLY_A10 | N | N | Y | Y | N | Y | NO |
| M2_SHRINK_C50 | Y | Y | Y | Y | N | Y | NO |
| M2_RELOC_TEL_C50 | Y | Y | Y | Y | Y | Y | YES |
| M2_RELOC_719B_C50 | Y | Y | Y | Y | N | N | NO |
| M2_RELOC_719B_C75 | Y | Y | Y | Y | N | N | NO |
| M2_RELOC_BIL_FX_C50 | Y | Y | Y | Y | Y | Y | YES |
| M2_RELOC_BIL_FX_C75 | Y | Y | Y | Y | Y | Y | YES |
| M2_HYBRID_719B_C50 | Y | Y | Y | Y | N | Y | NO |
| M2_HYBRID_719B_C75 | Y | Y | Y | Y | N | Y | NO |

## Read-through (paper)

1. Best M2 on held-out @1x: **`M2_HYBRID_719B_C75`** (score +3.77; COVID-ex -1.45; years `2015,2018,2020,2022`).
2. Any M2 clears full Section-2? **YES: M2_RELOC_TEL_C50, M2_RELOC_BIL_FX_C50, M2_RELOC_BIL_FX_C75**.
3. M2 stage pass (relocate/hybrid beats shrink on COVID-ex and rule 4∨5)? **YES**.
4. If NO: autopsy — DEF_TEL equity proxy may be too weak without cash/duration ingest; do **not** densify E45 alpha; M3 stays blocked pending charter amendment or stronger DEF data.
5. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN
- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement
- Freeze doc: `research/e45/E45_M2_DEF_SLEEVE_V1_FROZEN.md`

## Reproduce

```bash
python3 scripts/e45_m2_true_def_relocate_paper.py
```

Repro: `repro/e45-m2-true-def-relocate/` · Market: `forward/e21/live_market.csv`

