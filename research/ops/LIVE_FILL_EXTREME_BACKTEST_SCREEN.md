# Backtest fill extreme + mechanism audit — Screen

Generated: `2026-09-26T15:06:25Z`
Status: **`FILL_EXTREME_BACKTEST_DONE`** · Soft-Frozen KEEP · **no live wire** · book `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

Fills: **6299** (BUY 3235 / SELL 3064) · `2012-12-05` → `2026-09-07` · codes `['0050', '2412', '2880', '2886', '2892', '3045', '4904', '5880']`
COOL defense day-frac: **16.02%**

## A — Distance to local extreme (full history)

Overall ±5d: mean **2.44%** · median 2.0124% · ≤1%: 0.194 · ≤3%: 0.7209
Overall ±21d: mean **4.9849%** · median 4.2072%
Mean T+1 drag vs signal-day extreme: **0.789%**

| sleeve | defense | n | ±5 mean% | ±5 med% | ±21 mean% | T+1 drag% |
|---|---|---:|---:|---:|---:|---:|
| FIN | ALL | 3066 | 2.5077 | 2.0908 | 5.2078 | 0.8388 |
| FIN | COOL_DEFEND | 706 | 3.2426 | 2.7208 | 6.0202 | 0.9139 |
| FIN | COOL_OFF | 2360 | 2.2878 | 1.9028 | 4.9648 | 0.8163 |
| TEL | ALL | 2425 | 2.0434 | 1.6902 | 3.9648 | 0.7297 |
| TEL | COOL_DEFEND | 561 | 2.4354 | 1.9791 | 4.4348 | 0.8051 |
| TEL | COOL_OFF | 1864 | 1.9254 | 1.5545 | 3.8233 | 0.707 |
| 0050 | ALL | 808 | 3.3733 | 2.9607 | 7.2006 | 0.7781 |
| 0050 | COOL_DEFEND | 187 | 4.4006 | 3.9721 | 8.4894 | 0.7802 |
| 0050 | COOL_OFF | 621 | 3.064 | 2.717 | 6.8125 | 0.7774 |
| ALL | ALL | 6299 | 2.44 | 2.0124 | 4.9849 | 0.789 |
| ALL | COOL_DEFEND | 1454 | 3.0801 | 2.5979 | 5.7261 | 0.8547 |
| ALL | COOL_OFF | 4845 | 2.2478 | 1.8864 | 4.7625 | 0.7693 |

## Windows

| window | n | ±5 mean% | ±21 mean% | T+1 drag% | cool_defend_share |
|---|---:|---:|---:|---:|---:|
| `full` | 6299 | 2.44 | 4.9849 | 0.789 | 0.2308 |
| `oof_2011_2018` | 2651 | 2.2161 | 4.3215 | 0.7319 | 0.1531 |
| `validation_2019_2022` | 1981 | 2.5134 | 5.5555 | 0.817 | 0.311 |
| `sealed_2023_plus` | 1667 | 2.7087 | 5.3618 | 0.8466 | 0.2591 |
| `heldout_2019_plus` | 3648 | 2.6026 | 5.467 | 0.8305 | 0.2873 |

## B — Mechanism tags (count of fills where tag active)

| mechanism | n_fills |
|---|---:|
| `T1_ALWAYS` | 6299 |
| `T1_DRAG` | 6299 |
| `KD_OFFSEASON` | 2805 |
| `DEFENSE_COOL` | 1454 |
| `CLIP_FIN_HI` | 160 |
| `DEFENSE_DH_CF` | 126 |

### Read

1. **T1_ALWAYS / T1_DRAG** — Exact T+1 open fills (by design).
2. **DEFENSE_COOL** — on-book COOL_c8 shrink day (live twin).
3. **DEFENSE_DH_CF** — same signal dates under historical DH rule (counterfactual).
4. **CLIP_*** — Soft-Frozen champion sleeve weight on a clip edge that signal day.
5. **KD_OFFSEASON / KD_BUY_BLOCK** — FIN KD season / pre-exdiv buy gate.

Compare tip audit (`LIVE_FILL_EXTREME_AUDIT_SCREEN`) for short live tip window.

Repro: `PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py`

Label: `LIVE_FILL_EXTREME_BACKTEST_SCREEN_2026-09-26__FILL_EXTREME_BACKTEST_DONE`
