# Live fill extreme audit — adj OHLC re-run

Generated from tip fills · `ohlc_basis=adj_close_scaled`
Status: **FILL_EXTREME_AUDIT_DONE** · Soft-Frozen KEEP · no live wire

Fills: **96** (BUY 72 / SELL 24) · `2026-08-25` → `2026-09-16`

## 1 — Distance to local extreme (adj)

Overall ±5d mean **3.79%** · median 3.12% · ±21d mean **7.76%** · T+1 mean **1.15%**

| sleeve | side | n | ±5 mean% | ±5 med% | ±21 mean% | T+1% |
|---|---|---:|---:|---:|---:|---:|
| ALL | ALL | 96 | 3.79 | 3.12 | 7.76 | 1.15 |
| ALL | BUY | 72 | 4.03 | 3.20 | 8.32 | 1.40 |
| ALL | SELL | 24 | 3.07 | 2.83 | 6.09 | 0.42 |
| FIN | ALL | 48 | 4.65 | 4.19 | 9.04 | 1.62 |
| FIN | BUY | 48 | 4.65 | 4.19 | 9.04 | 1.62 |
| TEL | ALL | 36 | 2.85 | 2.65 | 5.70 | 0.64 |
| TEL | BUY | 15 | 2.60 | 1.81 | 4.98 | 0.94 |
| TEL | SELL | 21 | 3.02 | 2.86 | 6.22 | 0.42 |
| 0050 | ALL | 12 | 3.18 | 3.54 | 8.83 | 0.85 |
| 0050 | BUY | 9 | 3.10 | 3.91 | 10.05 | 0.99 |
| 0050 | SELL | 3 | 3.43 | 2.80 | 5.16 | 0.45 |

### COOL / DH windows (this tip span)

- COOL_CF on: **0** fills · DH on: **0** — tip Aug–Sep predates COOL live; full exposure

## 2 — Mechanism contrast (binding tags)

| mechanism | n_fills |
|---|---:|
| `T1_ALWAYS` | 96 |
| `T1_DRAG` | 96 |
| `KD_OFFSEASON` | 48 |
| `CLIP_FIN_HI` | 48 |

### Read

1. **T+1** — all 96 fills Exact T+1 (structural drag, not a defect to same-bar-fix).
2. **CLIP_FIN_HI** — 48 fills on signal days when Soft-Frozen FIN weight sits on hi clip.
3. **KD_OFFSEASON** — all 48 FIN fills (Aug–Sep outside Apr15–May15).
4. **COOL / DH** — neither shrinks exposure in this tip window (0 defend fills).

Label: `LIVE_FILL_EXTREME_AUDIT_ADJ_RERUN_2026-09-26__FILL_EXTREME_AUDIT_DONE`

