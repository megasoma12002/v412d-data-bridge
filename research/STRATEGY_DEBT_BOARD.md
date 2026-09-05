# Strategy Debt Board

Date: 2026-09-05 (L2 charter frozen + FIN_CAP month-end monitor)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Stage-8 / debt closeout | On main (#35, #36) |
| Dual-track A + B S1 | S1 held-out FAIL (#40) → keep A |
| L1 MDD loss-engine | Held-out MIXED (#42) → **STOP L1** |
| L1 sealed attribution | COMBO ~38% in sealed; CAGR giveback 8.9pp (2024/2026) |
| FIN_CAP_50 dual-paper proposal | #43 — Soft-Frozen unchanged |
| **L2 loss-engine charter** | This PR — sealed-aware / bull-day gates frozen |
| **FIN_CAP_50 month-end monitor** | This PR — paper runbook live for ops |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Month-end KPI | **KEEP** |
| FIN_CAP_50 paper | Month-end dual-paper monitor | **OPERATING (paper)** |
| L2 MDD engine | Exact T+1 OOF screen per L2 charter | **NEXT HARNESS** |
| Live | E16+E18+E22_v2s | Unchanged |

### NEXT
| Item | Action | Do not |
|---|---|---|
| L2 OOF screen | L2-FINCAP-ONLY + L2-DD-PATH first | Retune L1 COMBO×0.50 |
| FIN_CAP month-end reviews | ≥1 clean cycle before any cutover talk | Silent Soft-Frozen flip |
| Optional | `E22_v2s_tw` default cutover-only | Silent default flip |

### WON’T
L1 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50.

## Snapshot
| Topic | Number |
|---|---|
| L1 sealed CAGR giveback | **+8.91 pp** (FAIL) |
| L1 sealed COMBO / CRISIS share | **38.3% / 13.5%** |
| FIN_CAP_50 held-out | MDD +3.06 pp; CAGR giveback 1.63 pp; MDD ~−19.6% |

## Pointers
- `research/gaps/MDD_L2_LOSS_ENGINE_CHARTER.md`
- `research/gaps/MDD_L1_SEALED_ATTRIBUTION.md`
- `research/gaps/FIN_CAP_50_MONTH_END_RUNBOOK.md`
- `research/gaps/FIN_CAP_50_PROMOTE_PROPOSAL.md`
