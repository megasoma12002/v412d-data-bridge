# E45 Sleeve-Local Observe — OPEN Ballot (**ACCEPTED / OPERATING**)

Date: 2026-09-06  
Human ballot: **`E45 ACCEPT OPEN sleeve-local observe`**  
Status: **OPERATING OBSERVE** (paper only)  
Prior draft: `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN_BALLOT_DRAFT.md`  
Authority: Register #6c follow-on · `E45_SLEEVE_LOCAL.md` · `E45_SLEEVE_LOCAL_DEEP_DIVE.md` · `E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`**  
Parent observe sleeves still OPERATING in parallel: FULL E45 + blend-α=0.25 + blend-α=0.05

Chinese mirror (non-binding): `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN.zh-TW.md`

## Ballot

| Field | Value |
|---|---|
| Choice | **OPEN sleeve-local observe** |
| Paper books | `BASE_E16_E18_E22_v2s` vs `SLEEVE_FIN_ONLY_A10` |
| Overlay | E45 `E3_VOLTARGET_WINNER` @ **α=0.10** applied **only** to Financial sleeve |
| Cadence | Month-end parallel paper ledgers + monitor |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch authorized? | **No** |
| Retire FULL / A25 / A05? | **No** |

## Why this sleeve

Sleeve-local deep-dive held-out preferred **`FIN_ONLY @ α=0.10`** (score ~0.285) over whole-book A05 (~0.222); 2× cost twin still positive; crisis MDD help still ~84% in 2020. Opening is **observe-only** to learn structure vs whole-book A05. Expect YTD/1y **PAUSE_REVIEW** at current tip. Stitch remains forbidden.

## Pre-open checklist (recorded YES)

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen live clip remains [0.50, 0.95] | **YES** |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | **YES** |
| 3 | Parent sleeve-local paper + deep-dive present | **YES** |
| 4 | retired MDD narrative still RETIRED | **YES** |
| 5 | No stitch / live-wire PR bundled | **YES** |
| 6 | Month-end owner = `ops_month_end_paper_pack.py` / research/ops | **YES** |
| 7 | PAUSE_REVIEW policy understood (observe ≠ stitch) | **YES** |
| 8 | FULL + A25 + A05 observe sleeves left operating in parallel | **YES** |
| 9 | Explicit human ACCEPT recorded | **YES** — `ACCEPT 開 observe` |

## Operating artifacts

| Artifact | Path |
|---|---|
| Ledgers | `scripts/e45_sleeve_local_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e45_sleeve_local_month_end_monitor.py` |
| Repro | `repro/e45-sleeve-local-dual-paper-observe/` |
| Monitor JSON | `research/gaps/E45_SLEEVE_LOCAL_MONTH_END_MONITOR.json` |

## Explicit non-actions

1. Do **not** live-stitch E45 / rewrite `forward/e21` history.  
2. Do **not** flip Soft-Frozen or DEFAULT books.  
3. Do **not** treat sleeve-local clean prints as stitch license.  
4. Do **not** retire FULL / A25 / A05 observe without a separate ballot.  
5. Do **not** invent a replacement for the retired MDD narrative number.

## Label

`E45_SLEEVE_LOCAL_OBSERVE_OPEN_2026-09-06__OPERATING__SLEEVE_FIN_ONLY_A10__STITCH_FORBIDDEN`
