# Next-mechanism Stage A — Screen

Generated: `2026-09-27T04:30:18Z`
Status: **`MECH_HIT`** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · L1=**0.05** · live wire **false**
Base: `BASE_LIVE_CONF` = FUSE+COOL+CONF_RET3 α=0.10 H=5 · OFF=`00631L` · sell_amp=**0.75**
cool_exits=**38** · defend_frac=**16.02%**

MECH_HIT: **1** · CAGR_SOFT: **4** / 7 challengers

## Ranked

| book | track | CAGR↑h | CAGR↑s | MDD↑h | MDD↑s | tip | hit | soft |
|---|---|---:|---:|---:|---:|---|---|---|
| `SAT_A20_H5` | SAT | +0.33 | +0.13 | -0.31 | -0.10 | Y | Y | N |
| `SAT_A15_H5` | SAT | +0.10 | +0.06 | -0.10 | -0.05 | Y | N | Y |
| `E16_M20_050` | E16 | -0.04 | -0.08 | -0.05 | +0.01 | Y | N | Y |
| `SAT_A10_H8` | SAT | +0.05 | +0.32 | -0.18 | -0.50 | N | N | Y |
| `E16_BULL_E20` | E16 | +0.22 | +0.40 | -0.53 | -1.01 | Y | N | N |
| `PRIV_V8BEST_F08` | PRIV | -1.07 | -1.42 | -0.27 | -2.73 | N | N | Y |
| `PRIV_V8BEST_F10` | PRIV | -1.10 | -1.23 | -0.73 | -2.77 | N | N | N |

## Base windows (heldout)

`BASE_LIVE_CONF` CAGR=0.163054 · MDD=-0.144234 · pulse_frac=0.031794

## Binding

1. Soft-Frozen clips · Exact T+1 · L1=0.05 **KEEP**.
2. Even MECH_HIT → paper only; **at most one** track for ACCEPT discussion.
3. PRIV books omit CONF DEF (simulate_core FinPriv+DEF not co-supported).

Repro: `PYTHONPATH=scripts python3 scripts/next_mech_stagea.py`

Label: `NEXT_MECH_STAGEA_SCREEN_2026-09-27__MECH_HIT`
