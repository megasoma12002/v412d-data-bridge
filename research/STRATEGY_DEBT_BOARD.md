# Strategy Debt Board

Date: 2026-09-05 (code-review fixes: month-end NaN, fin_cap single-source, Soft-Frozen/live wording)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Stage-8 / debt closeout | On main (#35, #36) |
| L1/L2/L3 MDD engines | All MIXED stop on sealed CAGR |
| FIN_CAP_50 go-live verify | #49 — `NOT_READY_SEALED_CAGR` (sealed gb +4.33; PAUSE 1y/YTD) |
| Sealed CAGR improve diagnostics | CRISIS_ONLY / FIN70 / BLEND sealed-diag survivors |
| L4 path/mild-FIN charter | Frozen — util-rank; no harsh-cap family priority |
| L4 Exact T+1 OOF | `OOF_L4_READY_FOR_ADV_LITE` — locked `L4_DD_PATH_08_50` |
| L4 adv-lite | `ADV_LITE_L4_READY_FOR_HELDOUT` — placebo P=0.000; year-split OK |
| **L4 held-out** | **`PASS_HELDOUT_L4`** — val+sealed both clear |
| Code-review fixes | Month-end `0→nan` format; `e16_features_fin_cap` single-source; Soft-Frozen vs live cutover wording in `FROZEN_GOVERNANCE.md` |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Month-end KPI | **KEEP** |
| FIN_CAP_50 paper | Dual-paper observation; cutover frozen | **OPERATING (paper)** |
| Live Soft-Frozen | **[0.50, 0.95]** | **KEEP (no auto flip)** |
| L4 challenger | `L4_DD_PATH_08_50` held-out PASS | **RESEARCH PASS — dual-paper candidate only** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| Human review PR | Decide whether to open dual-paper for L4_DD_PATH vs Soft-Frozen | Auto live-wire / Soft-Frozen flip |
| If dual-paper | Month-end KPI parity with FIN50 paper rails | Promote without human PR |
| FIN_CAP month-end | Continue; cutover frozen while PAUSE/sealed fail | Auto-promote FIN50 |

### WON’T
L1/L2/L3/FIN50 lock retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50 / L4 without human PR.

## Snapshot
| Topic | Number |
|---|---|
| Go-live (FIN50) | **`NOT_READY_SEALED_CAGR`** |
| L4 OOF | **`OOF_L4_READY_FOR_ADV_LITE`** locked **`L4_DD_PATH_08_50`** |
| L4 adv-lite | **`ADV_LITE_L4_READY_FOR_HELDOUT`** (placebo P=**0.000**) |
| L4 held-out | **`PASS_HELDOUT_L4`** |
| Val | MDD **+1.63**pp; CAGR gb **+1.20**pp |
| Sealed | MDD **+1.47**pp; CAGR gb **+2.66**pp (≤3.0 gate) |

## Pointers
- `research/gaps/MDD_L4_HELDOUT.md`
- `research/gaps/MDD_L4_ADV_LITE.md`
- `research/gaps/MDD_L4_OOF.md`
- `research/gaps/MDD_L4_PATH_FINCAP_CHARTER.md`
- `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`
