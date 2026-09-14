# E45 Blend-α=0.25 Dual-Paper Observe — OPEN Ballot


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-06  
Status: **ARCHIVED (human: 封存 E45_BLEND025 observe · 2026-09-13)** · was OPERATING · stitch still **FORBIDDEN**
Archive batch: `RESEARCH_ARCHIVE_BATCH_E45_BLEND025_2026-09-13.md`
Human ballot: **`E45 OPEN blend-α=0.25 observe`** (proceed next step after paper screen)  
Authority: Register #6c follow-on · `E45_BLEND_ALPHA_PAPER_SCREEN.md` · `E45_STAGE12_STATUS.md`

Soft-Frozen (at writing): **[0.50, 0.95]** · **live today [0.60, 0.90]**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`**  
Parent full-E45 observe: residual / not primary (`E45_DUAL_PAPER_OBSERVE_OPEN.md`)

## Ballot

| Field | Value |
|---|---|
| Choice | **OPEN blend-α=0.25 observe** |
| Paper books | `BASE_E16_E18_E22_v2s` vs `BLEND_E45_A25` |
| Overlay | `exposure = 0.75·1 + 0.25·E3_VOLTARGET_WINNER` |
| Cadence | Month-end parallel paper ledgers + monitor |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch authorized? | **No** |

## Why this sleeve

Paper blend-alpha screen held-out heuristic preferred **α=0.25**:
~**+0.63 pp** MDD improve vs ~**2.83 pp** CAGR giveback (vs full E45 ~1.88 / 5.65).

## Pre-open checklist (recorded YES)

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen live clip at writing was [0.50, 0.95]; live today [0.60, 0.90] | **YES** |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | **YES** |
| 3 | Parent blend-alpha screen present | **YES** |
| 4 | retired MDD narrative still RETIRED | **YES** |
| 5 | No stitch / live-wire PR bundled | **YES** |
| 6 | Month-end owner = `ops_month_end_paper_pack.py` / research/ops | **YES** |
| 7 | PAUSE_REVIEW policy understood (observe ≠ stitch) | **YES** |
| 8 | Full-E45 observe sleeve left operating in parallel | **YES** |

## Operating artifacts

| Artifact | Path |
|---|---|
| Ledgers | `scripts/e45_blend025_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e45_blend025_month_end_monitor.py` |
| Repro | `repro/e45-blend025-dual-paper-observe/` |
| Monitor JSON | `research/gaps/E45_BLEND025_MONTH_END_MONITOR.json` |

## Explicit non-actions

1. Do **not** live-stitch E45 / rewrite `forward/e21` history.  
2. Do **not** flip Soft-Frozen or DEFAULT books.  
3. Do **not** treat blend sleeve clean prints as stitch license.  
4. Do **not** retire/replace the full-E45 observe sleeve without a separate ballot.

## Label

`E45_BLEND025_OBSERVE_OPEN_2026-09-06__ARCHIVED_2026-09-13__STITCH_FORBIDDEN`

## Archive seal (2026-09-13)

Human: **封存 E45_BLEND025 observe**.  
Tip YTD/1y giveback ~11 pp **PAUSE_REVIEW** → removed from operating month-end / alert queue.  
FINCAP `BLEND_025` observe **KEEP**. Reopen only with **new charter + human ballot**.
