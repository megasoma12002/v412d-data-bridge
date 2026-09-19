# 公股＋民營並存 × MDD — Stage A

Generated: `2026-09-19T11:18:54.615729+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · Soft-Frozen **KEEP** · live wire **false**
Charter: `PUB_PRIV_COEXIST_MDD_CHARTER.md` · asof **2026-09-16** · challengers **25**

Baseline heldout CAGR/MDD: **16.32%** / **-24.36%**
Baseline sealed CAGR/MDD: **22.37%** / **-9.50%**

## Coexist

- **None**

## Ranked vs LIVE_PUB_KD (by score_mdd)

| book | mech | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | coexist |
|---|---|---:|---:|---:|---:|---|---|---|
| `SF4_CTRL_PUB_ONLY` | `SF4_CLIP` | 1.302 | +1.62 | -0.64 | -0.5043 | Y | Y | N |
| `SF4_P60-90_V0-15_F10_KD` | `SF4_CLIP` | 0.257 | +0.50 | -0.48 | -0.8201 | Y | Y | N |
| `SF4_P60-90_V5-20_F15_EQ` | `SF4_CLIP` | 0.120 | +0.70 | -1.16 | -1.3518 | Y | Y | N |
| `SF4_P60-90_V0-20_F10_KD` | `SF4_CLIP` | 0.119 | +0.46 | -0.67 | -0.8936 | Y | Y | N |
| `DUAL_P90_EQ` | `DUAL_SPLIT` | 0.107 | +0.86 | -1.51 | -1.8507 | Y | Y | N |
| `SF4_P60-90_V5-25_F15_KD` | `SF4_CLIP` | 0.088 | +0.19 | -0.21 | -1.4058 | Y | Y | N |
| `SF4_P60-90_V0-15_F15_KD` | `SF4_CLIP` | 0.070 | +0.27 | -0.40 | -1.4018 | Y | Y | N |
| `DUAL_P90_KD` | `DUAL_SPLIT` | 0.051 | +0.66 | -1.21 | -1.6152 | Y | Y | N |
| `SF4_P60-90_V5-20_F15_KD` | `SF4_CLIP` | -0.096 | +0.17 | -0.54 | -1.2563 | Y | Y | N |
| `SF4_P60-90_V0-20_F10_EQ` | `SF4_CLIP` | -0.127 | +0.27 | -0.80 | -0.6889 | Y | Y | N |
| `SF4_P60-90_V0-20_F15_KD` | `SF4_CLIP` | -0.178 | +0.25 | -0.86 | -1.2621 | Y | Y | N |
| `SF4_P60-90_V5-25_F15_EQ` | `SF4_CLIP` | -0.215 | +0.27 | -0.97 | -1.312 | Y | Y | N |
| `SF4_P60-90_V0-15_F15_EQ` | `SF4_CLIP` | -0.274 | +0.22 | -0.99 | -1.2701 | Y | Y | N |
| `SF4_P60-90_V5-20_F10_KD` | `SF4_CLIP` | -0.289 | -0.11 | -0.35 | -1.0826 | Y | Y | N |
| `SF4_P60-90_V0-20_F15_EQ` | `SF4_CLIP` | -0.311 | -0.23 | -0.16 | -1.1165 | Y | Y | N |
| `DUAL_P85_KD` | `DUAL_SPLIT` | -0.318 | +0.81 | -2.25 | -2.2593 | Y | Y | N |
| `SF4_P60-90_V5-20_F10_EQ` | `SF4_CLIP` | -0.456 | -0.05 | -0.80 | -0.3673 | Y | Y | N |
| `DUAL_P85_EQ` | `DUAL_SPLIT` | -0.510 | +0.60 | -2.22 | -2.081 | Y | Y | N |
| `SF4_P60-90_V5-25_F10_EQ` | `SF4_CLIP` | -0.521 | -0.22 | -0.60 | -0.8341 | Y | Y | N |
| `DUAL_P80_KD` | `DUAL_SPLIT` | -0.843 | +0.37 | -2.42 | -2.4561 | Y | Y | N |
| `SF4_P60-90_V5-25_F10_KD` | `SF4_CLIP` | -0.879 | -0.72 | -0.32 | -0.1186 | Y | Y | N |
| `SF4_P60-90_V0-15_F10_EQ` | `SF4_CLIP` | -1.171 | -0.81 | -0.71 | -0.3852 | Y | Y | N |
| `DUAL_P75_EQ` | `DUAL_SPLIT` | -1.514 | +0.38 | -3.78 | -3.2354 | Y | Y | N |
| `DUAL_P80_EQ` | `DUAL_SPLIT` | -1.968 | -0.24 | -3.46 | -2.4316 | Y | Y | N |
| `DUAL_P75_KD` | `DUAL_SPLIT` | -2.654 | -0.55 | -4.21 | -3.2068 | Y | Y | N |

## Binding

1. Soft-Frozen live membership stays **公股 R1** until Class D ACCEPT.
2. Do **not** promote `#257` priv-replace from this screen.
3. Coexist → open dual-paper observe ballot (Stage B); else **STOP** this objective.

Repro: `PYTHONPATH=scripts python3 scripts/e16_pub_priv_coexist_mdd_stage_a.py`
Repro dir: `repro/pub-priv-coexist-mdd-stagea/`
