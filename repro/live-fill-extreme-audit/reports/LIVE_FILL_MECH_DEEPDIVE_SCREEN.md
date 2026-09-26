# Fill mechanism deep dive (A–D) — Screen

Generated: `2026-09-26T14:32:42Z`
Status: **`FILL_MECH_DEEPDIVE_DONE`** · Soft-Frozen KEEP · **no live wire** · `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

Tip fills **96** · Backtest twin fills **6299** (`2012-12-05` → `2026-09-07`)

## Findings (backtest-primary)

### A_T1_STRUCTURAL — Exact T+1 is the structural fill-cost driver across full history

```
{
  "mean_t1": 0.761,
  "mean_n5": 2.6809,
  "corr_t1_n5": 0.0724,
  "tip_mean_t1": 1.1543,
  "tip_mean_n5": 3.7887
}
```

### B_KD_OFFSEASON — FIN KD off-season fill quality vs in-season

```
{
  "in_n5": 2.6985,
  "off_n5": 2.4943,
  "delta_n5": -0.2042,
  "delta_t1": -0.057,
  "in_n": 261,
  "off_n": 2805
}
```

### C_CLIP_FIN_HI — FIN CLIP_FIN_HI edge fills vs non-edge

```
{
  "clip_n5": 1.5681,
  "not_n5": 2.5344,
  "delta_n5": -0.9663,
  "delta_t1": -0.3441,
  "clip_n": 72,
  "fin_share_ge_080": 0.0235
}
```

### D_COOL_DEFEND — COOL defend days: fill distance bump vs NAV MDD benefit

```
{
  "delta_n5": 0.5829,
  "delta_t1": 0.1534,
  "cool_on_n": 1454,
  "heldout_mdd_improve_pp": 7.5284,
  "heldout_cagr_giveback_pp": 0.7952,
  "sealed_mdd_improve_pp": 3.1973
}
```

Observe priority by |Δ ±5d mean| (B/C/D): **C_CLIP > D_COOL > B_KD**

## A — T+1 decomposition (backtest)

Overall mean T+1 **0.761%** · ±5d **2.6809%** · corr(T+1,±5d) **0.0724**

| sleeve | side | n | ±5 mean% | T+1 mean% | ±21 mean% |
|---|---|---:|---:|---:|---:|
| ALL | ALL | 6299 | 2.6809 | 0.761 | 5.4727 |
| ALL | BUY | 3235 | 2.7813 | 0.8218 | 5.9311 |
| ALL | SELL | 3064 | 2.5749 | 0.6968 | 4.9886 |
| FIN | ALL | 3066 | 2.5117 | 0.8293 | 5.2099 |
| FIN | BUY | 1663 | 2.3805 | 0.8715 | 5.289 |
| FIN | SELL | 1403 | 2.6672 | 0.7794 | 5.116 |
| TEL | ALL | 2425 | 2.1303 | 0.7102 | 4.2024 |
| TEL | BUY | 1166 | 2.2105 | 0.8082 | 4.3224 |
| TEL | SELL | 1259 | 2.056 | 0.6193 | 4.0914 |
| 0050 | ALL | 808 | 4.9758 | 0.6543 | 10.2822 |
| 0050 | BUY | 406 | 6.0627 | 0.6571 | 13.1814 |
| 0050 | SELL | 402 | 3.8781 | 0.6515 | 7.3541 |

### T+1 buckets (backtest ALL)

| bucket | n | share | mean ±5% |
|---|---:|---:|---:|
| <=0.5 | 2671 | 0.424 | 2.0444 |
| 0.5-1 | 1904 | 0.3023 | 2.2335 |
| 1-2 | 1253 | 0.1989 | 3.8567 |
| >2 | 471 | 0.0748 | 4.9719 |

### Windows (backtest)

| window | n | ±5 mean% | T+1 mean% |
|---|---:|---:|---:|
| `full` | 6299 | 2.6809 | 0.761 |
| `oof_2011_2018` | 2651 | 2.2555 | 0.7003 |
| `validation_2019_2022` | 1981 | 2.5394 | 0.8172 |
| `sealed_2023_plus` | 1667 | 3.5258 | 0.7907 |
| `heldout_2019_plus` | 3648 | 2.9901 | 0.8051 |

## B — KD season (FIN, backtest)

In-season n=261 ±5 **2.6985%** · Off-season n=2805 ±5 **2.4943%** · Δ(off−in) ±5 **-0.2042** · Δ T+1 **-0.057**

| window | in ±5 | off ±5 | Δ |
|---|---:|---:|---:|
| `full` | 2.6985 | 2.4943 | -0.2042 |
| `oof_2011_2018` | 2.0148 | 2.2321 | 0.2173 |
| `validation_2019_2022` | 3.5027 | 2.6006 | -0.9021 |
| `sealed_2023_plus` | 3.1498 | 2.7841 | -0.3657 |
| `heldout_2019_plus` | 3.3172 | 2.6833 | -0.6339 |

## C — CLIP_FIN_HI (FIN, backtest)

CLIP n=72 ±5 **1.5681%** · not CLIP n=2994 ±5 **2.5344%** · Δ(clip−not) ±5 **-0.9663** · Δ T+1 **-0.3441**
FIN weight share ≥0.80: **0.0235**

| cross | n | ±5 mean% | T+1 |
|---|---:|---:|---:|
| `clip_and_offseason` | 64 | 1.5816 | 0.5233 |
| `clip_and_inseason` | 8 | 1.4601 | 0.2531 |
| `notclip_offseason` | 2741 | 2.5156 | 0.8315 |
| `notclip_inseason` | 253 | 2.7376 | 0.9014 |

## D — COOL defend (backtest fills + NAV)

COOL on n=1454 ±5 **3.1293%** · off n=4845 ±5 **2.5464%** · Δ ±5 **0.5829** · Δ T+1 **0.1534**

| sleeve | on ±5 | off ±5 | Δ |
|---|---:|---:|---:|
| FIN | 3.3037 | 2.2747 | 1.029 |
| TEL | 2.4751 | 2.0265 | 0.4486 |
| 0050 | 4.4332 | 5.1392 | -0.706 |

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
