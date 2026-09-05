# L4 MDD Path/FINCAP — Adversarial-lite

Generated: `2026-09-05T03:39:36.432056+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.
Parents: L1/L2/L3 STOPPED — cut retune forbidden.

## Decision: `ADV_LITE_L4_READY_FOR_HELDOUT`

- Locked: **L4_DD_PATH_08_50** (TAIEX DD≤-8% → FIN[0.35,0.50])
- Locked OOF MDD improve: **2.25 pp**
- Placebo P(MDD≥locked) = **0.000** (gate < 0.50; DD-mask scramble)
- Year-split OK: **True** (positive years=3)
- Late-bull CAGR giveback: **-0.716 pp** (gate ≤ 1.5)

## Year-split

| Year | BASE MDD | Locked MDD | Improve pp |
|---:|---:|---:|---:|
| 2013 | -8.43% | -8.43% | +0.00 |
| 2014 | -7.51% | -7.62% | -0.11 |
| 2015 | -13.65% | -12.06% | +1.58 |
| 2016 | -5.00% | -4.93% | +0.07 |
| 2017 | -2.95% | -3.03% | -0.08 |
| 2018 | -6.98% | -6.68% | +0.30 |

## Aftermath

- Proceed to **one held-out** (val 2019–2022 + sealed 2023→latest).
- Do **not** retune cuts.
- Do **not** live-wire. Soft-Frozen stays **[0.50, 0.95]**.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l4_adv_lite/reports/l4_adv_lite_summary.json`
