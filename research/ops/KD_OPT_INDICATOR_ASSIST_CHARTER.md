# KD_OPT + Indicator Assist Screen (paper)

Date: 2026-09-10  
Status: **OPEN / PAPER ONLY**  
Human: **「LIVE_KD_OPT 還有進步空間嗎？ex 加入別的指標輔助找出低點或高點」**  
Soft-Frozen **KEEP** · live **KD_OPT KEEP** until ACCEPT · E45 stitch **OFF**

## Context

R1–R3 showed **replacing** KD_OPT with other TA (or pure buy-low/sell-high) did **not** beat live.  
Remaining question: keep **`LIVE_KD_OPT` as base**, add indicators as **assist filters**.

## Design

Base (unchanged mechanics):

- Scores: Yahoo K9 season `KD_APR15_MAY15_Klt30_T15`
- Buy window: pre-ex T−15 skip (`kd_buy_ok`)

Assist layers (paper):

| Mode | Buy gate | Sell gate |
|---|---|---|
| `KD+BUY_AND_LOW` | `kd_buy_ok AND low_i` | equal (default) |
| `KD+SELL_HIGH` | `kd_buy_ok` | `high_j` (else skip sell) |
| `KD+BOTH` | `kd_buy_ok AND low_i` | `high_j` |

Low/high catalog = Round-3 finite market TA (`ta_indicator_catalog.py`).

## Gates

Same coexist / beat-live vs `FIN_EQUAL` and held-out lift vs **`LIVE_KD_OPT`**.

## Artifacts

- Script: `scripts/e16_kd_opt_indicator_assist_screen.py`
- Results: `research/ops/KD_OPT_INDICATOR_ASSIST_SCREEN.md` (+ `.json`)
- Repro: `repro/kd-opt-indicator-assist/`

## Non-actions

No live KD_OPT param change / Soft-Frozen flip / E45 stitch from this screen alone.

## Label

`KD_OPT_INDICATOR_ASSIST_2026-09-10__PAPER_ONLY__BASE_KD_KEEP`
