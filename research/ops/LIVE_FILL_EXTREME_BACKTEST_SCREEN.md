# Backtest fill extreme + mechanism audit — Screen

Generated: `2026-09-26T14:23:45Z`
Status: **`FILL_EXTREME_BACKTEST_DONE`** · Soft-Frozen KEEP · **no live wire** · book `LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8`

Fills: **6299** (BUY 3235 / SELL 3064) · `2012-12-05` → `2026-09-07` · codes `['0050', '2412', '2880', '2886', '2892', '3045', '4904', '5880']`
COOL defense day-frac: **16.02%**

## A — Distance to local extreme (full history)

Overall ±5d: mean **2.6809%** · median 2.0153% · ≤1%: 0.1937 · ≤3%: 0.7168
Overall ±21d: mean **5.4727%** · median 4.3162%
Mean T+1 drag vs signal-day extreme: **0.761%**

| sleeve | defense | n | ±5 mean% | ±5 med% | ±21 mean% | T+1 drag% |
|---|---|---:|---:|---:|---:|---:|
| FIN | ALL | 3066 | 2.5117 | 2.0812 | 5.2099 | 0.8293 |
| FIN | COOL_DEFEND | 706 | 3.3037 | 2.7355 | 6.2117 | 0.9468 |
| FIN | COOL_OFF | 2360 | 2.2747 | 1.896 | 4.9102 | 0.7942 |
| TEL | ALL | 2425 | 2.1303 | 1.7089 | 4.2024 | 0.7102 |
| TEL | COOL_DEFEND | 561 | 2.4751 | 1.9965 | 4.5737 | 0.8256 |
| TEL | COOL_OFF | 1864 | 2.0265 | 1.5794 | 4.0907 | 0.6754 |
| 0050 | ALL | 808 | 4.9758 | 2.9409 | 10.2822 | 0.6543 |
| 0050 | COOL_DEFEND | 187 | 4.4332 | 3.9369 | 9.2227 | 0.7835 |
| 0050 | COOL_OFF | 621 | 5.1392 | 2.6874 | 10.6012 | 0.6154 |
| ALL | ALL | 6299 | 2.6809 | 2.0153 | 5.4727 | 0.761 |
| ALL | COOL_DEFEND | 1454 | 3.1293 | 2.62 | 5.967 | 0.879 |
| ALL | COOL_OFF | 4845 | 2.5464 | 1.8858 | 5.3243 | 0.7256 |

## Windows

| window | n | ±5 mean% | ±21 mean% | T+1 drag% | cool_defend_share |
|---|---:|---:|---:|---:|---:|
| `full` | 6299 | 2.6809 | 5.4727 | 0.761 | 0.2308 |
| `oof_2011_2018` | 2651 | 2.2555 | 4.4093 | 0.7003 | 0.1531 |
| `validation_2019_2022` | 1981 | 2.5394 | 5.6296 | 0.8172 | 0.311 |
| `sealed_2023_plus` | 1667 | 3.5258 | 6.9773 | 0.7907 | 0.2591 |
| `heldout_2019_plus` | 3648 | 2.9901 | 6.2455 | 0.8051 | 0.2873 |

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
