# SAT_A20 sealed-hygiene Stage B — Screen

Generated: `2026-09-27T04:37:44Z`
Status: **`PARENT_KEEP`** · α/H densify **OUT** · Soft-Frozen **KEEP** · live wire **false**
Parent `SAT_A20_H5` · Base `BASE_LIVE_CONF` · cool_exits=**38**

HYGIENE_HIT: **0** / 3 STOP books

## Ranked (vs BASE_LIVE_CONF)

| book | kind | stop | CAGR↑h | MDD↑h | MDD↑s | tip | hygiene |
|---|---|---:|---:|---:|---:|---|---|
| `A20_STOP_S02` | STOP | 2% | +0.48 | -0.18 | -0.41 | N | N |
| `SAT_A20_H5` | PARENT | — | +0.33 | -0.31 | -0.10 | Y | N |
| `A20_STOP_S05` | STOP | 5% | +0.33 | -0.31 | -0.10 | Y | N |
| `A20_STOP_S03` | STOP | 3% | +0.29 | -0.31 | -0.31 | Y | N |

## Binding

1. α／H densify **OUT** — STOP overlay only.
2. Soft-Frozen · Exact T+1 · L1=0.05 **KEEP**.
3. Even HYGIENE_HIT → paper only; no live wire.

Repro: `PYTHONPATH=scripts python3 scripts/sat_a20_sealed_hygiene_stageb.py`

Label: `SAT_A20_SEALED_HYGIENE_STAGEB_SCREEN_2026-09-27__PARENT_KEEP`
