# Strategy Debt Board

Date: 2026-09-05 (FIN_CAP_50 go-live verify BLOCKED)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Stage-8 / debt closeout | On main (#35, #36) |
| Dual-track A + B S1 | S1 held-out FAIL (#40) → keep A |
| L1/L2/L3 MDD engines | All MIXED stop on sealed CAGR (#42/#45/#48) |
| FIN_CAP_50 dual-paper + month-end | #43/#44 — paper ops |
| **FIN_CAP_50 go-live verification** | Exact T+1 refresh: Gate B (2019+) **PASS**; Gate C sealed **FAIL** (CAGR gb **+4.33pp**); Gate E PAUSE_REVIEW (1y/YTD) → **`NOT_READY_SEALED_CAGR` / KEEP Soft-Frozen** |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Month-end KPI | **KEEP** |
| FIN_CAP_50 paper | Dual-paper observation only (cutover frozen) | **OPERATING (paper)** |
| Live | E16+E18+E22_v2s Soft-Frozen **[0.50, 0.95]** | **KEEP** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| New charter only | Address sealed-only CAGR giveback (FIN concentration + 2023+) | Retune FIN_CAP_50 lock; silent Soft-Frozen flip |
| FIN_CAP month-end | Continue observation; cutover discussion frozen while PAUSE_REVIEW | Auto-promote |
| Optional | `E22_v2s_tw` default cutover-only | Silent default flip |

### WON’T
L1/L2/L3 cut retune; FIN_CAP_50 lock retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50.

## Snapshot
| Topic | Number |
|---|---|
| Go-live label | **`NOT_READY_SEALED_CAGR`** |
| Held-out 2019+ | MDD **+3.06 pp**; CAGR gb **+1.63 pp** (PASS) |
| Sealed 2023+ | MDD **+4.41 pp**; CAGR gb **+4.33 pp** (FAIL ≤3) |
| Trailing 1y CAGR gb | **+7.21 pp** → PAUSE_REVIEW |
| YTD CAGR gb | **+16.73 pp** → PAUSE_REVIEW |

## Pointers
- `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`
- `research/gaps/FIN_CAP_50_MONTH_END_RUNBOOK.md`
- `research/gaps/MDD_L3_HELDOUT.md`
