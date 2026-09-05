# L3 MDD Sealed-CAGR — Adversarial-lite

Generated: `2026-09-05T02:26:41.103938+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.
Parents: L1/L2 STOPPED — cut retune forbidden.

## Decision: `ADV_LITE_L3_READY_FOR_HELDOUT`

- Locked: **L3_MILD_35_60** (FIN clip [0.35, 0.60])
- Locked OOF MDD improve: **2.88 pp**
- Placebo P(MDD≥locked) = **0.042** (gate < 0.50; null fin_hi U[0.55,0.95])
- Year-split OK: **True** (positive years=6)
- Late-bull CAGR giveback: **0.153 pp** (gate ≤ 1.5)

## Year-split

| Year | BASE MDD | Locked MDD | Improve pp |
|---:|---:|---:|---:|
| 2013 | -8.43% | -7.58% | +0.85 |
| 2014 | -7.51% | -6.77% | +0.74 |
| 2015 | -13.65% | -12.17% | +1.48 |
| 2016 | -5.00% | -3.80% | +1.19 |
| 2017 | -2.95% | -2.72% | +0.23 |
| 2018 | -6.98% | -6.78% | +0.20 |

## Aftermath

- Proceed to **one held-out** (val 2019–2022 + sealed 2023→latest).
- Do **not** retune cuts.
- Do **not** live-wire. Soft-Frozen stays **[0.50, 0.95]**.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l3_adv_lite/reports/l3_adv_lite_summary.json`
