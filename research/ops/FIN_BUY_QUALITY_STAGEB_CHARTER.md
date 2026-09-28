# FIN buy-quality Stage B — MA120 seed micro-tune (paper)

Date: 2026-09-28  
Status: **Stage B DONE — `BUY_QUALITY_HIT`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · no live wire  
Parent Stage A: **`WIN_SOFT`** · seed `Q_BELOW_MA120` (CAGR↑+1.63 · MDD↑+0.89 · tip OK · buy WR↓)  
Human intent (normalized):

```
OPEN Stage B: FIN buy-quality · seed Q_BELOW_MA120 finite micro-tune · or accept WIN_SOFT → observe
```

Label: `FIN_BUY_QUALITY_STAGEB_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why Stage B

Stage A showed a tension: filters that lift buy win-rate hurt tip/MDD; `Q_BELOW_MA120` clears **CAGR+MDD+tip** but not the +2pp win-rate gate → `WIN_SOFT`.  
Stage B does **one** residual job: finite micro-tunes around the MA120 seed, then either:

1. find a joint HIT (economic + milder win-rate), or  
2. **explicitly accept** WIN_SOFT → **paper observe recommended** on the seed (or a better economic micro-tune).

## Question

On `BASE_LIVE_FUSE_COOL`, does any MA120-neighborhood overlay clear:

| Gate | Stage B HIT | Observe-eligible |
|---|---|---|
| held CAGR↑ | ≥ **+0.15pp** | ≥ **+0.15pp** |
| held MDD↑ | ≥ **−0.25pp** · \|MDD\|≤15% | same |
| tip MDD↑ | ≥ **0** (YTD & 1y) | same |
| buy WR↑ (H=21) | ≥ **+1.0pp** | ≥ **−1.0pp** (near-flat OK) |

## Non-actions

- Soft-Frozen / Exact T+1 / tip rewrite · live wire · broker  
- Re-open sell loss-defer · broad new filter families (RSI-only, ret-only) already Stage A rejected for joint goals  
- Auto-promote observe without human OPEN ballot

## Base / seed

| ID | Role |
|---|---|
| `CTRL_BASE` | Live twin control |
| `SEED_MA120` | Stage A `Q_BELOW_MA120` (parent) |

## Stage B grid (finite)

| ID | Spec |
|---|---|
| `B_MA90` | below MA**90** (tighter) |
| `B_MA100` | below MA**100** |
| `B_MA150` | below MA**150** (looser) |
| `B_MA180` | below MA**180** |
| `B_MA120_KD_ONLY` | MA120 filter **only in** KD season; else pass |
| `B_MA120_OFF_ONLY` | MA120 filter **only outside** KD season |
| `B_MA120_OR_K9` | below MA120 **OR** `K9_LT30` (softer) |
| `B_MA120_OR_RSI50` | below MA120 **OR** RSI14&lt;50 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `BUY_QUALITY_HIT` | ≥1 book clears HIT gates (incl. WR↑≥+1pp) |
| `OBSERVE_RECOMMENDED` | no HIT; ≥1 book (prefer seed) clears economic + WR≥−1pp → **accept WIN_SOFT → observe** |
| `MICRO_SOFT` | economic clear but WR &lt; −1pp |
| `PARENT_KEEP` | no micro-tune beats seed; seed still observe-eligible |
| `MDD_BLOCK` / `NO_LIFT` | fail |

Even HIT / OBSERVE → **ballot only**; no live wire from Stage B.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_stageb.py
```

Artifacts: `research/ops/FIN_BUY_QUALITY_STAGEB_*` · `repro/fin-buy-quality-stageb/`
