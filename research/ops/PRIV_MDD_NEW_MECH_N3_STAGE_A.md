# 民股／四類 × MDD New Mechanism N3 — Stage A

Generated: `2026-09-19T13:48:14.853574+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Mechanism: three-state (OFFENSE / COEXIST_DEFEND+N2 / PUB_ONLY) on FinPriv sleeve DD

## N3 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | mid/high/sink | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | %off/%def/%pub | coexist |
|---|---|---:|---:|---:|---|---|---|---|
| `N3_L06_L10_CASH` | `-0.06/-0.1/CASH` | 0.920 | +1.36 | -0.88 | Y | Y | 70/12/19 | N |
| `SF4_L4_08_REF` | `REF_L4` | 0.714 | +0.82 | -0.20 | Y | Y | — | N |
| `N2_0050_LOCAL_08_REF` | `REF_N2` | 0.419 | +0.44 | -0.04 | N | Y | — | N |
| `SF4_OFFENSE` | `CONTROL` | 0.257 | +0.50 | -0.48 | Y | Y | — | N |
| `N3_L08_L12_CASH` | `-0.08/-0.12/CASH` | 0.198 | +0.62 | -0.83 | Y | Y | 77/7/16 | N |
| `N3_L08_L10_0050` | `-0.08/-0.1/0050` | -0.156 | +0.03 | -0.37 | Y | Y | 77/4/19 | N |
| `N3_L08_L12_0050` | `-0.08/-0.12/0050` | -0.396 | +0.05 | -0.89 | Y | Y | 77/7/16 | N |
| `N3_L06_L08_0050` | `-0.06/-0.08/0050` | -0.475 | -0.09 | -0.60 | Y | Y | 70/7/23 | N |
| `N3_L06_L10_0050` | `-0.06/-0.1/0050` | -0.866 | -0.37 | -0.99 | Y | Y | 70/12/19 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune FinPriv clips or TAIEX L4 from this N3 Stage A.
3. N3 coexist → Stage B; else STOP new-mechanism ladder / human sealed-gate path.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_new_mech_n3_stage_a.py`
