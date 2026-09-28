# FIN buy-quality Stage A — Paper Charter

Date: 2026-09-28  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · no live wire  
Parent live: Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
Human intent (normalized):

```
OPEN Stage A charter: FIN 買側品質過濾 · 勝率診斷 + MDD 維持/改善 + CAGR↑ · paper only
```

Motivation: tip 賣出 FIFO 虧單與浮虧引發「改善買賣勝率」需求；賣側「等回本」已否決（另軌）。本軌改測 **買側進場過濾**——少做差的 FIN BUY，是否能同時抬 held CAGR、護 MDD，並讓 FIN BUY 前瞻勝率上升。

Label: `FIN_BUY_QUALITY_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Philosophy

| Regime | Job |
|---|---|
| **Normal rebalance** | AND-filter `fin_buy_ok` with quality gates (MA / RSI / short ret / COOL=1) |
| **COOL defense** | Live COOL exposure KEEP; optional challenger blocks new FIN buys while cool&lt;1 |
| **Win rate** | Diagnostic on FIN BUY fills (fwd H=21 ret &gt; 0); **not** a live tip rewrite |

Belief to test: tighter FIN buy quality raises win-rate **and** clears CAGR+MDD tip-safe gates.  
Risk to reject: filters starve buys → CAGR↓, or cherry-pick winners while MDD/tip worsen.

## Question

On `BASE_LIVE_FUSE_COOL` (Exact T+1 · Soft-Frozen KEEP), does a finite AND overlay on FIN `buy_ok` produce ≥1 book with:

1. held CAGR↑ ≥ **+0.15pp**  
2. held MDD near-flat (↑ ≥ **−0.25pp**) and abs MDD ≤ **15%**  
3. tip YTD / 1y MDD improve ≥ **0**  
4. FIN BUY win-rate (H=21) improve ≥ **+2.0pp** vs control  

## Non-actions

- Soft-Frozen clip / Exact T+1 / tip rewrite  
- Sell loss-defer / FIFO accounting rewrite  
- Live wire / broker / COOL retune  
- Re-open KD_OPT live within-sleeve retune (pre-exdiv `buy_ok` base KEEP; overlay only)

## Base

| ID | Construction |
|---|---|
| `CTRL_BASE` | Soft-Frozen + FUSE Soft SELL_a75 + Sleeve α live + KD_OPT pre-exdiv `buy_ok` + COOL_c8 |

## Stage A grid (finite)

| ID | Spec |
|---|---|
| `CTRL_BASE` | Live `buy_ok` only |
| `Q_BELOW_MA60` | AND `close < MA60` |
| `Q_BELOW_MA120` | AND `close < MA120` |
| `Q_NOT_RSI14_GT70` | AND NOT `RSI14 > 70` |
| `Q_RSI14_LT50` | AND `RSI14 < 50` |
| `Q_ABOVE_MA60` | AND `close > MA60` (trend) |
| `Q_RET5_POS` | AND 5d ret &gt; 0 |
| `Q_RET10_POS` | AND 10d ret &gt; 0 |
| `Q_COOL1_ONLY` | AND cool exposure = 1 (no new FIN buy while defending) |
| `Q_RET5_NEG` | **Negative control:** AND 5d ret &lt; 0 |

## Gates

| Gate | Pass |
|---|---|
| CAGR | heldout CAGR↑ ≥ **+0.15pp** |
| MDD near-flat | heldout MDD↑ ≥ **−0.25pp** |
| MDD band | \|heldout MDD\| ≤ **0.15** |
| tip-safe | tip YTD & trailing-1y MDD↑ ≥ **0** |
| buy win-rate | FIN BUY H=21 win-rate↑ ≥ **+2.0pp** vs `CTRL_BASE` |

## Verdicts

| Verdict | Meaning |
|---|---|
| `BUY_QUALITY_HIT` | ≥1 challenger clears **all** gates (incl. win-rate) |
| `WIN_SOFT` | CAGR+MDD+tip clear; win-rate short |
| `CAGR_SOFT` | MDD+tip (+optional win) clear; CAGR short |
| `MDD_BLOCK` | tip or held MDD fails |
| `NO_LIFT` | no useful lift |

Even HIT → **paper observe ballot only**; separate ACCEPT for live.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_stagea.py
```

Artifacts: `research/ops/FIN_BUY_QUALITY_STAGEA_*` · `repro/fin-buy-quality-stagea/`
