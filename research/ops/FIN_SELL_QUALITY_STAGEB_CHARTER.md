# FIN sell-quality Stage B — soft-dampen + relaxed MDD (paper)

Date: 2026-09-28  
Status: **Stage B DONE — `NO_EDGE`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · no live wire  
Parent Stage A: **`MDD_BLOCK`** · hard `fin_sell_ok` lifts CAGR/WR but worsens MDD (≥−1.46pp nearest)  
Human intent (normalized):

```
OPEN Stage B: FIN sell-quality · soft-dampen (not hard gate) · optional MDD soft floor −1.0pp · KEEP SELL_a75 · paper only
```

Label: `FIN_SELL_QUALITY_STAGEB_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why Stage B

Stage A hard AND `fin_sell_ok` **starves sells** → hold losers → MDD↓.  
Best CAGR seeds: `S_NOT_BELOW_MA60` (+1.81) · `S_ABOVE_MA60` (+1.77) · `S_NOT_BELOW_MA120` (+1.15).  

Stage B residual job (finite):

1. Replace hard block with **soft-dampen** / **boost-only-when-quality** on live `SELL_a75` scores  
2. Report both **strict MDD** (−0.25pp) and **relaxed MDD soft** (−1.0pp) for observe candidacy  
3. HIT only on strict gates; `MDD_SOFT` / observe ballot only if human accepts soft floor

## KEEP / forbidden

| Item | Status |
|---|---|
| Live `SELL_a75` amplitude 0.75 on `RSI6_GT80` | **KEEP** as base score construction |
| Soft-Frozen / Exact T+1 / COOL | **KEEP** |
| Sell loss-defer / 等回本 | **REJECTED** |
| CAGR sign | **chal − base** |

## Gates

| Gate | HIT (strict) | MDD_SOFT / observe-eligible |
|---|---|---|
| held CAGR↑ (chal−base) | ≥ **+0.15pp** | ≥ **+0.15pp** |
| held MDD↑ | ≥ **−0.25pp** · \|MDD\|≤15% | ≥ **−1.0pp** · \|MDD\|≤15% |
| tip MDD↑ | ≥ **0** YTD & 1y | same |
| sell WR↑ (H=21, fwd&lt;0) | ≥ **+1.0pp** | ≥ **−0.5pp** |

## Grid (finite)

| ID | Spec |
|---|---|
| `CTRL_BASE` | live SELL_a75 scores · no overlay |
| `SEED_HARD_MA120` | Stage A hard `NOT_BELOW_MA120` (reference) |
| `SEED_HARD_MA60` | Stage A hard `NOT_BELOW_MA60` (reference) |
| `B_DAMP_MA120_d25/50/75` | when `BELOW_MA120`, multiply sell scores by 0.25/0.50/0.75 |
| `B_DAMP_MA60_d25/50/75` | when `BELOW_MA60`, multiply sell scores by damp |
| `B_DAMP_NOTABOVE60_d25/50` | when NOT `ABOVE_MA60`, multiply sell by damp |
| `B_BOOST_ONLY_MA120` | `1 + 0.75·RSI6_GT80` **only if** NOT `BELOW_MA120`; else `1.0` |
| `B_BOOST_ONLY_MA60` | boost only if NOT `BELOW_MA60` |
| `B_BOOST_ONLY_ABOVE60` | boost only if `ABOVE_MA60` |

No `fin_sell_ok` hard gate on soft books (scores only).

## Verdicts

| Verdict | Meaning |
|---|---|
| `SELL_QUALITY_HIT` | ≥1 soft book clears **strict** HIT gates |
| `WIN_SOFT` | strict CAGR+MDD+tip; WR short |
| `MDD_SOFT` | no strict economic; ≥1 soft book clears **relaxed MDD** + CAGR+tip |
| `PARENT_HARD_ONLY` | only hard seeds look good (mechanism fail) |
| `MDD_BLOCK` / `NO_EDGE` | fail |

Even HIT / MDD_SOFT → **ballot only**; no live wire from Stage B.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_quality_stageb.py
```

Artifacts: `research/ops/FIN_SELL_QUALITY_STAGEB_*` · `repro/fin-sell-quality-stageb/`
