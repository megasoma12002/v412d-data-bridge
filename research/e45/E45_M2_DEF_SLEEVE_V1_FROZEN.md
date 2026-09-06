# E45 M2 — Frozen DEF Sleeve + Relocate Rule v1 (BEFORE any sealed metrics)

Date: 2026-09-06  
Status: **FROZEN FOR PAPER SCREEN** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent ingest: `E45_M2_TRUE_DEF_DATA_V0_FROZEN.md` · `data/def_proxies/`  
Parent v0 (equity DEF_TEL PASS): `E45_M2_DEF_SLEEVE_V0_FROZEN.md`  
Sensor: M1 intensity `s_t` lag-1 — unchanged; do not retune  
Claimed MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## Honesty bound

v1 relocates to **research DEF proxies** (not merged into `forward/e21/live_market.csv`).  
v0 `DEF_TEL` PASS is **not** rewritten; v1 is a separate screen.

| DEF destination | Instrument | Honesty limit |
|---|---|---|
| `DEF_719B` | TW ETF `00719B` (Yuanta 1–3Y US bond wrapper) | TWD-listed short-duration; **lists 2018-02-01**; still bond/FX beta, not local TWD bills |
| `DEF_BIL_FX` | USD `BIL` × FinMind `USDTWD` spot mid | Cash-like USD + FX; **not** a TWD money-market fund; FX can dominate |
| `DEF_TEL` | Telecom sleeve (v0 ref only) | Equity proxy — rebuild ref, not retuned |
| `DEF_CASH0` | Cash residual @ 0% | Shrink control only |

Primary challengers: **`DEF_719B`** and **`DEF_BIL_FX`**.  
Long ETFs `00679B` / `00687B` are **out of scope** for v1 relocate (duration stress only; not cash).

## Pre-list policy (frozen)

For books that target `DEF_719B`:

- On dates **before** `00719B` first bar (`2018-02-01`): destination = **`DEF_BIL_FX`** (no synthetic bond backfill).
- On/after first bar: destination = **`00719B`** close/open from ingest.
- Do **not** invent pre-2018 `00719B` prices.

`DEF_BIL_FX` books use BIL×FX for the full sample (no switch).

## Intensity (frozen, from M1)

`u_t = c · s_{t-1}`, `c ∈ {0.50, 0.75}`, clipped to `[0,1]`.  
Exact T+1 fills unchanged.

## Soft-Frozen base sleeve weights

Daily Soft-Frozen targets `w = (w_FIN, w_TEL, w_0050)` from E16 early-stack (unchanged).

## Modes (frozen)

### (a) `SHRINK` — rebuild control (cash@0)

Same as v0: scale all three equity sleeves by `(1 − u_t)`; residual cash @ 0%.

### (b) `RELOC_TEL` — rebuild v0 equity-DEF ref

Same as v0: move FIN+0050 → Telecom.

### (c) `RELOC_719B` — relocate to true short-duration DEF (primary)

```
move_FIN  = w_FIN  · u_t
move_0050 = w_0050 · u_t
w_FIN'  = w_FIN  − move_FIN
w_0050' = w_0050 − move_0050
w_TEL'  = w_TEL
w_DEF'  = move_FIN + move_0050
```

`DEF` marks the active destination per pre-list policy (`BIL_FX` then `00719B`).  
Sources: FIN + 0050 only.

### (d) `RELOC_BIL_FX` — relocate to USD cash-like × FX

Same weight algebra as (c); destination always `BIL_FX` TWD series  
`px_t = adj_close_BIL_t · usdtwd_mid_t` (ffill join onto equity calendar; no lookahead).

### (e) `HYBRID_719B` — 50/50 shrink + relocate-to-719B

```
w_i^s = w_i · (1 − 0.5·u_t)           # FIN, TEL, 0050
move_FIN  = w_FIN  · 0.5·u_t
move_0050 = w_0050 · 0.5·u_t
w_FIN'  = w_FIN^s  − move_FIN
w_0050' = w_0050^s − move_0050
w_TEL'  = w_TEL^s
w_DEF'  = move_FIN + move_0050
```

Residual from the shrink half stays **cash @ 0%** (not DEF).

## Cost model (frozen)

- DEF trades use **ETF** tax/fee lane (`TAX_ETF` / ETF buy-sell fees) in early-stack cost-×.
- No extra FX spread beyond mid for `BIL_FX` (honesty: mid is optimistic; state in report).
- Cost multiples `{0,1,2,3}` × same fee keys as v0.

## Book IDs

| Book | Mode | `c` |
|---|---|---|
| `M2_SHRINK_C50` | SHRINK | 0.50 |
| `M2_RELOC_TEL_C50` | RELOC_TEL | 0.50 |
| `M2_RELOC_719B_C50` | RELOC_719B | 0.50 |
| `M2_RELOC_719B_C75` | RELOC_719B | 0.75 |
| `M2_RELOC_BIL_FX_C50` | RELOC_BIL_FX | 0.50 |
| `M2_RELOC_BIL_FX_C75` | RELOC_BIL_FX | 0.75 |
| `M2_HYBRID_719B_C50` | HYBRID_719B | 0.50 |
| `M2_HYBRID_719B_C75` | HYBRID_719B | 0.75 |

## References (always run)

- `BASE_E16_E18_E22_v2s`
- `BLEND_E45_A05`
- `SLEEVE_FIN_ONLY_A10` (observe OPERATING — reference only)

## Qualification

Inherit charter §2 rules 1–6.  
**v1 informational gates (do not auto-OPEN observe / Soft-Frozen / stitch):**

1. Best true-DEF relocate/hybrid clears §2, **or** publish autopsy.  
2. Report COVID-ex held-out score vs rebuilt `M2_RELOC_TEL_C50` (equity DEF).  
3. §2 PASS ≠ observe OPEN (dedicated ballot still required).

## Explicit non-actions

- Do **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots
- Do **not** merge DEF codes into live market from this pack
- Do **not** densify E45 mild-α as a substitute
- Do **not** treat `BIL_FX` as local TWD cash
- Do **not** change these formulas after seeing sealed scores (amendment = new `v2` freeze)
- Do **not** invent a replacement for the retired MDD narrative

Label: `E45_M2_DEF_SLEEVE_V1_FROZEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`
