# Soft ∥ Sleeve Borrow-Promote — Research Charter (paper Stage A)

Date: 2026-09-12  
Status: **PAPER SCREEN DONE** · verdict **`HAS_PROMOTE_SHAPED_CANDIDATE`** · **no live wire** · **no Soft×Sleeve fuse**  
Human ask: 把這幾輪查到的資料進行研究看能不能測試出新的更優解

Screen: `SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.md` · Script: `scripts/e16_soft_sleeve_borrow_promote_screen.py`

Soft-Frozen **clips KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · E45 stitch **OFF**  
Soft-assist observe **KEEP** on `SOFT_CHAMP_PLUS_K9_LT30_a10` · Sleeve-tilt observe **KEEP** on `SLEEVE_BELOW_MA60_a01`

## Stage A outcome (asof 2026-09-11)

| Track | Verdict | Promote-shaped highlight |
|---|---|---|
| Soft | **`PROMOTE_SHAPED_BEATS_OBSERVE`** | `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` (held 0.101 vs observe 0.085) · also `…_a15` |
| Sleeve | **`MDD_CLEAR_BEATS_LIVE`** | `SLEEVE_RSI14_LT30_a02` tip-MDD clean + held>0 (lift tiny vs seed) |
| Overall | **`HAS_PROMOTE_SHAPED_CANDIDATE`** | Paper only — observe swap needs dedicated ballot · **no auto-wire** |

Seed `SLEEVE_BELOW_MA60_a01` remains tip-clean but **tip_mdd_clean=False** (same month-end MDD ALERT pattern). Lower-α MA60 neighbors did **not** clear tip MDD while keeping held>0.

## Question

Borrow-informed Stage A: does a **promote-shaped** paper challenger exist that

1. **Soft track** — tip-clean + tip MDD clean + held-out score beats current Soft-assist observe, or
2. **Sleeve track** — tip-clean + tip MDD clean (clears month-end MDD ALERT pattern) + held-out score > 0 vs `LIVE_STACK`?

**Promote-shaped** = tip YTD+1y PASS **and** tip YTD+1y MDD not worse than base **and** held-out score > 0.

## Why this charter (borrow map)

| Borrow note | Local map |
|---|---|
| Note 2 — soft informs, does not replace | Soft additive amplitude grid around K9+ observe (assist only) |
| Note 3 — tilt must clear diversification / risk hygiene | Sleeve lower-α / neighbor signals + **tip MDD hygiene** |
| Notes 4/5 — play-well ≠ auto-fuse | Soft ∥ Sleeve independent tracks; **no Soft×Sleeve combo** |

Evidence inputs: Soft KD/BB sensitivity `BEATS_CHAMPION` · Soft-assist month-end clean · Sleeve Stage A `BEATS_LIVE` but month-end **MDD ALERTs** · external borrow notes (PR #198 draft).

## Stage A grid (finite)

**Soft (~12 books):** `LIVE_KD_OPT` · Soft-assist champion · observe `SOFT_CHAMP_PLUS_K9_LT30_a10` · K9 amplitude `{0.25,0.5,0.75,1.25,1.5}` · K9_LT20@1 · sell amplitude `{0.5,1.5}` · K9@0.75+BB@0.25

**Sleeve (~12 books):** `LIVE_STACK` · BELOW_MA60 α `{0.025,0.05,0.075,0.10,0.125}` · BELOW_MA40 `{0.025,0.05,0.10}` · RSI14_LT30 `{0.10,0.15,0.20}`

## Non-actions

- No Soft-assist / Sleeve-tilt observe swap from this screen alone  
- No Soft×Sleeve auto-combo  
- No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire  
- No hard-AND indicator reopen  

## Label

`SOFT_SLEEVE_BORROW_PROMOTE_CHARTER_2026-09-12__HAS_PROMOTE_SHAPED_CANDIDATE`
