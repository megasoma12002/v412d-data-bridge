# 民股 MDD V6 — shadow relative-NAV FinPriv damp Stage A

Generated: `2026-09-19T15:07:15.651328+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Sensor: undamped shadow `DD_rel(SF4_OFFENSE vs LIVE_PUB)` · δ=**0.05** frozen · lag-1
Actuator: `FinPriv' = FinPriv · (1 − c · u)` · residual → 0050/cash/PUB

## V6 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | c/sink/var | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | mean_u | coexist |
|---|---|---:|---:|---:|---|---|---:|---|
| `V6_C100_CASH` | `1.0/CASH/BASE` | 1.544 | +1.75 | -0.40 | N | Y | 0.153 | N |
| `V6_C50_CASH` | `0.5/CASH/BASE` | 1.175 | +1.47 | -0.59 | Y | Y | 0.153 | N |
| `V6_C100_PUB` | `1.0/PUB/PUB` | 0.849 | +0.97 | -0.24 | Y | Y | 0.153 | N |
| `SF4_L4_08_REF` | `REF_L4` | 0.714 | +0.82 | -0.20 | Y | Y | — | N |
| `V6_C100_0050_ROLL252` | `1.0/0050/ROLL252` | 0.699 | +1.04 | -0.68 | Y | Y | 0.129 | N |
| `N2_0050_LOCAL_08_REF` | `REF_N2` | 0.419 | +0.44 | -0.04 | N | Y | — | N |
| `V6_C50_0050` | `0.5/0050/BASE` | 0.367 | +0.71 | -0.68 | Y | Y | 0.153 | N |
| `V6_C75_0050` | `0.75/0050/BASE` | 0.265 | +0.75 | -0.96 | Y | Y | 0.153 | N |
| `SF4_OFFENSE` | `CONTROL` | 0.257 | +0.50 | -0.48 | Y | Y | — | N |
| `V6_C100_0050_DB01` | `1.0/0050/DB01` | 0.149 | +0.48 | -0.66 | Y | Y | 0.105 | N |
| `V6_C100_0050` | `1.0/0050/BASE` | 0.011 | +0.60 | -1.18 | Y | N | 0.153 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune δ / N1–V5 / SF4 clips / sealed from this Stage A.
3. V6 coexist → Stage B; else STOP V6 · Soft-Frozen KEEP.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_shadow_relnav_v6_stage_a.py`
