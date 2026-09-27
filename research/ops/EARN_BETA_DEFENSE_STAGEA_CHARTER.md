# Earn-beta / defense rhythm Stage A — 5 tracks (paper)

Date: 2026-09-27  
Status: **Stage A OPEN** · Soft-Frozen clips **KEEP** · Exact T+1 **KEEP** · live L1=0.05 **KEEP** · no live wire  
Parent: live underperforms TAIEX/0050 CAGR (esp. sealed) while winning MDD; residual L1 already LIVE  
Human: 還有什麼改善 → **都研究**

Label: `EARN_BETA_DEFENSE_STAGEA_CHARTER_2026-09-27__OPEN__NO_LIVE_WIRE`

## Context

Current live twin loses CAGR to TAIEX/0050 on held/sealed/full, but MDD much shallower.  
Prior grids exhausted for fill-quality levers (C_CLIP/D_COOL/B_KD NO_LIFT; `R_L1_05` LIVE).  
This Stage A asks whether **paper** earn-beta / defense-rhythm / FIN-dynamic / vol-target challengers lift CAGR vs **current live base** without blowing MDD.

## Question

On base `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8` + **`REBALANCE_L1_MIN=0.05`**:

1. **BETA** — Bull-only higher 0050 hi (paper) improve held/sealed CAGR?  
2. **COOL** — milder floor / earlier exit recover beta without MDD collapse?  
3. **FIN_DYN** — Bull-only lower FIN hi + higher ETF (regime shift inside/near box)?  
4. **VOL** — inverse-vol equity scale (stacked with COOL) lift CAGR?  
5. **CLOSE** — if 1–4 miss CAGR gate → `CLOSE_OBSERVE_RECOMMENDED`?

## Non-actions

- Exact T+1 change · tip rewrite · live clip flip · live L1 retune  
- Turn COOL fully off as promote path · broker · batch live wire  

## Base

| ID | Construction |
|---|---|
| `BASE_LIVE_L1_05` | Soft-Frozen live clips + L1=0.05 + SELL_a75 + Sleeve α=0.225 + KD_OPT + COOL_c8 |

## Stage A grid (finite)

| Track | ID | Spec |
|---|---|---|
| BETA | `B_BULL_E055` | Bull-only ETF hi **0.55** (else live clips) |
| BETA | `B_BULL_E060` | Bull-only ETF hi **0.60** |
| COOL | `C_FLOOR_070` | COOL floor **0.70** (live 0.50) |
| COOL | `C_EXIT_04` | COOL exit_x **0.04** (live 0.06) — earlier recover |
| FIN_DYN | `F_BULL_F070_E050` | Bull FIN hi **0.70** / ETF **0.50** |
| FIN_DYN | `F_BULL_F065_E055` | Bull FIN hi **0.65** / ETF **0.55** |
| VOL | `V_TVOL_12` | equity scale `clip(0.12/rv20, 0.50, 1.0)` × COOL |
| VOL | `V_TVOL_15` | target vol **0.15** same clip |
| CLOSE | *(meta)* | no CAGR gate hit → close observe |

## Gates (observe)

| Gate | Pass |
|---|---|
| CAGR | heldout CAGR lift ≥ **+0.50pp** vs base |
| MDD near-flat | heldout MDD improve ≥ **−0.50pp** |
| Report-only | sealed CAGR / vs-TAIEX Δ (not gate) |

## Verdicts

| Verdict | Meaning |
|---|---|
| `EARN_HIT` | ≥1 clears CAGR + MDD |
| `CAGR_SOFT` | CAGR gate OK; MDD outside |
| `MDD_ONLY` | MDD ok; CAGR miss |
| `NO_LIFT` | neither |
| `CLOSE_OBSERVE_RECOMMENDED` | 1–4 all miss CAGR gate |

Even HIT → paper only; pick **at most one** track for ACCEPT discussion.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/earn_beta_defense_stagea.py
```

Artifacts: `research/ops/EARN_BETA_DEFENSE_STAGEA_*` · `repro/earn-beta-defense-stagea/`
