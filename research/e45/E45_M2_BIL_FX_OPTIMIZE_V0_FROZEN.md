# E45 M2 — BIL_FX Optimize Batch v0 (FROZEN BEFORE METRICS)

Date: 2026-09-06  
Status: **FROZEN FOR PAPER** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md` · `E45_M2_TRUE_DEF_RELOCATE.md`  
Sensor: M1 intensity `s_{t-1}` unchanged (do not retune)  
Claimed MDD: **`RETIRED_HISTORICAL_NARRATIVE`** — no invented replacement

## Why this batch

Improve pack left three actionable gaps (constant FX haircuts are return-invariant; `00720B` fails §2; cut only tested at 0.50/0.75). This batch freezes the next honesty upgrades **before** metrics:

1. **Path-dependent FX friction** on `BIL_FX` turnover (not constant level haircut).  
2. **True TWD cash carry** via dated CBC rediscount ingest (not bond ETF).  
3. **Cut / intensity-cap grid** for giveback vs §2 tradeoff.

Observe OPEN for `M2_RELOC_BIL_FX_C50` is authorized by human 「請全做」 in the same batch (separate OPEN docs; Soft-Frozen/stitch still forbidden).

## A. Path-dependent FX friction

Baseline book: `RELOC_BIL_FX` @ `c=0.50` marked at **USDTWD mid** (same as v1).  
Additional drag (research proxy):

- Let `h_t = (spot_sell_t − spot_buy_t) / (2 · usdtwd_mid_t)` (one-way half-spread as fraction).  
- Let `Δw_t = DEF_weight_t − DEF_weight_{t-1}` from the Exact-T+1 sleeve schedule.  
- Portfolio return drag on day `t`: `|Δw_t| · h_t` (turnover notionals pay half-spread).  
- Rebuild NAV from mid-marked early-stack returns minus this drag.

Honesty: bank executable FX may be wider; mid mark between trades still optimistic for P&L attribution. This measures **path-dependent turnover friction**, not a constant markdown.

Books: `M2_RELOC_BIL_FX_C50_FXPATH` (@ cost ×1 and ×2).

## B. TWD cash with CBC rediscount carry

Ingest: CBC 「重貼現率」 step table → daily forward-fill  
Source: https://www.cbc.gov.tw/tw/lp-640-1.html  
Files: `data/def_proxies/cbc_rediscount_rate_steps.csv`, `cbc_rediscount_rate_daily.csv`

Destination algebra: same `RELOC_*` from FIN+0050.  
DEF series `TWD_CASH_CBC`: unit cash accruing at `rediscount_pct / 100 / 252` per equity session (ACT/252 research convention).

Honesty: rediscount is a **policy** rate — not retail deposits / MM funds / CBC bills you can freely size. Upper-bound carry proxy only.

Books: `M2_RELOC_TWD_CASH_CBC_C50` / `C75` · refs `TWD_CASH0`, `BIL_FX_MID`.

## C. Cut / intensity-cap grid

Sensor unchanged. Actuator still `RELOC_BIL_FX` to mid-marked BIL_FX.

| Knob | Grid |
|---|---|
| Cut `c` | `{0.35, 0.40, 0.45, 0.50, 0.55, 0.60}` |
| Intensity cap `κ` | `{0.60, 0.80, 1.00}` at `c=0.50` only |

Effective relocate fraction: `u = c · min(s_{t-1}, κ)`.

Pass read (informational): among §2 PASS books, prefer **lowest held-out CAGR giveback** vs BASE without inventing MDD replacements.

## D. Observe OPEN (same batch)

Human authorization: 「請全做」 (2026-09-06) includes OPEN observe for locked book **`M2_RELOC_BIL_FX_C50`**.  
OPEN docs + month-end pack wiring ship in this batch. Soft-Frozen / DEFAULT / stitch remain forbidden.

## Explicit non-actions

- No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot  
- No E45 mild-α densify  
- No merge DEF into `live_market.csv`  
- No invented MDD replacement  
- No pretending CBC rediscount = retail cash product  

Label: `E45_M2_BIL_FX_OPTIMIZE_V0_FROZEN_2026-09-06__PAPER_PLUS_OBSERVE_OPEN__STITCH_FORBIDDEN`
