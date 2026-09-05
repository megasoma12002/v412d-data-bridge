# L2 MDD Loss-Engine — OOF Screen

Generated: `2026-09-05T01:54:18.326487+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.
Parent: L1 STOPPED — L1 cut retune forbidden.

## Decision: `OOF_L2_READY_FOR_ADV_LITE`

- Locked winner: **L2_FINCAP_ONLY**
- OOF: `2012-12-04` → `2018-12-31`
- Gates: Exact T+1; MDD ≥**3.0pp**; CAGR giveback ≤**2.5pp**; bull CAGR giveback ≤**1.5pp**; bull flag share ≤**20%**

BASE OOF: CAGR=8.8470% MDD=-17.4129% exact_t1=True

| ID | Family | MDD Δpp | CAGR gb pp | Bull gb pp | Bull flag | Exact T+1 | PASS | Fail |
|---|---|---:|---:|---:|---:|---|---|---|
| BASE | BASE | +0.00 | +0.00 | +0.00 | 0.0% | True | — | — |
| L2_FINCAP_ONLY | L2-FINCAP-ONLY | +4.57 | +0.35 | +1.16 | 0.0% | True | Y | — |
| L2_DD_PATH_08_70 | L2-DD-PATH | +3.07 | +0.04 | -0.03 | 5.7% | True | Y | — |
| L2_DD_PATH_08_50 | L2-DD-PATH | +5.54 | +0.17 | +0.22 | 5.7% | True | Y | — |
| L2_DD_PATH_10_50 | L2-DD-PATH | +5.72 | +0.22 | +0.60 | 4.6% | True | Y | — |
| L2_DD_PATH_05_70 | L2-DD-PATH | +3.44 | +1.18 | +2.01 | 12.9% | True | — | bull_cagr_giveback |
| L2_SPIKE_SHORT_90_3_70 | L2-SPIKE-SHORT | -0.03 | +0.16 | +0.71 | 9.8% | True | — | mdd_improve |
| L2_SPIKE_SHORT_90_5_50 | L2-SPIKE-SHORT | +0.60 | +0.32 | +1.37 | 10.3% | True | — | mdd_improve |
| L2_ASYM_CRISIS_DD_50_5 | L2-ASYM-SCALE | +5.58 | +0.09 | +0.21 | 5.7% | True | Y | — |
| L2_ASYM_CRISIS_DD_50_10 | L2-ASYM-SCALE | +5.80 | +0.29 | +0.31 | 6.4% | True | Y | — |
| L2_FINCAP_DD_08_70 | L2-FINCAP+DD | +6.92 | +0.95 | +1.82 | 5.7% | True | — | bull_cagr_giveback |
| L2_FINCAP_DD_10_50 | L2-FINCAP+DD | +8.82 | +1.20 | +2.39 | 4.6% | True | — | bull_cagr_giveback |

## Aftermath

- Proceed to **adversarial-lite** on locked `L2_FINCAP_ONLY`.
- Do **not** open held-out until adv-lite PASS.
- Do **not** live-wire.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l2_oof/reports/l2_oof_summary.json`
- `/workspace/repro/mdd-loss-engine/l2_oof/outputs/l2_oof_candidates.csv`
