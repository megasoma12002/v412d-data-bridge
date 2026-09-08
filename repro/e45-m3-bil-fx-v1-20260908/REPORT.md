# E45 M3 PAPER — Three-State + RELOC_BIL_FX (v1)

Generated: `2026-09-08T06:11:16.854209+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**.
Freeze: **`E45_M3_THREE_STATE_BIL_FX_V1_FROZEN_2026-09-08`** (frozen before metrics).
Honesty: `BIL_FX=BIL×USDTWD mid (FX risk; mid optimistic); discrete states paper-only; not C35×regime soft-mult`

## Verdict: **FAIL_AUTOPSY**

## State occupancy

| State | Share |
|---|---:|
| `CRASH` | 4.0% |
| `NORMAL` | 71.9% |
| `SLOW_BEAR` | 24.1% |

## Held-out deltas @1x (incl. COVID-ex)

| Book | Kind | MDD↑pp | Giveback | Score | COVID-ex | Years | tip clean |
|---|---|---:|---:|---:|---:|---|---|
| `M2_RELOC_BIL_FX_C35` | ref_m2_continuous | +2.52 | +1.43 | +1.81 | +3.72 | 2015,2018,2020,2022 | False |
| `SLEEVE_FIN_ONLY_A10` | ref_e45_sleeve | +0.47 | +0.31 | +0.32 | -0.43 | 2020 | True |
| `BLEND_E45_A05` | ref_e45 | +0.14 | +0.09 | +0.10 | +0.17 | — | True |
| `M3_STATE_V0` | ref_m3_v0_tel | -0.44 | +2.13 | -1.51 | -3.85 | — | False |
| `M3_BIL_FX_V1` | m3_bil_fx_v1 | +0.25 | +4.68 | -2.10 | -2.11 | 2015,2018,2022 | False |
| `BASE_E16_E18_E22_v2s` | ref | +0.00 | +0.00 | +0.00 | +0.00 | — | True |

## Section-2 qualification

| Book | Multi≥2 | Strict non-COVID≥2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `BASE_E16_E18_E22_v2s` | N | N | N | Y | N | N | NO |
| `BLEND_E45_A05` | N | N | Y | Y | Y | N | NO |
| `SLEEVE_FIN_ONLY_A10` | N | N | Y | Y | N | Y | NO |
| `M2_RELOC_BIL_FX_C35` | Y | Y | Y | Y | Y | Y | YES |
| `M3_STATE_V0` | N | N | N | Y | N | N | NO |
| `M3_BIL_FX_V1` | Y | Y | N | Y | N | N | NO |

## Stage gate vs continuous M2 C35

- M3 Section-2 PASS? **NO**
- M3 COVID-ex: `-2.11` · M2 C35 COVID-ex: `+3.72` · M3≥M2? **NO**
- Stage verdict: **FAIL_AUTOPSY**

## Tip diagnostics @1x (non-binding)

| Book | YTD gb | YTD | 1y gb | 1y |
|---|---:|---|---:|---|
| `BASE_E16_E18_E22_v2s` | +0.00 | **PASS** | +0.00 | **PASS** |
| `BLEND_E45_A05` | +1.86 | **PASS** | +1.91 | **PASS** |
| `SLEEVE_FIN_ONLY_A10` | +2.98 | **PASS** | +2.80 | **PASS** |
| `M2_RELOC_BIL_FX_C35` | +7.56 | **PAUSE_REVIEW** | +4.76 | **ALERT** |
| `M3_STATE_V0` | +7.19 | **PAUSE_REVIEW** | +4.97 | **ALERT** |
| `M3_BIL_FX_V1` | +15.24 | **PAUSE_REVIEW** | +11.17 | **PAUSE_REVIEW** |

## Read-through

1. Ladder continuation after M3-TEL fail: swap actuator to true DEF `RELOC_BIL_FX`.
2. Do **not** treat this as Soft_A / hard-regime soft-mult on ungated C35.
3. If FAIL: autopsy; keep M2 C35 observe + Soft_A tip twin options; continue other new sensors/actuators — do **not** densify C35×regime knobs.
4. Even on PASS: dedicated human ballot required for any observe OPEN; stitch still FORBIDDEN.

Repro: `repro/e45-m3-bil-fx-v1-20260908/`

```bash
python3 scripts/e45_m3_bil_fx_v1_paper.py
```
