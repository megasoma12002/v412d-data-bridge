# Live cutover ballot — EXECUTED ACCEPT (COOL_c8 replace DH, keep FUSE)

Date: 2026-09-25  
Human ballot (exact intent): **`ACCEPT Live cutover: COOL_c8_f50_d21（ replace DH、keep FUSE）。`**  
Normalized: `ACCEPT Live cutover: COOL_c8_f50_d21 (replace DH, keep FUSE)`  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Evidence: `COOL_C8_DH_FUSE_STACK_TRIAL.md` — **不疊** `FUSE_COOL` held 15.07% / −14.62% vs live `FUSE_DH` 14.89% / −24.38%.  
Stack min/× not selected (extra CAGR cost, no material MDD gain).

## Live recipe (forward-only)

| Layer | Value |
|---|---|
| Soft-Frozen FIN clip | **[0.60, 0.90] KEEP** |
| FIN within-sleeve | **`KD_OPT` KEEP** |
| TEL within-sleeve | **`TEL_EQUAL` KEEP** |
| Sleeve targets | **`FUSE_ADDITIVE` KEEP** |
| Risk overlay | **`COOL_c8_f50_d21`** (PROXY x=8%, floor=50%, exit=6%, dwell=21, cool=8) |
| Prior risk overlay | **`DH_dd06` RETIRED** forward-only (`LIVE_DH_EXPOSURE=False`) |
| Stacking | **FORBIDDEN** — DH+COOL both True → SystemExit |

## Implementation

- `scripts/live_config.py` — `LIVE_FUSE_ADDITIVE=True`, `LIVE_DH_EXPOSURE=False`, `LIVE_COOL_EXPOSURE=True`
- `scripts/live_cool_c8_cutover.py` — FUSE offense NAV → COOL exposure
- `scripts/live_strategy_targets.py` — COOL path + stack refuse
- `scripts/e21_forward_pipeline.py` / `live_day_commit.py` / `e21_qc.py` — cool signal fields + QC
- Helpers: `cool_c8_proxy_observe_helpers.LIVE_WIRE=True`; DH helper `LIVE_WIRE=False` (replaced)
- Soft-Frozen tip **KEEP** — no history rewrite

## Rollback

```python
# live_config.LiveConfig
live_cool_exposure: bool = False
# optional restore DH only with dedicated ACCEPT:
# live_dh_exposure: bool = True
```

FUSE stays independent (`live_fuse_additive`).

## Non-actions

- Soft-Frozen clip / KD / TEL flip  
- Tip history wipe/replay  
- Broker `SendAlgo` / `broker_live_write_accepted`  
- Stack DH+COOL  

## Label

`LIVE_COOL_C8_CUTOVER_ACCEPTED_2026-09-25__REPLACE_DH_KEEP_FUSE__FORWARD_ONLY`
