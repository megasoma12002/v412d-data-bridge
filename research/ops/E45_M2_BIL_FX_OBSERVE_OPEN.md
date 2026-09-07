# E45 M2 BIL_FX Observe — OPEN (**ACCEPTED / OPERATING** · lock **C35**)

Date: 2026-09-07  
Human authorization: **「請優化」** → **ACCEPT OPEN C35** retarget  
Prior C50 OPEN: 2026-09-06 via 「請全做」 (`E45_M2_BIL_FX_OBSERVE_OPEN` history)  
Prior C35 ballot: `research/ops/E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT.md`  
Prior HOLD: `research/ops/E45_M2_C35_OBSERVE_RETARGET_HOLD.md` (**SUPERSEDED**)  
Evidence: `research/e45/E45_M2_C35_RETARGET_BALLOT.md` · optimize `E45_M2_BIL_FX_OPTIMIZE.md`

Status: **OPERATING OBSERVE** (paper only)  
Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Retired MDD: **`RETIRED_HISTORICAL_NARRATIVE`**  
Parallel OPERATING: FULL + A25 + A05 + FIN_A10 + **BIL_FX_C35** (replaces C50 as lock)

Chinese mirror: `research/ops/E45_M2_BIL_FX_OBSERVE_OPEN.zh-TW.md`

## Ballot

| Field | Value |
|---|---|
| Choice | **Retarget OPEN** M2 BIL_FX observe **C50 → C35** |
| Locked paper book | **`M2_RELOC_BIL_FX_C35`** |
| Prior lock | `M2_RELOC_BIL_FX_C50` (evidence retained; lock retired) |
| Sensor / actuator | M1 `s_{t-1}` · `RELOC_BIL_FX` · cut `c=0.35` |
| DEF honesty | `BIL_FX` = USD T-bill × USDTWD mid — FX risk; mid optimistic; **not** TWD cash |
| Why | Optimize giveback-min among §2 PASS cuts (held giveback ~2.23 pp vs C50 ~3.43) |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch? | **No** |
| HIGH_BETA OPEN? | **No** (HOLD DRAFT) |
| C75 auto-OPEN? | **No** |

## Pre-open checklist (YES)

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen [0.50, 0.95] | **YES** |
| 2 | DEFAULT `E22_v2s_tw` | **YES** |
| 3 | C35 §2 PASS + retarget evidence present | **YES** |
| 4 | MDD narrative RETIRED | **YES** |
| 5 | No stitch / Soft-Frozen / DEFAULT in this PR | **YES** |
| 6 | BIL_FX honesty banner | **YES** |
| 7 | Parent observe sleeves parallel | **YES** |
| 8 | Explicit human ACCEPT | **YES** — 「請優化」 |
| 9 | Lock is C35 (not silent TEL/C75/HIGH_BETA) | **YES** |

## Operating artifacts

| Artifact | Path |
|---|---|
| Ledgers | `scripts/e45_m2_bil_fx_dual_paper_ledgers.py` (CUT=0.35) |
| Month-end monitor | `scripts/e45_m2_bil_fx_month_end_monitor.py` |
| Month-end pack | `scripts/ops_month_end_paper_pack.py` |
| Repro | `repro/e45-m2-bil-fx-dual-paper-observe/` |

## Explicit non-actions

1. No live stitch / Soft-Frozen / DEFAULT flip  
2. No invent MDD replacement  
3. No HIGH_BETA OPEN  
4. No auto-OPEN C75  
5. No label BIL_FX as TWD cash  
6. No merge DEF into `live_market.csv`

## Label

`E45_M2_BIL_FX_OBSERVE_OPEN_2026-09-07__OPERATING__M2_RELOC_BIL_FX_C35__RETARGET_FROM_C50__STITCH_FORBIDDEN`
