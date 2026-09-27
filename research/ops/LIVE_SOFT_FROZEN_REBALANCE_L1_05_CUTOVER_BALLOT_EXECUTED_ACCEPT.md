# Live cutover ballot — EXECUTED ACCEPT (Soft-Frozen REBALANCE_L1_MIN=0.05)

Date: 2026-09-27  
Human ballot (exact intent): **`R_L1_05請上live`**  
Normalized: `ACCEPT Live cutover: Soft-Frozen REBALANCE_L1_MIN=0.05 (R_L1_05)`  
Status: **ACCEPTED · LIVE WIRED (forward-only)**

Prior paper: `FIN_RESIDUAL_RESEARCH_STAGEA` · verdict **`SIGNAL_HIT`** · challenger **`R_L1_05`**  
(only residual track clearing sealed FIN BUY fill + heldout NAV gates).

## Live recipe (forward-only) — replaces Soft-Frozen L1 only

| Layer | Value |
|---|---|
| Soft-Frozen clips | **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] KEEP** |
| Soft-Frozen `REBALANCE_L1_MIN` | **0.05** (was **0.02**) |
| FIN / TEL within-sleeve | **`KD_OPT` / live TEL T3 KEEP** |
| Offense Soft sell amp | **`SELL_a75` KEEP** |
| Sleeve / FUSE | **`FUSE_ADDITIVE` KEEP** |
| Risk overlay | **`COOL_c8_f50_d21` KEEP** |
| Exact T+1 | **KEEP** |

## Paper evidence (pre-cutover)

| Window | CAGR Δpp | MDD improve pp |
|---|---:|---:|
| full | +0.18 | +0.04 |
| heldout 2019+ | +0.28 | +0.04 |
| sealed 2023+ | +0.96 | +0.37 |
| validation 2019–22 | **−0.31** | +0.04 |

Sealed FIN BUY adj ±5d: 2.768% → **2.491%** (−0.28pp) · fills 6299 → 3688 (−41%).  
Yearly return shadows: **2019 (−0.48pp), 2020 (−1.23pp)** inside validation; MDD still flat/better those years.

## Implementation

- `scripts/e16_soft_frozen_base.py` — `REBALANCE_L1_MIN=0.05` (+ prior/asof/ballot constants)  
- `scripts/live_config.py` — `live_rebalance_l1_min=0.05` + ballot string  
- Sleeve tilt / FUSE / e21 features pick up via Soft-Frozen SSOT (no second L1 copy)  
- Tip history **KEEP** — forward-only · broker PREP-only  

## Rollback

```python
# e16_soft_frozen_base
REBALANCE_L1_MIN = 0.02  # restore prior
# live_config.LiveConfig
live_rebalance_l1_min: float = 0.02
```

## Non-actions

- Soft-Frozen clip flip · Exact T+1 change · tip rewrite  
- COOL / FUSE / KD / SELL_a75 retune  
- Broker `SendAlgo` / `broker_live_write_accepted`  
- Promote `R_L1_10` or WITHIN TOP2 from residual Stage A  

## Label

`LIVE_SOFT_FROZEN_REBALANCE_L1_05_CUTOVER_ACCEPTED_2026-09-27__FORWARD_ONLY`
