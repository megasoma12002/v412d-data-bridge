# L1 MDD Loss-Engine — Adversarial-lite

Generated: `2026-09-05T01:26:44.122043+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.

## Decision: `ADV_LITE_L1_READY_FOR_HELDOUT`

- Locked: **L1_FINCAP50_COMBO_50** (FIN_CAP_50 + COMBO × scale 0.5)
- Locked OOF MDD improve: **8.32 pp**; CAGR giveback **1.43 pp**
- Placebo P(MDD improve ≥ locked) = **0.000** (gate &lt; 0.50; n=24, seed=20260905)
- Year-split OK: **True** (positive years=6)
- Exact T+1: **True**

## Year-split (OOF calendar years)

| Year | BASE MDD | Locked MDD | Improve pp |
|---:|---:|---:|---:|
| 2013 | -8.43% | -7.54% | +0.89 |
| 2014 | -7.51% | -4.43% | +3.08 |
| 2015 | -13.65% | -8.44% | +5.21 |
| 2016 | -5.00% | -3.67% | +1.33 |
| 2017 | -2.95% | -2.63% | +0.32 |
| 2018 | -6.98% | -6.13% | +0.85 |

## Aftermath

- Proceed to **one held-out** (val 2019–2022 + sealed 2023→latest).
- Do **not** retune cuts.
- Do **not** live-wire; dual paper ledgers (BASE + L1) on any later promote.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l1_adv_lite/reports/l1_adv_lite_summary.json`
- `/workspace/repro/mdd-loss-engine/l1_adv_lite/outputs/l1_adv_lite_placebos.csv`
