# FIN both-quality Stage A — joint buy×sell (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `WIN_SOFT`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · `SELL_a75` **KEEP** · no live wire  
Parents:
- Buy-quality A→D / observe OPEN (CAGR sign later corrected = chal−base; buy filters MDD↑ / CAGR↓)
- Sell-quality A `MDD_BLOCK` · B `NO_EDGE` (hard sell CAGR↑ / MDD↓; soft-dampen MDD≈flat / CAGR≈0)

Human intent (normalized):

```
OPEN Stage A: FIN 買賣側聯優 · 有限 buy×sell grid · MDD持平/改善 + CAGR↑ · 勝率兼顧更好 · KEEP SELL_a75 · paper only
```

Label: `FIN_BOTH_QUALITY_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why joint

Single-side densify exhausted the free lunch:
- Buy hard `buy_ok` → MDD↑ but **CAGR↓**
- Sell hard `sell_ok` → CAGR↑ but **MDD↓**
- Sell soft-dampen → MDD ok but **no CAGR**

Belief: **offsetting** buy MDD help × sell CAGR help may clear **both** gates where neither side alone did.  
Risk: interactions cancel both edges, or worsen tip.

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen / Exact T+1 / COOL / live **SELL_a75** | **KEEP** |
| Sell loss-defer / 等回本 | **REJECTED** |
| CAGR↑ definition | **chal − base** (not base−chal) |
| Unbounded combo densify | **forbidden** this Stage |

## Gates (HIT)

1. held **CAGR↑** ≥ **+0.15pp** (**chal − base**)  
2. held MDD↑ ≥ **−0.25pp** · \|MDD\| ≤ **15%**  
3. tip YTD & 1y MDD↑ ≥ **0**  
4. Diagnostics (HIT bar, either side): FIN BUY WR↑ H=21 ≥ **+0.5pp** **or** FIN SELL WR↑ (fwd&lt;0) ≥ **+0.5pp**

Soft path `WIN_SOFT`: economic (1–3) clear; WR short.

## Grid (finite ≤14)

| ID | Buy overlay | Sell overlay |
|---|---|---|
| `CTRL_BASE` | none | SELL_a75 scores only |
| `BUY_MA120` | hard AND `BELOW_MA120` | — |
| `BUY_OR_K9` | hard AND (`BELOW_MA120`∨`K9_LT30`) | — |
| `SELL_HARD_MA60` | — | hard `NOT_BELOW_MA60` |
| `SELL_HARD_MA120` | — | hard `NOT_BELOW_MA120` |
| `SELL_DAMP_MA60_d50` | — | damp×0.50 when below MA60 |
| `BOTH_MA120_x_HARD60` | `BELOW_MA120` | hard `NOT_BELOW_MA60` |
| `BOTH_MA120_x_HARD120` | `BELOW_MA120` | hard `NOT_BELOW_MA120` |
| `BOTH_OR_K9_x_HARD60` | MA120∨K9 | hard `NOT_BELOW_MA60` |
| `BOTH_OR_K9_x_HARD120` | MA120∨K9 | hard `NOT_BELOW_MA120` |
| `BOTH_MA120_x_DAMP60` | `BELOW_MA120` | damp MA60 d50 |
| `BOTH_OR_K9_x_DAMP60` | MA120∨K9 | damp MA60 d50 |
| `BOTH_MA120_x_DAMP120` | `BELOW_MA120` | damp MA120 d50 |
| `BOTH_HYBRID_C_x_HARD60` | MA120∨(K9∧MA60) | hard `NOT_BELOW_MA60` |

## Verdicts

| Verdict | Meaning |
|---|---|
| `BOTH_QUALITY_HIT` | ≥1 **BOTH_*** book clears HIT |
| `WIN_SOFT` | ≥1 BOTH clears economic; WR short |
| `SINGLE_SIDE_ONLY` | only BUY_* or SELL_* clears economic; joint fails |
| `MDD_BLOCK` / `NO_EDGE` | fail |

Even HIT → **ballot only**; no live wire from Stage A.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_both_quality_stagea.py
```

Artifacts: `research/ops/FIN_BOTH_QUALITY_STAGEA_*` · `repro/fin-both-quality-stagea/`
