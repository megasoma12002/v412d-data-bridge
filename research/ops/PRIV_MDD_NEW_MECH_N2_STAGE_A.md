# 民股／四類 × MDD New Mechanism N2 — Stage A

Generated: `2026-09-19T13:44:20.243241+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Mechanism: FinPriv-scoped relocate → cash / 0050 (ETF hi cap **0.35**)

## N2 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | sink | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | gate_on% | coexist |
|---|---|---:|---:|---:|---:|---|---|---:|---|
| `N2_CASH_LOCAL_06` | `CASH` | 1.631 | +2.00 | -0.73 | -0.4135 | Y | Y | 30.2 | N |
| `N2_CASH_DUAL_L08_R05` | `CASH` | 1.026 | +1.41 | -0.77 | -0.5806 | Y | Y | 25.3 | N |
| `N2_CASH_LOCAL_08` | `CASH` | 0.874 | +1.27 | -0.78 | -0.4844 | Y | Y | 22.8 | N |
| `SF4_L4_08_REF` | `REF_L4` | 0.714 | +0.82 | -0.20 | -1.2523 | Y | Y | 25.8 | N |
| `N2_0050_LOCAL_06` | `0050` | 0.501 | +0.72 | -0.44 | -1.0108 | Y | Y | 30.2 | N |
| `N2_0050_LOCAL_08` | `0050` | 0.419 | +0.44 | -0.04 | -0.7726 | N | Y | 22.8 | N |
| `SF4_OFFENSE` | `CONTROL` | 0.257 | +0.50 | -0.48 | -0.8201 | Y | Y | — | N |
| `N2_0050_DUAL_L08_R05` | `0050` | 0.217 | +0.29 | -0.15 | -1.0085 | Y | Y | 25.3 | N |
| `N2_CASH_REL_05` | `CASH` | 0.149 | +0.67 | -1.03 | -0.5373 | Y | Y | 9.5 | N |
| `N1_LOCAL_08_OFF_REF` | `REF_N1` | 0.004 | +0.13 | -0.25 | -0.8024 | Y | Y | 22.8 | N |
| `N2_0050_REL_05` | `0050` | -0.057 | -0.01 | -0.10 | -0.4973 | Y | Y | 9.5 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune FinPriv clips or TAIEX L4 from this N2 Stage A.
3. N2 coexist → Stage B; else STOP N2 / autopsy → N3 or sealed-gate human path.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n2_stage_a.py`
