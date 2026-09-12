# Sleeve-Layer Tilt Dual-Paper Observe — OPEN

Date: 2026-09-10  
Status: **OPERATING OBSERVE** (paper only)  
Human: **`OPEN Sleeve-tilt observe: SLEEVE_RSI14_LT30_a0225`**  
Soft-Frozen clips live **KEEP** · live wire **false** · Soft-assist observe **UNCHANGED**

Prior seed `SLEEVE_BELOW_MA60_a01` superseded 2026-09-12 (rule-path OPEN).

## Books

| Book | Soft-Frozen / within-sleeve |
|---|---|
| `LIVE_STACK` | Soft-Frozen FINBAND + `KD_OPT` + `TEL_EQUAL` |
| `SLEEVE_RSI14_LT30_a0225` | Same within-sleeve + Soft-Frozen router `score + 0.225 · 1{sleeve RSI14 < 30}` → clip/blend |

## Why these two

Stage A `SLEEVE_LAYER_TILT_SCREEN.md` (#191): champion tip-clean beat-live (held ≈ **+0.050**). Soft-assist remains a separate observe track.

## Gates (month-end)

YTD / trailing 1y vs `LIVE_STACK` (ALERT 3pp / PAUSE 5pp). Held-out is historical lock; tip is operating.

## Operating artifacts

| Artifact | Path |
|---|---|
| Dual-paper ledgers | `scripts/e16_sleeve_tilt_dual_paper_ledgers.py` |
| Month-end monitor | `scripts/e16_sleeve_tilt_month_end_monitor.py` |
| Helpers | `scripts/sleeve_tilt_helpers.py` |
| Operating memo | `SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPERATING.md` |
| Posture | `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md` |
| Ballot executed | `SLEEVE_LAYER_TILT_OBSERVE_BALLOT_EXECUTED_OPEN_OBSERVE.md` |
| Cutover stub | `CUTOVER_CHECKLIST_SLEEVE_LAYER_TILT.md` (**BLOCKED**) |
| Repro | `repro/sleeve-tilt-dual-paper-observe/` |

## WON’T

- Soft-Frozen clip flip · live Sleeve-tilt wire · KD/TEL change · Soft-assist combo · E45 stitch

## Label

`SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPEN_2026-09-10__OPERATING__LIVE_KEEP`
