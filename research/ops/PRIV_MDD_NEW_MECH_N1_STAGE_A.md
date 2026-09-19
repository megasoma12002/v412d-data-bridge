# 民股／四類 × MDD New Mechanism N1 — Stage A

Generated: `2026-09-19T13:37:58.963469+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Mechanism: FinPriv regime membership (LOCAL sleeve DD / REL vs FinPub / DUAL)

## N1 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | family | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | gate_on% | coexist |
|---|---|---:|---:|---:|---:|---|---|---:|---|
| `SF4_L4_08_REF` | `REF_L4` | 0.714 | +0.82 | -0.20 | -1.2523 | Y | Y | 25.8 | N |
| `N1_LOCAL_06` | `LOCAL` | 0.658 | +0.98 | -0.65 | -1.1096 | Y | Y | 30.2 | N |
| `SF4_OFFENSE` | `CONTROL` | 0.257 | +0.50 | -0.48 | -0.8201 | Y | Y | — | N |
| `N1_REL_08` | `REL` | 0.041 | +0.51 | -0.94 | -0.8205 | Y | Y | 3.0 | N |
| `N1_LOCAL_08` | `LOCAL` | 0.004 | +0.13 | -0.25 | -0.8024 | Y | Y | 22.8 | N |
| `N1_DUAL_L08_R05` | `DUAL` | -0.147 | +0.11 | -0.52 | -1.132 | Y | Y | 25.3 | N |
| `N1_LOCAL_10` | `LOCAL` | -0.321 | +0.17 | -0.98 | -0.7215 | Y | Y | 18.6 | N |
| `N1_REL_03` | `REL` | -0.781 | -0.14 | -1.28 | -0.6269 | Y | Y | 19.6 | N |
| `N1_REL_05` | `REL` | -0.785 | -0.56 | -0.45 | -0.4636 | Y | Y | 9.5 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune FinPriv clips or TAIEX L4 −8/−10 from this N1 Stage A.
3. N1 coexist → Stage B observe ballot; else STOP N1 / autopsy → N2 or sealed-gate human path.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n1_stage_a.py`
