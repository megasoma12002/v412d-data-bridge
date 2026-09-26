# 0050 BUY fill Stage A — Screen

Generated: `2026-09-26T14:47:54Z`
Status: **`METRIC_ARTIFACT_ONLY`** · Soft-Frozen KEEP · **no live wire** · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

## 1 — Metric fix (raw vs adj)

0050 BUY n=406 · SELL n=402
BUY ±5d raw mean **6.0627%** · adj mean **3.234%** · raw−adj **2.8287**
BUY ±5d adj median **2.9086%** · SELL adj mean **3.5141%**

_2025-06-18 ~4:1 split makes raw ±5d explode; adj_close-scaled OHLC is authoritative_

## 2 — Strata (adj ±5d)

### Windows BUY

| window | n | adj mean | adj med | raw mean | T+1 |
|---|---:|---:|---:|---:|---:|
| `full` | 406 | 3.234 | 2.9086 | 6.0627 | 0.9101 |
| `oof_2011_2018` | 172 | 2.6662 | 2.3906 | 2.6679 | 0.8995 |
| `validation_2019_2022` | 124 | 3.3716 | 3.0369 | 3.3526 | 0.6938 |
| `sealed_2023_plus` | 110 | 3.9665 | 3.78 | 14.4258 | 1.1706 |
| `heldout_2019_plus` | 234 | 3.6513 | 3.3436 | 8.558 | 0.918 |

### COOL × side

| slice | n | ±5 adj mean | T+1 |
|---|---:|---:|---:|
| `buy_on` | 12 | 4.6412 | 1.5142 |
| `buy_off` | 394 | 3.1911 | 0.8917 |
| `sell_on` | 175 | 4.3841 | 0.7299 |
| `sell_off` | 227 | 2.8433 | 0.5791 |

### T+1 buckets (BUY)

| bucket | n | ±5 adj mean |
|---|---:|---:|
| <=0.5 | 155 | 2.6994 |
| 0.5-1 | 112 | 3.0935 |
| 1-2 | 100 | 3.7875 |
| >2 | 39 | 4.3422 |

### Qty terciles (BUY)

| tercile | n | ±5 adj mean | T+1 |
|---|---:|---:|---:|
| `Q3_large` | 135 | 3.5292 | 1.1382 |
| `Q2_mid` | 135 | 2.8555 | 0.7956 |
| `Q1_small` | 136 | 3.3165 | 0.7975 |

## 3 — Slew sensitivity

Base 0050 BUY adj ±5d mean **3.234%** · fill gate improve ≥0.25pp · NAV: MDD≥-0.5pp & CAGR giveback≤0.5pp

| id | track | buy n | adj ±5 | improve pp | fill | held CAGR gb | held MDD↑ | nav | HIT |
|---|---|---:|---:|---:|---|---:|---:|---|---|
| `SLEW_UP_50bp` | SLEW_UP_ABS | 482 | 3.0739 | 0.1601 | n | -0.4485 | -0.012 | Y | n |
| `SLEW_UP_100bp` | SLEW_UP_ABS | 434 | 3.1337 | 0.1003 | n | -0.2427 | -0.0174 | Y | n |
| `SLEW_UP_200bp` | SLEW_UP_ABS | 406 | 3.2192 | 0.0148 | n | -0.0321 | -0.0056 | Y | n |
| `SLEW_FRAC_25` | SLEW_UP_FRAC | 466 | 3.0563 | 0.1777 | n | -0.5244 | -0.0638 | Y | n |
| `SLEW_FRAC_50` | SLEW_UP_FRAC | 433 | 3.0845 | 0.1495 | n | -0.2624 | -0.0192 | Y | n |

Hits: **0** · Verdict: **`METRIC_ARTIFACT_ONLY`**

Repro: `PYTHONPATH=scripts python3 scripts/etf0050_buy_fill_stagea.py`

Label: `ETF0050_BUY_FILL_STAGEA_SCREEN_2026-09-26__METRIC_ARTIFACT_ONLY`
