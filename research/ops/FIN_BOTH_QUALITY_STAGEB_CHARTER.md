# FIN both-quality Stage B — WR densify on joint seed (paper)

Date: 2026-09-28  
Status: **Stage B OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · no live wire  
Parent Stage A: **`WIN_SOFT`** · champion `BOTH_OR_K9_x_HARD120` (CAGR↑+1.07 · MDD↑+0.30 · tip OK · sell WR↓)  
Human intent (normalized):

```
OPEN Stage B: FIN both-quality · densify BOTH_OR_K9_x_HARD120 for WR HIT · KEEP SELL_a75 · paper only
```

Label: `FIN_BOTH_QUALITY_STAGEB_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why Stage B

Stage A showed joint offsetting **clears CAGR+MDD+tip**; failure mode is **sell WR↓** (≈−4.5pp on champion).  
Stage B residual job: finite micro-tunes around the seed to clear **WR either ≥ +0.5pp** without breaking economic gates — else accept WIN_SOFT → observe.

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen / Exact T+1 / COOL / **SELL_a75** | **KEEP** |
| Sell loss-defer | **REJECTED** |
| CAGR↑ | **chal − base** |
| Unbounded new families | **forbidden** |

## Gates

| Gate | HIT | Observe-eligible |
|---|---|---|
| held CAGR↑ (chal−base) | ≥ **+0.15pp** | same |
| held MDD↑ | ≥ **−0.25pp** · \|MDD\|≤15% | same |
| tip MDD↑ | ≥ **0** YTD & 1y | same |
| WR either (buy H=21↑ **or** sell fwd&lt;0↑) | ≥ **+0.5pp** | ≥ **−0.5pp** |

## Grid (finite)

| ID | Spec |
|---|---|
| `CTRL_BASE` | live twin |
| `SEED_OR_K9_x_HARD120` | Stage A champion |
| `SEED_MA120_x_HARD120` | Stage A alt economic |
| `B_OR_K9_x_HARD90/100/150` | sell NOT_BELOW_MA* window sweep |
| `B_OR_K9_x_HARD120_AND_RSI6` | sell hard MA120 **AND** `RSI6_GT80` |
| `B_OR_K9_x_HARD120_AND_RSI14` | sell MA120 **AND** `RSI14_GT70` |
| `B_OR_K9_x_HARD120_AND_K9` | sell MA120 **AND** `K9_GT70` |
| `B_OR_K9_x_HARD120_OR_RSI6` | sell MA120 **OR** `RSI6_GT80` |
| `B_HYBRID_C_x_HARD120` | buy hybrid C × sell HARD120 |
| `B_OR_K9_KD_x_HARD120` | buy OR_K9 **only in** KD season |
| `B_OR_K9_x_DAMP120_d25` | sell damp×0.25 when below MA120 |

## Verdicts

| Verdict | Meaning |
|---|---|
| `BOTH_QUALITY_HIT` | ≥1 micro-tune clears HIT (incl. WR) |
| `WIN_SOFT` / `OBSERVE_RECOMMENDED` | economic clear; WR short but ≥−0.5 → accept observe |
| `PARENT_KEEP` | no micro-tune beats seed; seed still observe-eligible |
| `MDD_BLOCK` / `NO_EDGE` | fail |

Even HIT → **ballot only**; no live wire.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_both_quality_stageb.py
```

Artifacts: `research/ops/FIN_BOTH_QUALITY_STAGEB_*` · `repro/fin-both-quality-stageb/`
