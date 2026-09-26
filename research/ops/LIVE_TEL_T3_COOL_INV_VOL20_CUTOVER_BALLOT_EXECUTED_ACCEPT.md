# Live cutover ballot — EXECUTED ACCEPT (T3_COOL_INV_VOL20 TEL within-sleeve)

Date: 2026-09-26  
Human ballot (exact):

```
請上live
```

Normalized: `ACCEPT Live cutover: T3_COOL_INV_VOL20 (TEL within-sleeve under COOL)`  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Prior paper: Stage A **`TEL_WITHIN_SOFT`** → densify **`TEL_NEARFLAT_READY`**  
Champion: `T3_COOL_INV_VOL20` / `D3_A100_C100_B00` · held CAGR↑ **+0.16pp** · MDD/tip OK · near-flat floor +0.15

## Live recipe (forward-only)

| Layer | Value |
|---|---|
| Soft-Frozen clips | **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] KEEP** |
| FIN within-sleeve | **`KD_OPT` KEEP** |
| TEL within-sleeve | **`T3_COOL_INV_VOL20`**: `TEL_RS_SOFT_TILT` + INV_VOL20 when `cool_exposure<1`; else **`TEL_EQUAL`** |
| Offense Soft sell | **`SELL_a75` KEEP** |
| FUSE / COOL | **`FUSE_ADDITIVE` + `COOL_c8_f50_d21` KEEP** |
| Class D FinPriv | **V7 F05 KEEP** |
| Satellite | **`CONF_RET3_A10_H5`/`00631L` KEEP** |
| Fail-closed | Missing cool / score build fail → **TEL_EQUAL** |
| Broker live-write | **PREP-only KEEP** |

## Implementation

- `scripts/live_config.py` — `live_tel_t3_cool_inv_vol20=True` + ballot string  
- `scripts/live_tel_t3_invvol_cutover.py` — INV_VOL20 scores + cool gate  
- `scripts/live_rebalance_orders.py` — Telecom path uses soft-tilt when defending  
- `scripts/e21_forward_pipeline.py` — pass `cool_exposure_today` · signal stamps  
- `scripts/live_day_commit.py` — portfolio_state cutover stamp  

## Rollback

```python
# live_config.LiveConfig
live_tel_t3_cool_inv_vol20: bool = False
```

Next tip day reverts Telecom to equal-split.

## Non-actions

- Soft-Frozen clip / FIN KD flip  
- Tip history wipe/replay  
- Broker `SendAlgo` / `broker_live_write_accepted`  
- Reopen TEL_PRE_EXDIV_KD / async STOP  
- Retune COOL / FUSE / SELL_a75 / CONF_RET3  

## Evidence

- `TEL_WITHIN_SLEEVE_DECISION_PACK.md` · `TEL_T3_DENSIFY_DECISION_PACK.md`  
- Checklist: `CUTOVER_CHECKLIST_TEL_T3_COOL_INV_VOL20.md`

## Label

`LIVE_TEL_T3_COOL_INV_VOL20_CUTOVER_ACCEPTED_2026-09-26__FORWARD_ONLY`
