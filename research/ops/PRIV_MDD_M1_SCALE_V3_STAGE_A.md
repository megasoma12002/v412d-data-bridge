# 民股 MDD V3 — M1 proportional FinPriv scale Stage A

Generated: `2026-09-19T14:12:12.613424+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Mechanism: FinPriv × (1 − c · M1 `s_{t-1}`) · residual → 0050/cash · `E45_M1_STATE_VECTOR_V0_FROZEN_2026-09-06`

## V3 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | c/sink | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | mean_e | coexist |
|---|---|---:|---:|---:|---|---|---:|---|
| `V3_C100_CASH` | `1.0/CASH` | 1.612 | +1.82 | -0.41 | N | Y | 0.687 | N |
| `V3_C75_CASH` | `0.75/CASH` | 1.409 | +1.64 | -0.46 | N | Y | 0.765 | N |
| `V3_C50_CASH` | `0.5/CASH` | 1.147 | +1.46 | -0.63 | N | Y | 0.843 | N |
| `V3_C25_CASH` | `0.25/CASH` | 0.899 | +1.23 | -0.67 | Y | Y | 0.922 | N |
| `SF4_L4_08_REF` | `REF_L4` | 0.714 | +0.82 | -0.20 | Y | Y | — | N |
| `V3_C50_0050` | `0.5/0050` | 0.632 | +0.85 | -0.44 | Y | Y | 0.843 | N |
| `N2_0050_LOCAL_08_REF` | `REF_N2` | 0.419 | +0.44 | -0.04 | N | Y | — | N |
| `V3_C100_0050` | `1.0/0050` | 0.326 | +0.68 | -0.71 | Y | Y | 0.687 | N |
| `V3_C25_0050` | `0.25/0050` | 0.301 | +0.56 | -0.52 | Y | Y | 0.922 | N |
| `SF4_OFFENSE` | `CONTROL` | 0.257 | +0.50 | -0.48 | Y | Y | — | N |
| `V3_C75_0050` | `0.75/0050` | -0.229 | +0.20 | -0.86 | Y | Y | 0.765 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune M1 feature maps / N1–N3 / V2 from this Stage A.
3. V3 coexist → Stage B; else STOP V3 · Soft-Frozen KEEP.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_m1_scale_v3_stage_a.py`
