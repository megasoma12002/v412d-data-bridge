# Fill mechanism deep dive (A–D) — Screen

Generated: `2026-09-26T15:06:34Z`
Status: **`FILL_MECH_DEEPDIVE_DONE`** · Soft-Frozen KEEP · **no live wire** · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

Tip fills **96** · Backtest twin fills **6299** (`2012-12-05` → `2026-09-07`)

## Findings (backtest-primary)

### A_T1_STRUCTURAL — Exact T+1 is the structural fill-cost driver across full history

```
{
  "mean_t1": 0.789,
  "mean_n5": 2.44,
  "corr_t1_n5": 0.3455,
  "tip_mean_t1": 1.1543,
  "tip_mean_n5": 3.7887
}
```

### B_KD_OFFSEASON — FIN KD off-season fill quality vs in-season

```
{
  "in_n5": 2.6985,
  "off_n5": 2.4899,
  "delta_n5": -0.2086,
  "delta_t1": -0.0467,
  "in_n": 261,
  "off_n": 2805
}
```

### C_CLIP_FIN_HI — FIN CLIP_FIN_HI edge fills vs non-edge

```
{
  "clip_n5": 1.6304,
  "not_n5": 2.5287,
  "delta_n5": -0.8983,
  "delta_t1": -0.4228,
  "clip_n": 72,
  "fin_share_ge_080": 0.0235
}
```

### D_COOL_DEFEND — COOL defend days: fill distance bump vs NAV MDD benefit

```
{
  "delta_n5": 0.8323,
  "delta_t1": 0.0854,
  "cool_on_n": 1454,
  "heldout_mdd_improve_pp": 7.5284,
  "heldout_cagr_giveback_pp": 0.7952,
  "sealed_mdd_improve_pp": 3.1973
}
```

Observe priority by |Δ ±5d mean| (B/C/D): **C_CLIP > D_COOL > B_KD**

## A — T+1 decomposition (backtest)

Overall mean T+1 **0.789%** · ±5d **2.44%** · corr(T+1,±5d) **0.3455**

| sleeve | side | n | ±5 mean% | T+1 mean% | ±21 mean% |
|---|---|---:|---:|---:|---:|
| ALL | ALL | 6299 | 2.44 | 0.789 | 4.9849 |
| ALL | BUY | 3235 | 2.3986 | 0.8923 | 5.2159 |
| ALL | SELL | 3064 | 2.4837 | 0.68 | 4.7409 |
| FIN | ALL | 3066 | 2.5077 | 0.8388 | 5.2078 |
| FIN | BUY | 1663 | 2.4018 | 0.9058 | 5.3966 |
| FIN | SELL | 1403 | 2.6331 | 0.7594 | 4.984 |
| TEL | ALL | 2425 | 2.0434 | 0.7297 | 3.9648 |
| TEL | BUY | 1166 | 2.103 | 0.8668 | 4.0587 |
| TEL | SELL | 1259 | 1.9881 | 0.6027 | 3.8778 |
| 0050 | ALL | 808 | 3.3733 | 0.7781 | 7.2006 |
| 0050 | BUY | 406 | 3.234 | 0.9101 | 7.7994 |
| 0050 | SELL | 402 | 3.5141 | 0.6447 | 6.5958 |

### T+1 buckets (backtest ALL)

| bucket | n | share | mean ±5% |
|---|---:|---:|---:|
| <=0.5 | 2658 | 0.422 | 1.875 |
| 0.5-1 | 1906 | 0.3026 | 2.2104 |
| 1-2 | 1259 | 0.1999 | 3.0706 |
| >2 | 476 | 0.0756 | 4.846 |

### Windows (backtest)

| window | n | ±5 mean% | T+1 mean% |
|---|---:|---:|---:|
| `full` | 6299 | 2.44 | 0.789 |
| `oof_2011_2018` | 2651 | 2.2161 | 0.7319 |
| `validation_2019_2022` | 1981 | 2.5134 | 0.817 |
| `sealed_2023_plus` | 1667 | 2.7087 | 0.8466 |
| `heldout_2019_plus` | 3648 | 2.6026 | 0.8305 |

## B — KD season (FIN, backtest)

In-season n=261 ±5 **2.6985%** · Off-season n=2805 ±5 **2.4899%** · Δ(off−in) ±5 **-0.2086** · Δ T+1 **-0.0467**

| window | in ±5 | off ±5 | Δ |
|---|---:|---:|---:|
| `full` | 2.6985 | 2.4899 | -0.2086 |
| `oof_2011_2018` | 2.0148 | 2.2385 | 0.2237 |
| `validation_2019_2022` | 3.5027 | 2.6372 | -0.8655 |
| `sealed_2023_plus` | 3.1498 | 2.7125 | -0.4373 |
| `heldout_2019_plus` | 3.3172 | 2.6711 | -0.6461 |

## C — CLIP_FIN_HI (FIN, backtest)

CLIP n=72 ±5 **1.6304%** · not CLIP n=2994 ±5 **2.5287%** · Δ(clip−not) ±5 **-0.8983** · Δ T+1 **-0.4228**
FIN weight share ≥0.80: **0.0235**

| cross | n | ±5 mean% | T+1 |
|---|---:|---:|---:|
| `clip_and_offseason` | 64 | 1.6517 | 0.4475 |
| `clip_and_inseason` | 8 | 1.4601 | 0.2531 |
| `notclip_offseason` | 2741 | 2.5095 | 0.8439 |
| `notclip_inseason` | 253 | 2.7376 | 0.9014 |

## D — COOL defend (backtest fills + NAV)

COOL on n=1454 ±5 **3.0801%** · off n=4845 ±5 **2.2478%** · Δ ±5 **0.8323** · Δ T+1 **0.0854**

| sleeve | on ±5 | off ±5 | Δ |
|---|---:|---:|---:|
| FIN | 3.2426 | 2.2878 | 0.9548 |
| TEL | 2.4354 | 1.9254 | 0.51 |
| 0050 | 4.4006 | 3.064 | 1.3366 |

### Offense vs COOL stack NAV

| window | off CAGR | cool CAGR | giveback pp | off MDD | cool MDD | MDD improve pp |
|---|---:|---:|---:|---:|---:|---:|
| `full` | 0.130613 | 0.122945 | 0.7668 | -0.225438 | -0.150154 | 7.5284 |
| `oof_2011_2018` | 0.096235 | 0.08862 | 0.7615 | -0.161582 | -0.131794 | 2.9788 |
| `validation_2019_2022` | 0.124303 | 0.132036 | -0.7733 | -0.225438 | -0.150154 | 7.5284 |
| `sealed_2023_plus` | 0.203459 | 0.177853 | 2.5606 | -0.09663 | -0.064657 | 3.1973 |
| `heldout_2019_plus` | 0.161522 | 0.15357 | 0.7952 | -0.225438 | -0.150154 | 7.5284 |

## Tip mirror (short window)

Tip overall ±5 **3.7887%** · T+1 **1.1543%** · COOL-on fills **0** · FIN CLIP_FIN_HI n=24 · FIN KD off n=48

Repro:
```bash
PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py
PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py
PYTHONPATH=scripts python3 scripts/live_fill_mech_deepdive.py
```

Label: `LIVE_FILL_MECH_DEEPDIVE_SCREEN_2026-09-26__FILL_MECH_DEEPDIVE_DONE`
