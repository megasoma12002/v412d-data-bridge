# L3 MDD Sealed-CAGR — OOF Screen

Generated: `2026-09-05T02:17:17.123357+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.
Parents: L1/L2 STOPPED — cut retune forbidden.

## Decision: `OOF_L3_READY_FOR_ADV_LITE`

- Locked winner: **L3_MILD_35_60**
- OOF: `2012-12-04` → `2018-12-31`
- Late-bull proxy: `2017-01-01` → `2018-12-31`
- Gates: Exact T+1; MDD ≥**2.0pp**; CAGR giveback ≤**1.5pp**; late-bull CAGR giveback ≤**1.5pp**
- Passers: **4**

BASE OOF: CAGR=8.8470% MDD=-17.4129% exact_t1=True mean_fin_w=80.3%

| ID | Family | MDD Δpp | CAGR gb pp | Late-bull gb pp | Fin w | Exact T+1 | PASS | Fail |
|---|---|---:|---:|---:|---:|---|---|---|
| BASE | BASE | +0.00 | +0.00 | +0.00 | 80.3% | True | — | — |
| L2_FINCAP_ONLY | L2-REF | +4.57 | +0.35 | +1.26 | 50.0% | True |  | not_lockable_reference |
| L3_MILD_35_60 | L3-FINCAP-MILD | +2.88 | +0.10 | +0.15 | 59.7% | True | Y | — |
| L3_MILD_35_70 | L3-FINCAP-MILD | +1.71 | -0.05 | -0.50 | 68.6% | True |  | mdd_improve |
| L3_MILD_35_80 | L3-FINCAP-MILD | +0.94 | -0.00 | -0.24 | 76.4% | True |  | mdd_improve |
| L3_MILD_50_60 | L3-FINCAP-MILD | +2.88 | +0.10 | +0.15 | 59.7% | True | Y | — |
| L3_MILD_50_70 | L3-FINCAP-MILD | +1.71 | -0.05 | -0.50 | 68.6% | True |  | mdd_improve |
| L3_MILD_50_80 | L3-FINCAP-MILD | +0.94 | -0.00 | -0.24 | 76.4% | True |  | mdd_improve |
| L3_BLEND_025 | L3-FINCAP-BLEND | +1.37 | +0.03 | +0.40 | 72.7% | True |  | mdd_improve |
| L3_BLEND_050 | L3-FINCAP-BLEND | +2.83 | -0.00 | +0.65 | 65.1% | True | Y | — |
| L3_BLEND_075 | L3-FINCAP-BLEND | +3.74 | +0.10 | +0.76 | 57.6% | True | Y | — |

## Aftermath

- Proceed to **adversarial-lite** on locked `L3_MILD_35_60`.
- Do **not** open held-out until adv-lite PASS.
- Do **not** live-wire. Soft-Frozen stays **[0.50, 0.95]**.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l3_oof/reports/l3_oof_summary.json`
- `/workspace/repro/mdd-loss-engine/l3_oof/outputs/l3_oof_candidates.csv`
