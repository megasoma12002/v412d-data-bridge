# Financial Within-Sleeve Allocation Charter — Research Only


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-08  
Status: **CHARTER ACCEPTED** — human **「金融也研究分開」** (research only)  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live (at writing): **KEEP** (FIN [0.50, 0.95]; live today [0.60, 0.90] · TEL [0.03, 0.35] · 0050 [0.00, 0.35])  
Execution context: capital **500M** (human-accepted operating scale) · board-lot **1000** · books **`E22_v2s_tw`**

Authority: `STRATEGY_UPDATE_STANDARD_PROCESS.md` · telecom within-sleeve precedent · `TW_SHARE_LOT_DEFINITIONS.md`

**Passing ≠ Soft-Frozen flip ≠ live cutover.**

---

## Problem

Financial sleeve (4 names: 2880/2886/2892/5880) currently **equal-splits** sleeve trade dollars.  
Telecom already has a within-sleeve research/live line (`TEL_MIN_LOT_PACK`). Human asked to **research Financial separately** the same way — not force all four names.

## In scope

1. Paper challengers for **within-Financial** allocation under board-lot 1000 @ **500M**.  
2. Predeclared policies; Exact T+1 + Soft-Frozen **sleeve** targets unchanged.  
3. Telecom within-sleeve held at **`TEL_EQUAL`** in this screen (isolate FIN).  
4. Compare vs `FIN_EQUAL` BASE: held-out score, tip FIN name count / concentration, cash.

## Out of scope / WON’T

- Soft-Frozen clip edit  
- Live `e21` wire until dedicated **ACCEPT live FIN within-sleeve cutover**  
- Changing Telecom live policy in this PR  
- Zero-lot / 零股 continuous-book orders  

---

## Predeclared policies (Stage B)

| id | Rule sketch |
|---|---|
| `FIN_EQUAL` | Equal split 4 names (BASE control) |
| `FIN_MIN_LOT_PACK` | Greedy ≥1 張 cheapest-first until sleeve budget exhausted |
| `FIN_TOP1` | Concentrate Financial sleeve into single highest-score name |
| `FIN_TOP2_EQUAL` | Top-2 by score; equal-split those two only |

## Predeclared policies (Stage C — per-name timing)

Human: **各檔各做各的**（除權息日不同 · 個股強弱時間不同）。Stage B hard concentrate **STOP**; Stage C is softer.

| id | Rule sketch |
|---|---|
| `FIN_RS_SOFT_TILT` | Buy $ soft-tilt by causal mom score (`exp(0.5·clip(z))`); sells equal among holders |
| `FIN_EXDIV_SKIP_BUY` | On cash/stock ex-date for a name, skip **buy** that name only; redistribute to others |
| `FIN_RS_SOFT_TILT_EXDIV` | Soft-tilt buys among non-exdiv names only |

Selection: **held-out 2019+**  
Score: `MDD_improve_pp − 0.5 × |CAGR_giveback_pp|` vs `FIN_EQUAL`  
Sealed 2023+: report-only after lock.

---

## Stage plan

```
A  ACCEPT charter                         ← DONE (「金融也研究分開」)
B  Paper hard policies @ 500M/整張          ← DONE · STOP_NO_POSITIVE_HELDOUT_SCORE
C  Ex-div skip-buy + RS soft-tilt         ← DONE · STAGE_C_CANDIDATES_LOCKED
D  Dual-paper EQUAL ∥ RS ∥ MIX_L75 ∥ KD_OPT ← OPERATING (+KD_OPT 2026-09-09)
E  Separate human ballot for live cutover
```

## Human ballot

See **`FIN_WITHIN_SLEEVE_ALLOC_DECISION_PACK.md`**.
