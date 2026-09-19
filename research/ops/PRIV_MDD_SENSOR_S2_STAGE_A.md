# 民股 MDD V2 S2 — USDTWD / CBC sensor Stage A

Generated: `2026-09-19T14:05:12.261334+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Mechanism: lag-1 USDTWD 60d z / CBC rediscount 63d hike → FinPriv→0050

## S2 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | family | thr | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |
|---|---|---|---:|---:|---:|---|---|---:|---|
| `SF4_L4_08_REF` | `REF_L4` | `None` | 0.714 | +0.82 | -0.20 | Y | Y | 25.8 | N |
| `S1_BREADTH_45_REF` | `REF_S1` | `None` | 0.461 | +0.82 | -0.42 | Y | Y | 23.0 | N |
| `N2_0050_LOCAL_08_REF` | `REF_N2` | `None` | 0.419 | +0.44 | -0.04 | N | Y | 22.8 | N |
| `SF4_OFFENSE` | `CONTROL` | `None` | 0.257 | +0.50 | -0.48 | Y | Y | — | N |
| `S2_CBC_HIKE` | `CBC_HIKE` | `d63>0` | 0.203 | +0.50 | -0.59 | Y | Y | 10.2 | N |
| `S2_FX_15` | `USDTWD_Z` | `1.5` | -0.951 | -0.19 | -1.09 | N | Y | 6.1 | N |
| `S2_FX_10` | `USDTWD_Z` | `1.0` | -1.757 | -1.32 | -0.48 | Y | Y | 12.1 | N |
| `S2_OR_MID` | `OR_MID` | `FX1.0|CBC` | -2.402 | -1.32 | -2.16 | Y | Y | 21.2 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune N1–N3 / S1 thresholds from this S2 Stage A.
3. S2 coexist → Stage B; else STOP V2 sensor ladder / Soft-Frozen KEEP.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_sensor_s2_stage_a.py`
