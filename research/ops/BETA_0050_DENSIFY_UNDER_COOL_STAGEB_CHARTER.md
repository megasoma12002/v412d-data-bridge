# β / 0050 densify under COOL — Stage B (MDD flat + CAGR lift)

Date: 2026-09-25  
Status: **PAPER STAGE B OPEN** · parent Stage A **`BETA_0050_HIT`**  
Human ask: **MDD 持平 + CAGR 改善** (not CAGR-only HIT)

Label: `BETA_0050_DENSIFY_UNDER_COOL_STAGEB_CHARTER_2026-09-25__MDD_FLAT_CAGR__NO_LIVE_WIRE`

## Why

Stage A HIT `F[0.60,0.80] E[0,0.50]`: CAGR **+0.57pp**, held MDD↑ **−0.06pp** (slightly worse).  
Near-miss `F[0.60,0.85] E[0,0.45|0.50]`: held CAGR **+0.27pp** **and** MDD↑ **+0.37pp**, but **tip MDD fail** (−0.12pp YTD/1y).

Stage B searches the **FIN hi ∈ [0.80, 0.85]** neighborhood for joint:

1. held CAGR lift ≥ **+0.20 pp**  
2. held MDD↑ ≥ **0** (flat or better)  
3. tip YTD + 1y MDD↑ ≥ **0**  
4. held |MDD| ≤ **15%** (band keep)

## Non-actions

Same as Stage A: Soft-Frozen live KEEP · no 公+民 · no COOL retune · no live wire from Stage B.

## Finite grid (predeclared)

| Axis | Values |
|---|---|
| FIN | lo **0.60** · hi ∈ `{0.80, 0.82, 0.83, 0.84, 0.85}` |
| TEL | live `[0.03, 0.35]` frozen |
| ETF | lo **0.00** · hi ∈ `{0.40, 0.42, 0.45, 0.48, 0.50}` |
| Soft/Sleeve/COOL | frozen live twin |

Script: `scripts/beta_0050_densify_under_cool_stageb.py`  
Repro: `repro/beta-0050-densify-under-cool-stageb/`

## Verdicts

| Verdict | Meaning |
|---|---|
| `MDD_FLAT_CAGR_HIT` | ≥1 book clears all four gates |
| `HELD_FLAT_TIP_FAIL` | held MDD flat+CAGR OK; tip fails |
| `NO_FLAT_LIFT` | no book with MDD↑≥0 and CAGR≥+0.20 in band |

Even HIT → paper observe only.
