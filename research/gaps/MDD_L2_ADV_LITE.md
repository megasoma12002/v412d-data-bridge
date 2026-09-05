# L2 MDD Loss-Engine — Adversarial-lite

Generated: `2026-09-05T01:55:33.171602+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.

## Decision: `ADV_LITE_L2_READY_FOR_HELDOUT`

- Locked: **L2_FINCAP_ONLY** (FIN_CAP_50, no gross scale)
- Locked OOF MDD improve: **4.57 pp**
- Placebo P(MDD≥locked) = **0.000** (gate < 0.50; null fin_hi U[0.55,0.95])
- Year-split OK: **True** (positive years=6)
- Bull-day CAGR giveback: **1.1557358755907465 pp** (gate ≤ 1.5)

## Year-split

| Year | BASE MDD | Locked MDD | Improve pp |
|---:|---:|---:|---:|
| 2013 | -8.43% | -7.54% | +0.89 |
| 2014 | -7.51% | -6.69% | +0.82 |
| 2015 | -13.65% | -11.23% | +2.42 |
| 2016 | -5.00% | -3.64% | +1.35 |
| 2017 | -2.95% | -2.63% | +0.32 |
| 2018 | -6.98% | -6.72% | +0.26 |

## Aftermath

- Proceed to **one held-out** (val 2019–2022 + sealed 2023→latest).
- Do **not** retune cuts.
- Do **not** live-wire.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l2_adv_lite/reports/l2_adv_lite_summary.json`
