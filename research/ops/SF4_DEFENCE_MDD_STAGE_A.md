# Soft-Frozen 四類 + DH／L4 防禦 × MDD — Stage A

Generated: `2026-09-19T11:27:00.495597+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**

## Coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | mech | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | coexist |
|---|---|---:|---:|---:|---:|---|---|---|
| `SF4_L4_10_DH` | `SF4+L4_10+DH` | 1.192 | +1.57 | -0.76 | -0.5826 | Y | Y | N |
| `SF4_L4_08_DH` | `SF4+L4_08+DH` | 1.177 | +1.47 | -0.59 | -0.5772 | Y | Y | N |
| `SF4_L4_08` | `SF4+L4_08` | 0.714 | +0.82 | -0.20 | -1.2523 | Y | Y | N |
| `SF4_DH` | `SF4+DH_dd06` | 0.589 | +1.19 | -1.20 | -0.2316 | Y | Y | N |
| `SF4_L4_10` | `SF4+L4_10` | 0.425 | +0.99 | -1.12 | -0.9795 | Y | Y | N |
| `SF4_OFFENSE` | `SF4_FROZEN` | 0.257 | +0.50 | -0.48 | -0.8201 | Y | Y | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune FinPriv clips from this defence Stage A.
3. Coexist → Stage B observe; else STOP this defence objective.

Repro: `PYTHONPATH=scripts python3 scripts/e16_sf4_defence_mdd_stage_a.py`
