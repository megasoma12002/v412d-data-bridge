# 民股 MDD V2 S1 — breadth / FinPub–TAIEX sensor Stage A

Generated: `2026-09-19T14:00:09.897140+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Mechanism: lag-1 breadth / FinPub–TAIEX z → FinPriv→0050

## S1 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | family | thr | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |
|---|---|---|---:|---:|---:|---|---|---:|---|
| `S1_FINZ_15` | `FINPUB_TAIEX_Z` | `-1.5` | 1.696 | +2.05 | -0.71 | Y | Y | 18.7 | N |
| `SF4_L4_08_REF` | `REF_L4` | `None` | 0.714 | +0.82 | -0.20 | Y | Y | 25.8 | N |
| `S1_BREADTH_45` | `BREADTH` | `0.45` | 0.461 | +0.82 | -0.42 | Y | Y | 23.0 | N |
| `S1_BREADTH_55` | `BREADTH` | `0.55` | 0.461 | +0.82 | -0.42 | Y | Y | 23.0 | N |
| `N2_0050_LOCAL_08_REF` | `REF_N2` | `None` | 0.419 | +0.44 | -0.04 | N | Y | 22.8 | N |
| `SF4_OFFENSE` | `CONTROL` | `None` | 0.257 | +0.50 | -0.48 | Y | Y | — | N |
| `S1_OR_MID` | `OR_MID` | `B0.45|Z-1.0` | -0.595 | +1.48 | -3.87 | Y | Y | 44.9 | N |
| `S1_FINZ_10` | `FINPUB_TAIEX_Z` | `-1.0` | -3.102 | -1.05 | -4.10 | Y | Y | 29.9 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune N1–N3 or SF4 clips from this S1 Stage A.
3. S1 coexist → Stage B; else STOP S1 / ballot S2 or Soft-Frozen KEEP.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sensor_s1_stage_a.py`
