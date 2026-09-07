# E45 M2 BIL_FX Relocate Observe — OPEN (**ACCEPTED / OPERATING**)

Date: 2026-09-06  
Human authorization: **「請全做」** (ACCEPT OPEN for locked book only)  
Status: **OPERATING OBSERVE** (paper only)  
Prior awaiting: `research/ops/E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md`  
Prior draft ballot: `research/ops/E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.md`  
Optimize paper: `research/e45/E45_M2_BIL_FX_OPTIMIZE.md`

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`**  
Parent observe sleeves still OPERATING in parallel: FULL + A25 + A05 + `SLEEVE_FIN_ONLY_A10`

Chinese mirror (non-binding): `research/ops/E45_M2_BIL_FX_OBSERVE_OPEN.zh-TW.md`

## Ballot

| Field | Value |
|---|---|
| Choice | **OPEN M2 BIL_FX relocate observe** |
| Locked paper book | **`M2_RELOC_BIL_FX_C50`** |
| Sensor / actuator | M1 intensity `s_{t-1}` · `RELOC_BIL_FX` · cut `c=0.50` |
| DEF honesty | `BIL_FX` = USD T-bill ETF × USDTWD **mid** — FX risk; mid optimistic; **not** TWD cash |
| Cadence | Month-end parallel paper ledgers + monitor |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch authorized? | **No** |
| Auto-OPEN C75? | **No** (still ballot-gated) |
| Retire FULL / A25 / A05 / FIN_A10? | **No** |

## Why this book

True-DEF §2 PASS on `M2_RELOC_BIL_FX_C50`; improve pack showed mid-mark return-invariance of constant FX haircuts; optimize pack adds path FX friction (~0.62 pp held giveback vs mid) and CBC cash twin honesty. Opening is **observe-only** to learn live paper behavior under Exact T+1 dual ledgers. Stitch remains forbidden.

## Pre-open checklist (recorded YES)

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen live clip remains [0.50, 0.95] | **YES** |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | **YES** |
| 3 | M2 v1 §2 PASS + improve/optimize papers present | **YES** |
| 4 | Retired MDD narrative still RETIRED | **YES** |
| 5 | No stitch / Soft-Frozen / DEFAULT flip bundled | **YES** |
| 6 | BIL_FX honesty banner (FX + mid optimistic; not TWD cash) | **YES** |
| 7 | Parent observe sleeves left operating in parallel | **YES** |
| 8 | Explicit human ACCEPT recorded | **YES** — 「請全做」 |
| 9 | Locked book is BIL_FX C50 (not silent TEL / C75) | **YES** |

## Operating artifacts

| Artifact | Path |
|---|---|
| Ledgers | `scripts/e45_m2_bil_fx_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e45_m2_bil_fx_month_end_monitor.py` |
| Month-end pack wiring | `scripts/ops_month_end_paper_pack.py` |
| Repro | `repro/e45-m2-bil-fx-dual-paper-observe/` |
| Optimize paper | `research/e45/E45_M2_BIL_FX_OPTIMIZE.md` |

## Explicit non-actions

1. Do **not** live-stitch E45 / rewrite `forward/e21` history.  
2. Do **not** flip Soft-Frozen or DEFAULT books.  
3. Do **not** treat M2 observe clean prints as stitch license.  
4. Do **not** auto-OPEN `M2_RELOC_BIL_FX_C75` without a separate ballot.  
5. Do **not** invent a replacement for the retired MDD narrative.  
6. Do **not** label `BIL_FX` or CBC rediscount as retail TWD cash.  
7. Do **not** merge DEF proxies into `live_market.csv`.

## Label

`E45_M2_BIL_FX_OBSERVE_OPEN_2026-09-06__OPERATING__M2_RELOC_BIL_FX_C50__STITCH_FORBIDDEN`
