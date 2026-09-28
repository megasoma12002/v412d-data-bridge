# ETF 0050 soft-dampen × extreme/DD Stage A — paper

Date: 2026-09-28  
Status: **Stage A DONE — `TIP_BLOCK`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · β clip **KEEP** · no live wire  
Parent: `1d` both-quality Stage A **`TIP_BLOCK`** (hard Δw freeze lifts WR / occasional CAGR but tip MDD fails)  
Seeds to soft-scale: `SELL_COOL_DEFEND` (held CAGR↑+0.16 tip↓) · `BUY_RET5_POS` (CAGR↑+0.14 tip↓)

Human intent (normalized):

```
OPEN Stage A: 0050 Δw 軟縮放（seed SELL_COOL_DEFEND / BUY_RET5_POS）或 0050 自身高低點／DD 閘 · tip-safe + CAGR↑ · paper only
```

Label: `ETF0050_SOFT_EXTREME_STAGEA_CHARTER_2026-09-28__DONE_TIP_BLOCK__NO_LIVE_WIRE`

## Why

Hard quality freeze (`1d`) moved WR and near-cleared CAGR but **tip MDD blocked**. Two new mechanisms (not densify / slew / same hard MA grid):

| Track | Idea |
|---|---|
| **SOFT** | When quality fails, take only `damp∈{0.25,0.50}` of intended 0050 Δw (residual → FIN+TEL) |
| **EXT** | Gate adds near 0050 local lows / deep own-DD; gate cuts near local highs |

Belief: soft scale protects tip vs hard freeze; extreme/DD is closer to buy-low/sell-high than MA/RET alone.  
Risk: soft under-trades β sleeve → no CAGR; extreme starves adds → CAGR↓ / tip fail.

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen β clip `E[0,0.50]` · Exact T+1 · COOL · SELL_a75 | **KEEP** |
| Hard Δw freeze grid (`1d`) | **CLOSED** — do not reopen identical hard books |
| Densify / asymm densify / BUY slew / ex-calendar | **CLOSED** |
| Live wire | **forbidden** this Stage |

## Mechanism

On `BASE_LIVE_FUSE_COOL` targets, for each day Δ = intended 0050 − prior applied:

**SOFT:** if Δ&gt;0 and not `buy_ok` → apply `damp·Δ`; if Δ&lt;0 and not `sell_ok` → apply `damp·Δ`; else full Δ. Redistribute residual to FIN+TEL pro-rata ∩ Soft-Frozen box.

**EXT:** hard allow/deny like `1d`, but gates from **0050 own** N-day low/high / peak DD (not MA60/120 RET5 seeds except SOFT track).

## Gates (HIT)

1. held CAGR↑ ≥ **+0.15pp** (**chal − base**)  
2. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. tip YTD & 1y MDD↑ ≥ **0**  
4. Diagnostic: 0050 BUY WR↑ H=21 ≥ **+0.5pp** **or** SELL WR↑ ≥ **+0.5pp**

## Grid (finite ≤14 — do not expand after peek)

| ID | Track | Spec |
|---|---|---|
| `CTRL_BASE` | ctrl | live twin |
| `SOFT_BUY_RET5_d50` | soft | buy_ok=RET5&gt;0 · damp=0.50 when false |
| `SOFT_BUY_RET5_d25` | soft | buy_ok=RET5&gt;0 · damp=0.25 |
| `SOFT_SELL_COOL_d50` | soft | sell_ok=COOL defend · damp=0.50 |
| `SOFT_SELL_COOL_d25` | soft | sell_ok=COOL defend · damp=0.25 |
| `SOFT_BOTH_RET5_x_COOL_d50` | soft | both seeds · damp=0.50 |
| `SOFT_BOTH_RET5_x_COOL_d25` | soft | both seeds · damp=0.25 |
| `EXT_BUY_LOW20` | ext | add only within 2% of 20d low |
| `EXT_BUY_DD8` | ext | add only when own DD63 ≤ −8% |
| `EXT_BUY_DD12` | ext | add only when own DD63 ≤ −12% |
| `EXT_SELL_HIGH20` | ext | cut only within 2% of 20d high |
| `EXT_SELL_HIGH60` | ext | cut only within 2% of 60d high |
| `EXT_BOTH_LOW20_x_HIGH20` | ext | LOW20 × HIGH20 |
| `EXT_BOTH_DD8_x_HIGH20` | ext | DD8 × HIGH20 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `SOFT_EXTREME_HIT` | ≥1 SOFT_* or EXT_* clears all HIT gates |
| `WIN_SOFT` | economic clear; WR short |
| `CAGR_SOFT` | MDD+tip clear; CAGR short |
| `TIP_BLOCK` | CAGR clears somewhere; tip fails (repeat of `1d` pattern) |
| `MDD_BLOCK` / `NO_EDGE` | structural / no lift |

Even HIT → **paper observe ballot only**.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/etf0050_soft_extreme_stagea.py
```

Artifacts: `research/ops/ETF0050_SOFT_EXTREME_STAGEA_*` · `repro/etf0050-soft-extreme-stagea/`
