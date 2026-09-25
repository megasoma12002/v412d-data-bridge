# ACCEPT — R2 / Stage B MDD band floor −15%

Status: **ACCEPTED** (human 2026-09-25: 「接受-15%」)  
Soft-Frozen tip: **KEEP** · no live wire

## Ballot

> `ACCEPT R2/Stage-B held-MDD band floor widen from -14.5% to -15% (band [-15%, -13%]); re-score Stage B tip-safe FAST only; Soft-Frozen KEEP; no live wire.`

## Effect

- Re-score `HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN` with `max_drawdown >= -0.15`.
- Does **not** flip Soft-Frozen clip / FUSE / DH.
- Does **not** by itself OPEN paper observe (separate ballot).

## Rescore reading (same NAV paths)

Verdict upgrades: **`TIP_FAIL` → `TIPSAFE_STRETCH`**

| id | held CAGR | held MDD | held gb pp | tip |
|---|---:|---:|---:|---|
| **`COOL_c8_f50_d21`** (best gb) | 15.29% | −14.86% | **+0.27** | pass |
| **`GATE_g04_f50_d21`** | 15.17% | −14.61% | **+0.39** | pass |

Both clear stretch (gb ≤ 0.56pp) under the new band. Anchor FAST remains tip-fail.

Label: `ACCEPT_2026-09-25_R2_MDD_BAND_FLOOR_15`
