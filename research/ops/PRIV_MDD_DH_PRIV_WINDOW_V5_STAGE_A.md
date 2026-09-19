# 民股 MDD V5 — DH FinPriv window Stage A

Generated: `2026-09-19T14:57:20.750207+00:00`
Status: **STAGE_A_SCORE_POS_GATES_FAIL** · baseline **`LIVE_PUB_KD`** · frozen offense **`SF4_P60-90_V0-15_F10_KD`**
Soft-Frozen **KEEP** · live wire **false** · sealed gate **unchanged**
Enter: frozen `DH_dd06_vz1p0` (dd=0.06, vol_z=1.0) on offense-book features
Actuator: while DEFEND → FinPriv relocate only (≠ whole-book shrink)

## V5 coexist

- **None**

## Ranked vs LIVE_PUB_KD

| book | sink/exit | score_mdd | MDD↑ held | MDD↑ sealed | tip | tipMDD | gate_on% | coexist |
|---|---|---:|---:|---:|---|---|---:|---|
| `SF4_L4_08_REF` | `None/None` | 0.714 | +0.82 | -0.20 | Y | Y | 25.8 | N |
| `V5_DH_CASH_XDEF` | `CASH/XDEF` | 0.628 | +0.84 | -0.42 | Y | Y | 1.2 | N |
| `SF4_DH_REF` | `SHRINK/XDEF` | 0.469 | +1.08 | -1.22 | Y | Y | 1.2 | N |
| `N2_0050_LOCAL_08_REF` | `None/None` | 0.419 | +0.44 | -0.04 | N | Y | 22.8 | N |
| `SF4_OFFENSE` | `None/None` | 0.257 | +0.50 | -0.48 | Y | Y | — | N |
| `V5_DH_0050_XTIGHT` | `0050/XTIGHT` | 0.221 | +0.36 | -0.27 | Y | Y | 1.4 | N |
| `V5_DH_0050_XDEF` | `0050/XDEF` | 0.015 | +0.21 | -0.38 | Y | Y | 1.2 | N |
| `V5_DH_0050_XLONG` | `0050/XLONG` | 0.015 | +0.21 | -0.38 | Y | Y | 1.2 | N |
| `V5_DH_0050_XLOOSE` | `0050/XLOOSE` | 0.015 | +0.21 | -0.38 | Y | Y | 1.2 | N |
| `V5_DH_0050_NOT2` | `0050/XDEF_NOT2` | 0.002 | +0.18 | -0.35 | Y | Y | 1.7 | N |
| `V5_DH_PUB_XDEF` | `PUB/XDEF` | -0.214 | +0.33 | -1.10 | Y | Y | 1.2 | N |

## Binding

1. Soft-Frozen stays 3-sleeve 公股 until Class D ACCEPT.
2. Do not retune DH enter / N1–V4 / SF4 clips from this Stage A.
3. V5 coexist → Stage B; else STOP V5 · Soft-Frozen KEEP.

Repro: `PYTHONPATH=scripts python3 scripts/e16_priv_mdd_dh_priv_window_v5_stage_a.py`
