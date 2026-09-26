# Live cutover ballot — EXECUTED ACCEPT (CONF_RET3_A10_H5 × 00631L)

Date: 2026-09-26  
Human ballot (exact):

```
CONF_RET3_A10_H5 accept live
```

Normalized: `ACCEPT Live cutover: CONF_RET3_A10_H5 (00631L short-assist under COOL)`  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Prior paper: Stage A **`SHORT_ASSIST_HIT`** → observe OPEN `CONF_RET3_A10_H5` · dual-paper OPERATING.

## Live recipe (forward-only) — coexists with COOL + FUSE + SELL_a75

| Layer | Value |
|---|---|
| Soft-Frozen clips | **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] KEEP** |
| FIN / TEL within-sleeve | **`KD_OPT` / `TEL_EQUAL` KEEP** |
| Offense Soft sell | **`SELL_a75` KEEP** |
| FUSE / COOL | **`FUSE_ADDITIVE` + `COOL_c8_f50_d21` KEEP** |
| Class D FinPriv | **V7 F05 KEEP** |
| Satellite OFF | **`00631L`** on COOL exit + 0050 **RET3>0** · α=**0.10** · H=**5** |
| Soft scale | Soft sleeves × `(1 − OFF)` while pulse active |
| Fail-closed | Missing `00631L` proxy px → OFF weight forced **0** |
| Broker live-write | **PREP-only KEEP** |

## Implementation

- `scripts/live_config.py` — `live_conf_ret3_631l=True` + ballot string  
- `scripts/live_conf_ret3_631l_cutover.py` — schedule / px merge / OFF orders / ETF tax set  
- `scripts/live_strategy_targets.py` — Soft scale after COOL  
- `scripts/e21_forward_pipeline.py` — session px + OFF orders + signal/nav stamps  
- `scripts/live_ledger.py` — holdings universe + `live_etf_codes` include `00631L`  
- `scripts/e21_qc.py` — allow `00631L` outside Soft FIN universe check  
- `scripts/live_day_commit.py` — portfolio_state cutover stamp  
- Prices: `data/def_proxies/00631L_ohlcv.csv` (not tip history rewrite)

## Rollback

```python
# live_config.LiveConfig
live_conf_ret3_631l: bool = False
```

Next tip day with `off_weight=0` force-flats any residual `00631L` board lots.

## Non-actions

- Soft-Frozen clip / KD / TEL flip  
- Tip history wipe/replay  
- Broker `SendAlgo` / `broker_live_write_accepted`  
- Loosen or disable COOL / FUSE / SELL_a75  
- Dual-handoff INV (`00632R`) — Stage A SOFT, **not** this ballot  

## Label

`LIVE_CONF_RET3_A10_H5_00631L_CUTOVER_ACCEPTED_2026-09-26__FORWARD_ONLY`
