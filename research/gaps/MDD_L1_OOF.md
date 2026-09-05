# L1 MDD Loss-Engine — OOF Screen

Generated: `2026-09-05T01:24:54.451481+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.

## Decision: `OOF_L1_READY_FOR_ADV_LITE`

- Locked winner: **L1_FINCAP50_COMBO_50**
- OOF window: `2012-12-04` → `2018-12-31`
- Gates: Exact T+1; MDD improve ≥ **3.0 pp**; CAGR giveback ≤ **2.5 pp**

BASE OOF: CAGR=8.8470% MDD=-17.4129% exact_t1=True

| ID | Family | Flag | Scale | OOF CAGR | OOF MDD | MDD Δpp | CAGR giveback pp | Exact T+1 | COVID flag share* | PASS |
|---|---|---|---:|---:|---:|---:|---:|---|---:|---|
| BASE | BASE | NONE | 1.00 | 8.85% | -17.41% | +0.00 | +0.00 | True | 0.0% | — |
| L1_CRISIS_EQ_70 | L1-CRISIS-EQ | CRISIS | 0.70 | 8.88% | -15.02% | +2.40 | -0.03 | True | 13.9% | — |
| L1_CRISIS_EQ_50 | L1-CRISIS-EQ | CRISIS | 0.50 | 8.93% | -13.12% | +4.29 | -0.09 | True | 13.9% | Y |
| L1_CRISIS_EQ_30 | L1-CRISIS-EQ | CRISIS | 0.30 | 8.92% | -11.71% | +5.70 | -0.07 | True | 13.9% | Y |
| L1_STRESS_VOL80_50 | L1-STRESS-DET | VOL80 | 0.50 | 8.52% | -15.66% | +1.75 | +0.33 | True | 97.2% | — |
| L1_STRESS_DD10_50 | L1-STRESS-DET | DD10 | 0.50 | 8.63% | -11.70% | +5.72 | +0.22 | True | 19.4% | Y |
| L1_STRESS_COMBO_70 | L1-STRESS-DET | COMBO | 0.70 | 8.40% | -13.90% | +3.51 | +0.44 | True | 97.2% | Y |
| L1_STRESS_COMBO_50 | L1-STRESS-DET | COMBO | 0.50 | 7.89% | -11.81% | +5.60 | +0.96 | True | 97.2% | Y |
| L1_STRESS_COMBO_30 | L1-STRESS-DET | COMBO | 0.30 | 7.45% | -9.48% | +7.94 | +1.39 | True | 97.2% | Y |
| L1_GROSS_FLOOR_60_COMBO | L1-GROSS-FLOOR | COMBO | 0.60 | 8.13% | -12.81% | +4.60 | +0.71 | True | 97.2% | Y |
| L1_FINCAP50_CRISIS_50 | L1-FINCAP-STACK | CRISIS | 0.50 | 8.04% | -9.78% | +7.63 | +0.81 | True | 13.9% | Y |
| L1_FINCAP50_COMBO_50 | L1-FINCAP-STACK | COMBO | 0.50 | 7.42% | -9.10% | +8.32 | +1.43 | True | 97.2% | Y |

\* COVID flag share is **descriptive only** (2020-01-20→03-19); not used for OOF pass.

## Aftermath

- Proceed to **adversarial-lite** on locked `L1_FINCAP50_COMBO_50` (placebo flag scramble P&lt;0.50).
- Do **not** open held-out until adv-lite PASS.
- Do **not** live-wire; dual paper ledgers on any later promote.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l1_oof/reports/l1_oof_summary.json`
- `/workspace/repro/mdd-loss-engine/l1_oof/outputs/l1_oof_candidates.csv`
