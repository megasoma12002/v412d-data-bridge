# ACCEPT — R2 MDD band floor −14.5%

Status: **ACCEPTED** (human 2026-09-25: 「接受 MDD 略深到 −14.5%」)  
Soft-Frozen tip: **KEEP** · no live wire

## Ballot

> `ACCEPT R2 held-MDD band floor widen from -14.0% to -14.5% (band [-14.5%, -13%]); re-score Stage A only; Soft-Frozen KEEP; no live wire.`

## Effect

- Re-score `HELD_MDD17_R2_CAGR0_STAGEA_SCREEN` with `max_drawdown >= -0.145`.
- Does **not** flip Soft-Frozen clip / FUSE / DH.
- Does **not** by itself OPEN paper observe (separate ballot).

## Rescore reading (same NAV paths)

| id | held MDD | held gb pp | tip YTD/1y MDD↑ | under new band |
|---|---:|---:|---|---|
| `FAST_x08_ex06_f50_d21` | −14.45% | **+0.56** | **fail** (−0.99pp) | in-band but tip hygiene fail → not PRIMARY/BEATS |
| `REF_PROXY_x08_f50` | −14.34% | +1.11 | pass | in-band; gb just over beats-R1 1.0pp cap |
| `STH_*` band hits | −13.1%～−14.3% | +1.3～+1.7 | pass | in-band; gb worse than R1 ref |

Stage A verdict after rescore: still **`BAND_ONLY`** (no stretch/primary/beats-R1 clear with tip hygiene).

Label: `ACCEPT_2026-09-25_R2_MDD_BAND_FLOOR_14_5`
