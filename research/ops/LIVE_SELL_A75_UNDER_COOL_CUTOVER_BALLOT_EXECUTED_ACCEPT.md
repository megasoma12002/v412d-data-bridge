# Live cutover ballot — EXECUTED ACCEPT (SELL_a75 under COOL)

Date: 2026-09-26  
Human ballot (exact intent): **`Accept上live`** (context: SOFT near-flat `SELL_a75` already EXECUTED)  
Normalized: `ACCEPT Live cutover: SELL_a75 under COOL (keep FUSE+COOL)`  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Prior paper: `ACCEPT near-flat: SELL_a75 under COOL (CAGR floor +0.15)` → `NEAR_FLAT_HIT` · observe OPERATING.

## Live recipe (forward-only) — coexists with COOL

| Layer | Value |
|---|---|
| Soft-Frozen clips | **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] KEEP** |
| FIN / TEL within-sleeve | **`KD_OPT` / `TEL_EQUAL` KEEP** |
| Offense Soft sell amp | **`SELL_a75`** (boost **0.75**; was 0.50 / a05) |
| Sleeve / FUSE | **`FUSE_ADDITIVE` KEEP** |
| Risk overlay | **`COOL_c8_f50_d21` KEEP** (not replaced) |
| Class D FinPriv | **V7 F05 KEEP** |
| Independent Soft observe | stays **`SELL_a05`** paper (not this cutover) |

## Implementation

- `scripts/live_config.py` — `live_fuse_soft_sell_boost=0.75` + ballot string  
- `scripts/live_dh_fuse_cutover.py` — FUSE soft sell panels / offense NAV use live boost  
- `scripts/soft_assist_helpers.py` — `build_observe_sell_panel(..., boost=)` override  
- `scripts/live_day_commit.py` — tip stamp `fuse_soft_sell_*`  
- Soft-Frozen tip **KEEP** — no history rewrite · broker PREP-only  

## Rollback

```python
# live_config.LiveConfig
live_fuse_soft_sell_boost: float = 0.5  # restore SELL_a05
```

COOL / FUSE flags unchanged.

## Non-actions

- Soft-Frozen clip / KD / TEL flip  
- Tip history wipe/replay  
- Broker `SendAlgo` / `broker_live_write_accepted`  
- Loosen or disable COOL  
- Flip independent Soft-assist observe sleeve to a75  

## Label

`LIVE_SELL_A75_UNDER_COOL_CUTOVER_ACCEPTED_2026-09-26__KEEP_FUSE_COOL__FORWARD_ONLY`
