# E45 M2 — BIL_FX Improve Pack v0 (FROZEN BEFORE METRICS)

Date: 2026-09-06  
Status: **FROZEN FOR PAPER** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_M2_DEF_SLEEVE_V1_FROZEN.md` · `E45_M2_TRUE_DEF_RELOCATE.md`  
Sensor: M1 intensity `s_{t-1}` unchanged (do not retune)  
Claimed MDD: **`RETIRED_HISTORICAL_NARRATIVE`** — no invented replacement

## Why this pack

M2 v1 §2 PASS on `M2_RELOC_BIL_FX_C50/C75` left three design gaps:

1. FX mark uses **mid only** (optimistic; no bid/ask haircut).  
2. No **TWD-local** cash / short twin vs USD×FX.  
3. Observe OPEN still DRAFT — needs wiring **awaiting human ACCEPT** (this pack prepares; does not ACCEPT).

## A. FX / mark sensitivity (BIL_FX only)

Baseline algebra unchanged: `RELOC_BIL_FX` with `c ∈ {0.50, 0.75}`.  
Price of DEF leg (TWD):

| Mark id | Formula | Honesty |
|---|---|---|
| `MID` | `BIL_adj × usdtwd_mid` | v1 baseline (optimistic) |
| `SPOT_BUY` | `BIL_adj × spot_buy` | Conservative long-USD mark |
| `SPOT_SELL` | `BIL_adj × spot_sell` | Optimistic long-USD mark |
| `MID_H5` | `MID × (1 − 5bp)` | One-way haircut |
| `MID_H10` | `MID × (1 − 10bp)` | One-way haircut |
| `MID_H25` | `MID × (1 − 25bp)` | One-way haircut |
| `MID_H50` | `MID × (1 − 50bp)` | One-way haircut |

Haircut is applied to the **level series** before returns (constant proportional markdown of the FX-converted price path).  
Cost multiples for sensitivity: **1× and 2×** only (fee keys same as v1).

**Pass read (informational):** does `RELOC_BIL_FX_C50` still clear charter §2 under `SPOT_BUY` and under `MID_H25`?  
If not → publish autopsy; do **not** auto-OPEN observe.

## B. TWD twin destinations

Same relocate algebra as v1 (`RELOC_*` from FIN+0050). Destinations:

| Code | Instrument | Honesty |
|---|---|---|
| `TWD_CASH0` | Residual cash @ **0%** (≡ SHRINK control destination) | Not a yield; control only |
| `TWD_720B` | TW-listed ETF `00720B` (short-duration bond wrapper) | **TWD-listed**, still bond/rate beta — **not** CBC bills / MM fund |
| `BIL_FX_MID` | v1 baseline | USD×FX |

Pre-list for `00720B`: first bar **2018-02-01**; before that fall back to `TWD_CASH0` (no synthetic bond backfill).  
Do **not** invent Taiwan policy-rate carry without a dated rate ingest + new freeze.

Books @ `c=0.50` (and `c=0.75` for BIL_FX / 720B only):

- `M2_RELOC_TWD_CASH0_C50` (control twin)  
- `M2_RELOC_TWD_720B_C50` / `C75`  
- Rebuild refs: `M2_RELOC_BIL_FX_C50`, `M2_RELOC_TEL_C50`, `M2_SHRINK_C50`, BASE / BLEND_A05 / SLEEVE_FIN_A10

## C. Observe OPEN prep (NOT ACCEPT)

Prepare Exact T+1 dual paper ledgers + month-end monitor for locked book **`M2_RELOC_BIL_FX_C50`** with banner honesty (FX + mid optimistic; not TWD cash).  

Status of observe artifacts in this pack: **`AWAITING_HUMAN_ACCEPT`** — do **not** mark OPERATING, do **not** add to `ops_month_end_paper_pack.py` until a separate ACCEPT.

## Explicit non-actions

- No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot  
- No silent TEL default  
- No merge of DEF into `live_market.csv`  
- No E45 mild-α densify  
- No invented MDD replacement  
- No ACCEPT of observe from this freeze alone

Label: `E45_M2_BIL_FX_IMPROVE_V0_FROZEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`
