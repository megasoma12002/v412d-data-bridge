# E45 M3 PAPER — Three-State Risk Machine

Generated: `2026-09-06T13:31:12.924388+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; HIGH_BETA **DRAFT / NOT OPEN**.

M3 freeze: **`E45_M3_THREE_STATE_V0_FROZEN_2026-09-06`** (frozen before metrics).
Honesty: `DEF_TEL=Telecom equity proxy only; discrete states are paper risk regimes; no Soft-Frozen/stitch auto-open`

## Verdict: **FAIL_AUTOPSY**

## Setup

- Books: `BASE_E16_E18_E22_v2s, BLEND_E45_A05, SLEEVE_FIN_ONLY_A10, M1_EQW_C75, M2_RELOC_TEL_C50, M3_STATE_V0`
- Sensor: M1 frozen `s_t` with hysteresis; action applies `state_{t-1}` (Exact T+1)
- Actions: NORMAL=identity · SLOW_BEAR=RELOC_TEL(u=0.40) · CRASH=RELOC_TEL(u=0.75)
- Continuous refs: `M1_EQW_C75`, `M2_RELOC_TEL_C50` (rebuild only)
- Cost multiples: 0x/1x/2x/3x; qualify on 1x & 2x
- Year help threshold: MDD improve > **0.25 pp** in [2015, 2018, 2020, 2022]

## State occupancy (full sample)

| State | Share |
|---|---:|
| NORMAL | 71.9% |
| SLOW_BEAR | 24.1% |
| CRASH | 4.0% |

## Held-out deltas @1x (incl. COVID-ex score)

| Book | Kind | Mode | MDD dpp | Giveback | Score | COVID-ex score | Years helped | TO/yr |
|---|---|---|---:|---:|---:|---:|---|---:|
| M1_EQW_C75 | ref_m1_continuous | EQW_C75 | +8.08 | +7.73 | +4.21 | -0.16 | 2015,2018,2020,2022 | +4.75 |
| M2_RELOC_TEL_C50 | ref_m2_continuous | RELOC_TEL_C50 | +1.61 | +2.26 | +0.48 | +0.16 | 2015,2018,2020,2022 | +3.99 |
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | — | +0.91 | +1.25 | +0.29 | -2.41 | 2020 | +2.27 |
| BLEND_E45_A05 | ref_e45 | — | +0.70 | +0.96 | +0.22 | -2.05 | 2020 | +2.23 |
| BASE_E16_E18_E22_v2s | ref | — | +0.00 | +0.00 | +0.00 | +0.00 | — | +2.19 |
| M3_STATE_V0 | m3_state | STATE_V0 | -0.29 | +2.71 | -1.65 | -5.52 | — | +3.67 |

## Sealed deltas @1x

| Book | Kind | Mode | MDD dpp | Giveback | Score | TO/yr |
|---|---|---|---:|---:|---:|---:|
| M3_STATE_V0 | m3_state | STATE_V0 | +2.84 | +0.57 | +2.56 | +3.67 |
| SLEEVE_FIN_ONLY_A10 | ref_e45_sleeve | — | +3.42 | +1.80 | +2.52 | +2.27 |
| BLEND_E45_A05 | ref_e45 | — | +2.78 | +1.42 | +2.07 | +2.23 |
| M1_EQW_C75 | ref_m1_continuous | EQW_C75 | +7.06 | +12.94 | +0.59 | +4.75 |
| M2_RELOC_TEL_C50 | ref_m2_continuous | RELOC_TEL_C50 | +1.60 | +2.88 | +0.17 | +3.99 |
| BASE_E16_E18_E22_v2s | ref | — | +0.00 | +0.00 | +0.00 | +2.19 |

## M3 stage gate vs continuous M2

- M3 Section-2 PASS? **NO**
- M3 COVID-ex held-out score: **-5.52**
- M2_RELOC_TEL_C50 COVID-ex held-out score: **+0.16**
- M3 ≥ M2 on COVID-ex? **NO**
- M3 stage PASS? **NO**

## Section-2 qualification (binding)

| Book | Multi≥2 | Strict non-COVID≥2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| BASE_E16_E18_E22_v2s | N | N | N | Y | N | N | NO |
| BLEND_E45_A05 | N | N | Y | Y | N | Y | NO |
| SLEEVE_FIN_ONLY_A10 | N | N | Y | Y | N | Y | NO |
| M1_EQW_C75 | Y | Y | Y | Y | N | Y | NO |
| M2_RELOC_TEL_C50 | Y | Y | Y | Y | Y | Y | YES |
| M3_STATE_V0 | N | N | N | Y | N | N | NO |

## Giveback diagnostics (non-binding)

- YTD CAGR giveback vs BASE @1x: **+6.86** (MDD help +2.84)
- Trailing 1y CAGR giveback vs BASE @1x: **+5.57** (MDD help +2.84)
- These diagnostics do **not** open Soft-Frozen / stitch / HIGH_BETA ballots.

## Read-through (paper)

1. M3 book `M3_STATE_V0` Section-2: **FAIL**.
2. Continuous M2 ref COVID-ex comparison: M3 -5.52 vs M2 +0.16 → **< M2**.
3. Stage verdict: **FAIL_AUTOPSY**.
4. If FAIL: autopsy — discrete machine did not beat continuous M2 and/or missed Section-2; keep observe E45 sleeves as tax-control refs; do **not** densify E45 α.
5. Even on PASS: **no auto Soft-Frozen / stitch / observe OPEN** — needs dedicated human ballot.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN
- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement
- Freeze doc: `research/e45/E45_M3_THREE_STATE_V0_FROZEN.md`

## Reproduce

```bash
python3 scripts/e45_m3_three_state_risk_paper.py
```

Repro: `repro/e45-m3-three-state-risk/` · Market: `forward/e21/live_market.csv`

