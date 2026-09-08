# E45 C35 Soft Gate — Decision Pack (draft)

Date: 2026-09-08  
Status: **RESEARCH DONE — same-family recovery mostly exhausted**  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock today **`M2_RELOC_BIL_FX_C35`**

## Question

Hard `GATE_BEAR_CRISIS` cleans tip (YTD/1y **PASS**) but sacrifices held-out score **+1.81 → +0.72**. How to improve that long-term score?

## Finding

| Book | Tip YTD/1y | held-out | recovery vs hard→ungated |
|---|---|---:|---:|
| Ungated C35 (lock) | PAUSE / ALERT | **+1.81** | 1.00 |
| **`SOFT_A`** Side0.25/Bear0.75/Crisis1 | **PASS / PASS** | **+0.83** | **+0.11** |
| Hard Bear+Crisis | **PASS / PASS** | +0.72 | 0.00 |
| HYST_K10 (exit hysteresis) | tip dirty | +0.96 | — |
| Stronger Side / Crisis-boost / higher cut | tip dirty **or** worse score | — | — |

Root cause: **2020 MDD help** falls `+2.52 → +0.79` under hard gate. Soft_A only lifts 2020 help to `+0.93`. Restoring ungated defense without tip giveback is **not** available inside C35 × Soft-Frozen regime.

## Optional ballots (not cast)

| Ballot | Effect |
|---|---|
| `KEEP observe C35 ungated` | No change (status quo) |
| `ACCEPT observe retarget C35_SOFT_A` | Paper observe → Soft_A; tip stays PASS; small held-out lift |
| `ACCEPT dual-monitor ungated + Soft_A` | Long-score twin + tip-hygiene twin (no live wire) |
| `DEFER` / leave C35×regime for new mechanism | cheap-protect / tax-control / other actuator |

Live stitch still requires separate second ACCEPT after clean trailing on the chosen book.

## Hard non-actions

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · no live wire · no invent MDD · no auto observe-lock flip.

Artifacts: `E45_C35_SOFT_GATE_RESEARCH.md` · `repro/e45-c35-soft-gate-20260908/`
