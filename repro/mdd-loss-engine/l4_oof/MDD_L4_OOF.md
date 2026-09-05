# L4 MDD Path/FINCAP — OOF Screen

Generated: `2026-09-05T03:31:57.964732+00:00`
Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.
Parents: L1/L2/L3 STOPPED — cut retune forbidden.

## Decision: `OOF_L4_READY_FOR_ADV_LITE`

- Locked winner: **L4_DD_PATH_08_50**
- OOF: `2012-12-04` → `2018-12-31`
- Late-bull proxy: `2017-01-01` → `2018-12-31`
- Gates: Exact T+1; MDD ≥**1.5pp**; CAGR giveback ≤**1.5pp**; late-bull CAGR giveback ≤**1.5pp**
- Selection: **util = MDD_improve_pp − 0.5×late_bull_gb** (no harsh-cap family priority)
- Passers: **5** → L4_FINCAP_70_35, L4_FINCAP_70_50, L4_BLEND_050, L4_DD_PATH_08_50, L4_DD_PATH_10_50

BASE OOF: CAGR=8.8470% MDD=-17.4129% exact_t1=True mean_fin_w=80.3%

| ID | Family | MDD Δpp | CAGR gb pp | Late-bull gb pp | Util | Fin w | Exact T+1 | PASS | Fail |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| BASE | BASE | +0.00 | +0.00 | +0.00 | +0.00 | 80.3% | True | — | — |
| FIN_CAP_50_REF | REF-STOPPED | +4.57 | +0.35 | +1.26 | +3.94 | 50.0% | True |  | not_lockable_reference |
| L3_MILD_35_60_REF | REF-STOPPED | +2.88 | +0.10 | +0.15 | +2.80 | 59.7% | True |  | not_lockable_reference |
| L4_DD_PATH_08_50 | L4-DD-PATH | +2.25 | -0.77 | -0.72 | +2.60 | 76.3% | True | Y | — |
| L4_DD_PATH_10_50 | L4-DD-PATH | +2.14 | -0.44 | -0.73 | +2.51 | 76.9% | True | Y | — |
| L4_BLEND_050 | L4-BLEND-LIGHT | +2.83 | -0.00 | +0.65 | +2.50 | 65.1% | True | Y | — |
| L4_FINCAP_70_35 | L4-FINCAP-70 | +1.71 | -0.05 | -0.50 | +1.96 | 68.6% | True | Y | — |
| L4_FINCAP_70_50 | L4-FINCAP-70 | +1.71 | -0.05 | -0.50 | +1.96 | 68.6% | True | Y | — |
| L4_CRISIS_ONLY_50 | L4-CRISIS-ONLY | +1.31 | -0.01 | +0.22 | +1.20 | 79.2% | True |  | mdd_improve |
| L4_BLEND_025 | L4-BLEND-LIGHT | +1.37 | +0.03 | +0.40 | +1.17 | 72.7% | True |  | mdd_improve |

## Aftermath

- Proceed to **adversarial-lite** on locked `L4_DD_PATH_08_50` (util=2.60; MDD +2.25pp; late-bull gb -0.72pp).
- Do **not** open held-out until adv-lite PASS.
- Do **not** live-wire. Soft-Frozen stays **[0.50, 0.95]**.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l4_oof/reports/l4_oof_summary.json`
- `/workspace/repro/mdd-loss-engine/l4_oof/outputs/l4_oof_candidates.csv`
