# Live fill extreme + mechanism audit — Screen

Generated: `2026-09-26T14:15:29Z`
Status: **`FILL_EXTREME_AUDIT_DONE`** · Soft-Frozen KEEP · **no live wire** · no tip rewrite

Fills: **96** (BUY 72 / SELL 24) · `2026-08-25` → `2026-09-16` · codes `['0050', '2412', '2880', '2886', '2892', '3045', '4904', '5880']`

## A — Distance to local extreme

Overall ±5d: mean **3.7887%** · median 3.115% · ≤1%: 0.0729 · ≤3%: 0.4896
Overall ±21d: mean **7.7602%** · median 6.6721%
Mean T+1 drag vs signal-day extreme: **1.1543%**

| sleeve | defense | n | ±5 mean% | ±5 med% | ±21 mean% | T+1 drag% |
|---|---|---:|---:|---:|---:|---:|
| FIN | ALL | 48 | 4.6479 | 4.1885 | 9.036 | 1.6175 |
| TEL | ALL | 36 | 2.8457 | 2.6486 | 5.704 | 0.6366 |
| 0050 | ALL | 12 | 3.1807 | 3.5429 | 8.8256 | 0.8541 |
| ALL | ALL | 96 | 3.7887 | 3.115 | 7.7602 | 1.1543 |

## B — Mechanism tags (count of fills where tag active)

| mechanism | n_fills |
|---|---:|
| `T1_ALWAYS` | 96 |
| `T1_DRAG` | 96 |
| `KD_OFFSEASON` | 48 |
| `CLIP_FIN_HI` | 48 |

### Read

1. **T1_ALWAYS / T1_DRAG** — every tip fill is Exact T+1; drag vs signal-day low/high is structural.
2. **CLIP_*** — Soft-Frozen sleeve weight on a clip edge that signal day.
3. **DEFENSE_DH** — historical tip defense (fill window pre-COOL live).
4. **DEFENSE_COOL_CF** — same dates under reconstructed COOL_c8 (counterfactual).
5. **KD_OFFSEASON** — FIN fills outside Apr15–May15 (expected for Aug–Sep tip).

Repro: `PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py`

Label: `LIVE_FILL_EXTREME_AUDIT_SCREEN_2026-09-26__FILL_EXTREME_AUDIT_DONE`
