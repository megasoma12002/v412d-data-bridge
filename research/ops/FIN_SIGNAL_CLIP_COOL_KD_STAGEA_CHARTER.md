# FIN signal improve Stage A — C_CLIP / D_COOL / B_KD (paper)

Date: 2026-09-26  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · no live wire  
Parent: fill A–D deep dive + FIN tip/sealed `FIN_BOTH_WEAK`  
Human: 改善訊號本身可以研究 → **每個都研究**（三軌 paper，不 batch-retune live）

Label: `FIN_SIGNAL_CLIP_COOL_KD_STAGEA_CHARTER_2026-09-26__OPEN__NO_LIVE_WIRE`

## Context

Fill audits showed Exact T+1 drag is structural (do not change).  
`FIN_BOTH_WEAK`: tip + sealed FIN fill quality worse than TEL peers.  
Deep-dive observe priority by |Δ ±5d|: **C_CLIP > D_COOL > B_KD**.  
This Stage A asks whether **paper signal challengers** on each lever improve FIN fills / NAV without touching Exact T+1.

## Question

On live twin book `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8` (Exact T+1):

1. **C_CLIP** — does a paper Soft-Frozen FIN-hi challenger improve FIN fill quality vs base?  
2. **D_COOL** — does turning COOL off or mildening floor improve FIN fills without NAV collapse?  
3. **B_KD** — does relaxing pre-exdiv buy_ok or blocking off-season FIN buys improve FIN fills?

## Non-actions

- Exact T+1 change · tip rewrite · Soft-Frozen live clip flip  
- Live COOL / KD / FUSE retune · live wire · broker  
- Batch-promote all three tracks to live from one Stage A

## Base

| ID | Construction |
|---|---|
| `BASE_FUSE_COOL` | Soft-Frozen live clips + Soft SELL_a75 + Sleeve α=0.225 + KD_OPT + COOL_c8 |

## Stage A grid (finite)

| Track | Challenger | Spec |
|---|---|---|
| C_CLIP | `C_FIN_HI_075` | Paper FIN hi **0.75** (tighter); TEL/ETF live |
| C_CLIP | `C_FIN_HI_090` | Paper FIN hi **0.90** (prior looser); TEL/ETF live |
| D_COOL | `D_COOL_OFF` | Same offense; **no** e45/COOL exposure |
| D_COOL | `D_COOL_FLOOR_070` | COOL circuit floor **0.70** (milder than live 0.50) |
| B_KD | `B_KD_BUYOK_ALWAYS` | `fin_buy_ok` always True (drop pre-exdiv block) |
| B_KD | `B_KD_OFFSEASON_NO_BUY` | Block FIN buys outside KD season |

Clip challengers rebuild sleeve-tilt targets with challenger clip box (**does not edit** `e16_soft_frozen_base`).  
COOL/KD challengers rebuild COOL from each book's own offense NAV when defense is on.

## Gates (observe)

| Gate | Pass |
|---|---|
| Fill | sealed_2023+ FIN BUY adj ±5d mean improve ≥ **+0.25pp** vs base (distance ↓) |
| NAV near-flat | heldout MDD improve ≥ **−0.50pp** and CAGR giveback ≤ **0.50pp** |

## Verdicts

| Verdict | Meaning |
|---|---|
| `SIGNAL_HIT` | ≥1 challenger clears fill + NAV gates |
| `FILL_BETTER_NAV_COST` | ≥1 clears fill only; NAV outside band |
| `NAV_ONLY` | NAV improves; fill gate fails |
| `NO_LIFT` | no challenger clears fill gate |

Per-track labels: `C_*` / `D_*` / `B_*` HIT or NO_LIFT.  
Even HIT → **paper observe only**; no live wire; human picks **at most one** track for follow-up ACCEPT discussion.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_signal_clip_cool_kd_stagea.py
```

Artifacts: `research/ops/FIN_SIGNAL_CLIP_COOL_KD_STAGEA_*` · `repro/fin-signal-clip-cool-kd-stagea/`
