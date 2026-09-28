# FIN sell BREAK5 diagnostic monitor/log Stage A — Paper Charter

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · **`fin_sell_ok` OFF** · no live wire  
Parent: `FIN_SELL_DIAG_ROLE_STAGEA` · top SIGNAL **`A_BREAK5`** (WR↑ +3.82pp · n=98 · cov≈10.6%)  
Track: **C** (`ABC_STAGEA_NEXT_BATCH_2026-09-28`)  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Prior: sell-quality `MDD_BLOCK`/`NO_EDGE` · sell new-mech `MDD_BLOCK` (hard gates starve exits)  
Human intent (normalized):

```
OPEN Stage A: FIN sell BREAK5 diagnostic monitor/log · no fin_sell_ok · paper only
```

Motivation: Parent diag-role Stage A found **`A_BREAK5`** (close &lt; prior 5d low) as DIAG_SIGNAL on live `SELL_a75` fills. This pack **does not gate** — it opens a paper **monitor/log** that labels each FIN SELL with `break5`, reports conditional WR H=21 vs unconditional, and emits a sell-level CSV. Still **no** `fin_sell_ok`, **no** observe/live from this pack.

Label: `FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_CHARTER_2026-09-28__OPEN__NO_GATE__NO_LIVE`

## Role (binding)

| Item | Rule |
|---|---|
| Simulation | **One** `CTRL_BASE` book only (same as diag-role Stage A) |
| `fin_sell_ok` | **Never passed** to `simulate_core` |
| NAV / fills | Identical to live Soft+FUSE+SELL_a75+COOL path |
| Attribute | **`A_BREAK5`** only via `breakdown_ok(raw_close, raw_low, 5)` |
| Output | Monitor CSV of sells + conditional WR vs unconditional |
| Observe / live | **Not authorized** by MONITOR_* alone |
| Hard-gate reopen | **Forbidden** from this charter |

## KEEP / REJECT

| Item | Status |
|---|---|
| Soft-Frozen + Exact T+1 + COOL + SELL_a75 | **KEEP** |
| Sell loss-defer | **REJECTED** |
| Prior hard-gate densify | **STOP** (do not reopen here) |

## Question

On live FIN SELL fills (fwd H=21, win = price down), does **`A_BREAK5`** show:

1. **MONITOR_READY**: WR↑ ≥ **+3.0pp** vs unconditional · n ≥ **80** · coverage ∈ **[5%, 70%]**  
2. else **MONITOR_WEAK**: WR↑ ≥ **+1.5pp** · n ≥ **50** · same coverage  
3. else **DRIFT** (lift &lt; 0 or coverage out of band) / **NO_SIGNAL**

## Monitor CSV

Path (on run): `repro/fin-sell-diag-break5-monitor-stagea/outputs/sell_break5_monitor.csv`  
Columns: `date, code, break5, fwd_ret_21, win`

## Non-actions

- Apply / densify `fin_sell_ok`  
- Soft-dampen sell scores from this pack  
- Open paper observe or live from MONITOR_*  
- Soft-Frozen / tip / FIFO rewrite  

## Follow-up if READY

Allowed: continue paper monitor/log on live sells (still no gate).  
Any gate/soft-tilt needs a **new** charter + human OPEN.

## Run

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_diag_break5_monitor_stagea.py
```

Artifacts: `research/ops/FIN_SELL_DIAG_BREAK5_MONITOR_STAGEA_*` · `repro/fin-sell-diag-break5-monitor-stagea/`
