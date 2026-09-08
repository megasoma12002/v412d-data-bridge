# Capital 500M + live TEL_MIN_LOT_PACK — 2026-09-08

Human: **「A接受 B 500m」**  
Soft-Frozen sleeve clips: **KEEP** (FIN [0.50, 0.95] · TEL [0.03, 0.35] · 0050 [0.00, 0.35])  
stitch: **FORBIDDEN** · board-lot **1000 KEEP**

## Ballots executed

| | Decision |
|---|---|
| **A** | **ACCEPT live within-sleeve cutover** → `TEL_MIN_LOT_PACK` |
| **B** | **Capital 500M** → `DEFAULT_CAPITAL = 500_000_000` |

Note: Stage B paper screen was `STOP_NO_POSITIVE_HELDOUT_SCORE` vs `TEL_EQUAL`.  
Live cutover is an **explicit human override** (fill / scale priority).

## Change

- `scripts/portfolio_capital.py` — `DEFAULT_CAPITAL = 500_000_000`
- `scripts/telecom_within_sleeve.py` — shared within-Telecom allocator; `LIVE_TELECOM_ALLOC = TEL_MIN_LOT_PACK`
- Live `e21_forward_pipeline` — Telecom orders via `TEL_MIN_LOT_PACK` (FIN/0050 equal-split)
- Paper `simulate_core` — default `telecom_alloc` aligned to live
- Authorized wipe+replay `forward/e21` 2026-08-24→tip @ 500M + board-lot 1000

## Live tip after replay (2026-09-07)

| | 3M equal-split | **500M + TEL_MIN_LOT_PACK** |
|---|---:|---:|
| NAV | ≈3.16M | ≈**534.4M** |
| cash | ≈14.6% | ≈**0%** |
| TEL weight | **0%** | ≈**6.7%** |
| TEL 張 (2412/3045/4904) | 0/0/0 | **0 / 0 / 352** (cheapest-first pack) |
| Soft-Frozen clips | KEEP | **KEEP** |

QC + Gap6 PASS. `telecom_within_sleeve=TEL_MIN_LOT_PACK`.
