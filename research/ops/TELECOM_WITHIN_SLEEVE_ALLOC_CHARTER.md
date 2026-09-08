# Telecom Within-Sleeve Allocation Charter — Research Only

Date: 2026-09-08  
Status: **CHARTER ACCEPTED** — Stage B paper implementation authorized  
Class: **A. Research / EXPERIMENTAL**  
Soft-Frozen live: **KEEP** (FIN [0.50, 0.95] · TEL [0.03, 0.35] · 0050 [0.00, 0.35])  
Execution context: capital **3M** · board-lot **1000** · books **`E22_v2s_tw`**

Authority: `STRATEGY_UPDATE_STANDARD_PROCESS.md` · `CAPITAL_3M_RESTORE_2026-09-08.md` · `TW_SHARE_LOT_DEFINITIONS.md`

Ballot: human **`ACCEPT telecom within-sleeve charter`** (2026-09-08)

**Passing ≠ Soft-Frozen flip ≠ live cutover.**

---

## Problem

Live/paper allocate sleeve trade dollars **equally across names**:

`value = sleeve_trade[Telecom] * nav / len(TEL)`  → 3-way split.

Under **整張 1000** @ **3M**, TEL target ≈6% cannot fund 1 張 per name → **TEL holdings = 0** even though Soft-Frozen still wants a Telecom sleeve.

Raising capital to 15M fixed fills but changed scale economics; human restored **3M** and wants research on **not forcing all three telecom names**.

## In scope

1. Paper challengers for **within-Telecom** allocation under board-lot 1000 @ 3M.  
2. Predeclared policies (below); Exact T+1 + Soft-Frozen **sleeve** targets unchanged.  
3. Compare vs equal-split BASE: held-out score, tip TEL weight / fill rate, cash residual.  
4. Optional dual-paper observe if a policy clears held-out.

## Out of scope / WON’T

- Soft-Frozen clip edit  
- Drop Telecom from universe permanently  
- Rewrite `forward/e21` until dedicated live ACCEPT  
- Change FIN within-sleeve rule in the same PR (Telecom-only first)  
- Zero-lot / 零股 continuous-book orders  

---

## Predeclared policies (Stage B)

| id | Rule sketch |
|---|---|
| `TEL_EQUAL` | Current: equal split 3 names (BASE control) |
| `TEL_MIN_LOT_PACK` | Greedy: buy ≥1 張 on cheapest-first names until sleeve budget exhausted; skip unaffordable |
| `TEL_TOP1` | Concentrate Telecom sleeve into single highest-score name (board-lot) |
| `TEL_TOP2_EQUAL` | Pick top-2 by score; equal-split those two only |

Selection window: **held-out 2019+**  
Score: `MDD_improve_pp − 0.5 × |CAGR_giveback_pp|` vs `TEL_EQUAL`  
Sealed 2023+: report-only after lock.

Execution: Exact T+1 · `E22_v2s_tw` · `lot_size=1000` · `capital=3_000_000`.

---

## Pass / fail

| Gate | Pass |
|---|---|
| Soft-Frozen | Sleeve clip module **untouched** |
| Exact T+1 | ok |
| Board-lot | fills multiples of 1000 |
| Identity | Challenger ids distinct from Soft-Frozen BASE |
| Live | No auto-wire |

Fail → keep equal-split live; Soft-Frozen KEEP.

---

## Stage plan

```
A  ACCEPT charter                                      ← DONE 2026-09-08
B  Implement paper policies + BASE equal-split @ 3M    ← THIS PR
C  Held-out rank; sealed report for top ≤2
D  Optional dual-paper observe
E  Separate human ballot for live within-sleeve cutover
```

## Human ballot

See **`TELECOM_WITHIN_SLEEVE_ALLOC_DECISION_PACK.md`**.

| Ballot | Effect |
|---|---|
| **ACCEPT charter** | Stage B paper implementation allowed — **ACCEPTED** |
| **DEFER / REJECT** | No code; live stays equal-split @ 3M |
