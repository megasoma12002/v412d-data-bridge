# FIN Within-Sleeve Dual-Paper Observe — OPEN

Date: 2026-09-08  
Human ballot: **`dual-paper 觀察 FIN_RS_SOFT_TILT_EXDIV 並排 FIN_EQUAL`**  
Follow-on: **`把 MIX_L75 加進 dual-paper observe`** (2026-09-08)  
Authority: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md` Stage D · Stage C `STAGE_C_CANDIDATES_LOCKED` · Mix `COEXIST_CANDIDATE_FOUND`

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live FIN equal-split (`e21`): **KEEP / untouched**  
Live within-sleeve cutover: **still FORBIDDEN** (dedicated ACCEPT required)

## Ballot

| Field | Value |
|---|---|
| Choice | **OPEN / extend multi-paper observe** |
| Paper books | `FIN_EQUAL` ∥ `FIN_RS_SOFT_TILT_EXDIV` ∥ **`MIX_L75`** (λ=0.75) |
| Capital / lot | **500M** / **1000** (charter exec) |
| Cadence | Month-end parallel paper ledgers + monitor |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |

## Pre-open checklist

| # | Item | YES/NO |
|---|---|---|
| 1 | Soft-Frozen live clip remains [0.50, 0.95] | **YES** |
| 2 | Stage C locked top = `FIN_RS_SOFT_TILT_EXDIV` | **YES** |
| 3 | Mix coexist candidate = `MIX_L75` | **YES** (`FIN_EQUAL_RS_EXDIV_MIX.md`) |
| 4 | Live e21 FIN equal-split unchanged | **YES** |
| 5 | No live-wire PR bundled | **YES** |
| 6 | Month-end pack wiring | **YES** (`ops_month_end_paper_pack.py`) |
| 7 | PAUSE_REVIEW ≠ cutover license | **YES** |

## Operating artifacts

| Artifact | Path |
|---|---|
| Ledgers | `scripts/e16_fin_within_sleeve_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e16_fin_within_sleeve_month_end_monitor.py` |
| Observe memo | `research/ops/FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPERATING.md` |
| Repro root | `repro/fin-within-sleeve-dual-paper-observe/` |

## Explicit non-actions

1. Do **not** wire `FIN_RS_SOFT_TILT_EXDIV` or `MIX_L75` into `e21` from this observe.  
2. Do **not** flip Soft-Frozen clips.  
3. Do **not** treat clean month-end as live cutover license.  
4. Stage B hard policies remain **STOP**.

## Label

`FIN_WITHIN_SLEEVE_DUAL_PAPER_OBSERVE_OPEN_2026-09-08__OPERATING__MIX_L75_ADDED__LIVE_WIRE_FORBIDDEN`
