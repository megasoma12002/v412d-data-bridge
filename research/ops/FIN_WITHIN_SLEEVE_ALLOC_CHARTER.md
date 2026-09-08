# Financial Within-Sleeve Allocation Charter — Research Only

Date: 2026-09-08  
Status: **CHARTER ACCEPTED** — human **「金融也研究分開」** (research only)  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live: **KEEP** (FIN [0.50, 0.95] · TEL [0.03, 0.35] · 0050 [0.00, 0.35])  
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

Selection: **held-out 2019+**  
Score: `MDD_improve_pp − 0.5 × |CAGR_giveback_pp|` vs `FIN_EQUAL`  
Sealed 2023+: report-only after lock.

---

## Stage plan

```
A  ACCEPT charter                         ← DONE (「金融也研究分開」)
B  Paper policies + BASE @ 500M/整張      ← THIS PR
C  Held-out rank; sealed report top ≤2
D  Optional dual-paper observe
E  Separate human ballot for live cutover
```

## Human ballot

See **`FIN_WITHIN_SLEEVE_ALLOC_DECISION_PACK.md`**.
