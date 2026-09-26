# Class D FinPriv Gate V7 Bull+Side F05 — Ballot EXECUTED (ACCEPT)

Date: 2026-09-25/26  
Status: **ACCEPTED · LIVE WIRED (forward-only)**  
Human (exact intent):

```
ACCEPT Class D: FinPriv V7 F05
```

Prior paper path: observe OPEN → near-flat ACCEPT (floor +0.15) → this Class D live wire.

## Live recipe (forward-only)

| Layer | Value |
|---|---|
| Soft-Frozen 3-sleeve router | **KEEP** (公股 R1 features / β densify clips) |
| FIN within-sleeve (FinPub) | **`KD_OPT` KEEP** (+ FUSE softs when live) |
| FinPriv carve | Gate **`REG_BULL_SIDE`** · **`priv_frac=0.05`** · **`PRIV_KD_MAY`** |
| Gate off | FinPriv target **0** — force-sell PRIV board lots |
| Fail-closed | Stale/missing `private_fin_adjusted` (lag > 5d) → gate forced off |
| Risk overlay | **FUSE + COOL_c8 KEEP** |
| Broker live-write | **PREP-only KEEP** |

Paper twin: `V7_REG_BULL_SIDE_F05_KDMAY`.

## Implementation

- `scripts/live_config.py` — `live_fin_priv_v7_f05=True`
- `scripts/live_finhc_v7_f05_cutover.py` — gate / freshness / price merge / force-sell
- `scripts/live_rebalance_orders.py` — `FIN_DUAL_PUB_PRIV` carve + gate-off PRIV sell
- `scripts/live_ledger.py` — holdings universe includes PRIV when Class D live
- `scripts/e21_forward_pipeline.py` / `live_day_commit.py` / `e21_qc.py` — sleeve vals + audit + QC allow PRIV
- `data/market/private_fin_adjusted.csv` — tip refreshed through live asof (FinMind)

## Rollback

```python
# live_config.LiveConfig
live_fin_priv_v7_f05: bool = False
```

Gate-off path force-sells any PRIV holdings on the next live day.

## Non-actions

- Soft-Frozen clip / tip history rewrite  
- Soft-Frozen FIN membership rewrite to 4-sleeve topology  
- Broker `SendAlgo` / `broker_live_write_accepted`  
- NHI DEFAULT tip advance  

## Label

`CLASSD_FINPRIV_V7_F05_ACCEPTED_2026-09-25__LIVE_WIRED_FORWARD_ONLY`
