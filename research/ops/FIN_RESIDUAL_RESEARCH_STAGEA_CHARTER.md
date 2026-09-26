# FIN residual research Stage A — 5 tracks (paper)

Date: 2026-09-26  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · no live wire  
Parent: FIN tip/sealed `FIN_BOTH_WEAK` + signal Stage A `NAV_ONLY` (C/D/B no fill lift)  
Human: 還有什麼可以研究 → **每條都研究**

Label: `FIN_RESIDUAL_RESEARCH_STAGEA_CHARTER_2026-09-26__OPEN__NO_LIVE_WIRE`

## Context

Signal levers C_CLIP / D_COOL / B_KD cleared **no fill gate**. Exact T+1 stays KEEP.  
Residual menu (prior discussion):

1. Other sleeve signals (TEL / sleeve-tilt)  
2. Execution layer **without** changing T+1 day (slip / cost model)  
3. FIN within-sleeve name allocation  
4. Rebalance rhythm (L1 threshold)  
5. Close observe (accept structural gap; monitor tip only)

## Question

On `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8` (Exact T+1):

1. **SLEEVE** — does killing sleeve RSI tilt or switching TEL within-sleeve policy improve FIN BUY fill quality?  
2. **EXEC** — does zero / 2× cost_multiple (slip+fees scale) move sealed FIN BUY ±5d enough to clear the fill gate?  
3. **WITHIN** — does `FIN_EQUAL` or `FIN_TOP2_EQUAL` beat live `FIN_PRE_EXDIV_KD` on fill?  
4. **REBAL** — does raising Soft-Frozen L1 rebalance threshold (fewer trades) improve fill distance?  
5. **CLOSE** — if 1–4 all miss the fill gate, recommend **close observe** (no further Stage A from this menu)?

## Non-actions

- Exact T+1 calendar change · tip rewrite · Soft-Frozen live clip flip  
- Live wire · broker · batch-promote all tracks  

## Base

| ID | Construction |
|---|---|
| `BASE_FUSE_COOL` | Soft-Frozen live + SELL_a75 + Sleeve α=0.225 + KD_OPT + COOL_c8 · Exact T+1 open |

## Stage A grid (finite)

| Track | ID | Spec |
|---|---|---|
| SLEEVE | `S_ALPHA_0` | Sleeve RSI tilt **α=0** (router score only) |
| SLEEVE | `S_TEL_PRE_EXDIV_KD` | `telecom_alloc=TEL_PRE_EXDIV_KD` (live TEL_EQUAL → KD) |
| EXEC | `E_COST_0` | `cost_multiple=0` (no slip/fees) |
| EXEC | `E_COST_2` | `cost_multiple=2` |
| WITHIN | `W_FIN_EQUAL` | `financial_alloc=FIN_EQUAL` |
| WITHIN | `W_FIN_TOP2_EQUAL` | `financial_alloc=FIN_TOP2_EQUAL` |
| REBAL | `R_L1_05` | Paper rebuild targets with `REBALANCE_L1_MIN=0.05` |
| REBAL | `R_L1_10` | Paper rebuild with `REBALANCE_L1_MIN=0.10` |
| CLOSE | *(meta)* | If no fill-gate hit across 1–4 → `CLOSE_OBSERVE_RECOMMENDED` |

## Gates (observe)

| Gate | Pass |
|---|---|
| Fill | sealed_2023+ FIN BUY adj ±5d improve ≥ **+0.25pp** vs base |
| NAV near-flat | heldout MDD improve ≥ **−0.50pp** and CAGR giveback ≤ **0.50pp** |

## Verdicts

| Verdict | Meaning |
|---|---|
| `SIGNAL_HIT` | ≥1 challenger clears fill + NAV |
| `FILL_BETTER_NAV_COST` | fill gate only |
| `NAV_ONLY` | NAV ok; no fill gate |
| `NO_LIFT` | no fill gate; NAV also not the story |
| `CLOSE_OBSERVE_RECOMMENDED` | 1–4 all miss fill gate → stop this residual menu; tip monitor only |

Even HIT → paper observe only; pick **at most one** track for follow-up.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_residual_research_stagea.py
```

Artifacts: `research/ops/FIN_RESIDUAL_RESEARCH_STAGEA_*` · `repro/fin-residual-research-stagea/`
