# E45 C35 + Regime Gate — Research

Generated: `2026-09-08T03:44:27.305032+00:00`
Ballot: **研究 C35 + 多空閘門** · Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **unchanged**
Claimed MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`**

Sensor: M1 `s_{t-1}` · Actuator: `RELOC_BIL_FX` @ **c=0.35** · Gate: Soft-Frozen `regime_{t-1}` allow-list

## Results vs BASE (and vs ungated C35)

| Book | allow | days on | held score | MDD↑pp | CAGR giveback | sealed score | YTD gb | YTD gate | 1y gb | 1y gate | non2020>0.25 |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|
| `M2_RELOC_BIL_FX_C35` | `None` | 100.0% | +1.807 | +2.52 | +1.43 | -0.375 | +7.56 | **PAUSE_REVIEW** | +4.76 | **ALERT** | 3 |
| `M2_C35_GATE_BEAR_CRISIS` | `['Bear', 'Crisis']` | 23.3% | +0.715 | +0.79 | +0.16 | -0.845 | +1.94 | **PASS** | +0.32 | **PASS** | 3 |
| `M2_C35_GATE_NOT_BULL` | `['Bear', 'Crisis', 'Sideways']` | 31.7% | -0.185 | +0.26 | +0.89 | -1.499 | +7.52 | **PAUSE_REVIEW** | +3.81 | **ALERT** | 3 |
| `M2_C35_GATE_CRISIS_ONLY` | `['Crisis']` | 11.8% | -0.664 | -0.59 | +0.15 | -0.635 | +1.66 | **PASS** | +0.15 | **PASS** | 2 |

## Year MDD help pp

| Book | 2015 | 2018 | 2020 | 2022 |
|---|---:|---:|---:|---:|
| `M2_RELOC_BIL_FX_C35` | +1.65 | +0.69 | +2.52 | +4.56 |
| `M2_C35_GATE_BEAR_CRISIS` | +1.17 | +0.53 | +0.79 | +5.06 |
| `M2_C35_GATE_NOT_BULL` | +1.17 | +0.46 | +0.26 | +4.75 |
| `M2_C35_GATE_CRISIS_ONLY` | +1.02 | -0.22 | -0.59 | +4.06 |

## Verdict

- Beat ungated C35 on held-out score: `none`
- Tip YTD giveback improved (>0.5pp lower) vs C35: `['M2_C35_GATE_BEAR_CRISIS', 'M2_C35_GATE_CRISIS_ONLY']`
- Best held-out gated book: `M2_C35_GATE_BEAR_CRISIS`
- Observe lock stays **`M2_RELOC_BIL_FX_C35`** until dedicated retarget ACCEPT.

## Hard non-actions

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · no live wire · no invent MDD

Repro: `repro/e45-c35-regime-gate-20260908/`
