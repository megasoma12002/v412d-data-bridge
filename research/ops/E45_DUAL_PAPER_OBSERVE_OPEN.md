# E45 Dual-Paper Observe — OPEN Ballot


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-05  
Human ballot: **`E45 OPEN dual-paper observe`**  
Authority: Register #6c follow-on · `E45_DUAL_PAPER_OBSERVE_CHECKLIST.md` · `E45_STAGE12_STATUS.md`

Soft-Frozen (at writing): **[0.50, 0.95]** · **live today [0.60, 0.90]**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN** (second dedicated stitch ACCEPT still required)  
Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## Ballot

| Field | Value |
|---|---|
| Choice | **OPEN dual-paper observe** |
| Paper books | `BASE_E16_E18_E22_v2s` vs `CHAL_E45_E3` |
| Cadence | Month-end parallel paper ledgers + monitor |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch authorized? | **No** |

## Pre-open checklist (recorded YES)

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen live clip at writing was [0.50, 0.95]; live today [0.60, 0.90] | **YES** |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | **YES** |
| 3 | Design metrics present (`repro/e45-dual-paper-observe-design/`) | **YES** |
| 4 | the retired handoff MDD narrative labeled **RETIRED_HISTORICAL_NARRATIVE** (not verified) | **YES** |
| 5 | No stitch / live-wire PR bundled | **YES** |
| 6 | Month-end monitor owner | **`ops_month_end_paper_pack.py` / research/ops** |
| 7 | PAUSE_REVIEW policy understood (observe ≠ promote / stitch) | **YES** |

## Operating artifacts

| Artifact | Path |
|---|---|
| Ledgers harness | `scripts/e45_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e45_month_end_monitor.py` |
| Runbook | `research/gaps/E45_MONTH_END_RUNBOOK.md` |
| Observe sleeve memo | `research/e45/E45_DUAL_PAPER_OBSERVE.md` |
| Repro root | `repro/e45-dual-paper-observe/` |

## Explicit non-actions

1. Do **not** live-stitch E45 / rewrite `forward/e21` history.  
2. Do **not** flip Soft-Frozen or DEFAULT books.  
3. Do **not** treat clean month-end as stitch license.  
4. Do **not** cite the retired handoff MDD narrative as verified.

## Label

`E45_DUAL_PAPER_OBSERVE_OPEN_2026-09-05__OPERATING__STITCH_FORBIDDEN`
