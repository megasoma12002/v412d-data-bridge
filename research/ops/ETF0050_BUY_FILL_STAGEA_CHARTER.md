# 0050 BUY fill Stage A — adj metric + slew sensitivity (paper)

Date: 2026-09-26  
Status: **Stage A OPEN** · Soft-Frozen live **KEEP** · no live wire / no tip rewrite  
Parent: fill extreme audit + A–D deep dive (`LIVE_FILL_MECH_DEEPDIVE_*`)  
Human: 0050 BUY 最差有優化空間 → 開 Stage A（先修度量 + 分批敏感度）

Label: `ETF0050_BUY_FILL_STAGEA_CHARTER_2026-09-26__OPEN__NO_LIVE_WIRE`

## Context

Deep-dive reported 0050 BUY ±5d mean **6.06%** (vs FIN BUY ~2.4%).  
Root check: **2025-06-18 ~4:1 split** — raw OHLC ±5d windows mix pre/post prices → fake ~290% distances.  
Median was already ~2.85%; robust mean ~3.20%. Residual gap vs FIN BUY ~**+0.8pp**.

## Question

On live twin `FUSE_ADDITIVE + SELL_a75 + COOL_c8`:

1. **Metric fix** — does split-adjusted OHLC remove the 0050 BUY mean artifact?  
2. **Strata** — after adj, how do 0050 BUY vs SELL look by window / COOL / T+1 / size?  
3. **Slew** — does capping daily **0050 weight increases** (batch-in) improve adj ±5d on 0050 BUY without material held NAV damage?

## Non-actions

- Soft-Frozen clip flip · Exact T+1 change · tip rewrite  
- COOL retune · live wire · broker  

## Base

| ID | Construction |
|---|---|
| `BASE_FUSE_COOL` | Soft-Frozen + Soft SELL_a75 + Sleeve α=0.225 + COOL_c8 |

## Stage A grid (finite)

| Track | Spec |
|---|---|
| `METRIC_RAW_VS_ADJ` | Same base fills; raw vs adj_close-scaled OHLC extremes |
| `STRATA_0050` | BUY/SELL × window × COOL × T+1 bucket × qty tercile (adj) |
| `SLEW_UP_ABS` | Cap daily 0050 **up** Δ ∈ `{0.005, 0.010, 0.020}`; residual → FIN+TEL pro-rata |
| `SLEW_UP_FRAC` | Catch fraction of intended up-gap ∈ `{0.25, 0.50}` per day |

## Gates (observe)

| Gate | Pass |
|---|---|
| Fill | 0050 BUY adj ±5d mean improve ≥ **+0.25pp** vs base |
| NAV near-flat | heldout MDD improve ≥ **−0.50pp** and CAGR giveback ≤ **0.50pp** |

## Verdicts

| Verdict | Meaning |
|---|---|
| `ETF_BUY_SLEW_HIT` | ≥1 slew clears fill + NAV gates |
| `FILL_BETTER_NAV_COST` | fill gate OK; NAV cost above band |
| `METRIC_ARTIFACT_ONLY` | adj fix explains the 6% scare; no slew clears fill gate |
| `NO_LIFT` | neither metric story nor slew helps residual gap |

Even HIT → **paper observe only**; no live wire from Stage A.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/etf0050_buy_fill_stagea.py
```

Artifacts: `research/ops/ETF0050_BUY_FILL_STAGEA_*` · `repro/etf0050-buy-fill-stagea/`
