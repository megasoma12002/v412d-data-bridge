# Strategy Debt Board

Date: 2026-09-05 (L2 Exact T+1 held-out MIXED stop)  
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
| L2 loss-engine charter | #44 — sealed-aware / bull-day gates frozen |
| FIN_CAP_50 month-end monitor | #44 — paper runbook live for ops |
| **L2 Exact T+1 OOF → adv-lite → held-out** | Locked `L2_FINCAP_ONLY`; adv-lite PASS; held-out **val PASS / sealed FAIL** → **`STOP_L2_HELDOUT_MIXED_KEEP_BASE`** |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Month-end KPI | **KEEP** |
| FIN_CAP_50 paper | Month-end dual-paper monitor | **OPERATING (paper)** |
| Live | E16+E18+E22_v2s | Unchanged |
| BASE | Keep Soft-Frozen **[0.50, 0.95]** | **KEEP** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| FIN_CAP month-end reviews | ≥1 clean cycle before any cutover talk | Silent Soft-Frozen flip |
| New charter only | Address sealed-only CAGR giveback (L1+L2 both failed) | Retune L1/L2 locks; reopen S1 |
| Optional | `E22_v2s_tw` default cutover-only | Silent default flip |

### WON’T
L1/L2 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50.

## Snapshot
| Topic | Number |
|---|---|
| L1 sealed CAGR giveback | **+8.91 pp** (FAIL) |
| L2 sealed CAGR giveback | **+4.33 pp** (FAIL; MDD +4.41 pp) |
| L2 val 2019–2022 | MDD **+3.06 pp**; CAGR giveback **−0.75 pp** (PASS) |
| FIN_CAP_50 held-out (combined) | MDD +3.06 pp; CAGR giveback 1.63 pp; MDD ~−19.6% |

## Pointers
- `research/gaps/MDD_L2_HELDOUT.md` / `MDD_L2_HELDOUT_DECISION.json`
- `research/gaps/MDD_L2_OOF.md` / `MDD_L2_ADV_LITE.md`
- `research/gaps/MDD_L2_LOSS_ENGINE_CHARTER.md`
- `research/gaps/FIN_CAP_50_MONTH_END_RUNBOOK.md`
