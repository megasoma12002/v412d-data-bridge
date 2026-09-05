# Strategy Debt Board

Date: 2026-09-05 (FIN_CAP_50 dual-paper promote proposal)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip remains **[0.50, 0.95]**.

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Gap 6.5 / Stage-8 archive | **On main** (#35, #36) |
| Dual-track A + B S1 | S1 held-out FAIL (#40) → keep Track A |
| L1 MDD loss-engine | OOF+adv PASS; held-out **MIXED** (#42) → **STOP L1 / keep BASE** |
| FIN_CAP_50 research | OOF+held-out **PASS** (#39 lineage) |
| **FIN_CAP_50 dual paper promote proposal** | This PR — Soft-Frozen default **unchanged** |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 paper monitor | Month-end KPI cadence | **KEEP** |
| Live | E16+E18+E22_v2s; FIN clip [0.50,0.95] | Unchanged |
| FIN_CAP_50 | Dual paper ledgers for ops review | **PROPOSAL READY** |
| L1 MDD axis | Closed | **STOPPED** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| Human review of dual paper books | ≥1 month-end compare BASE vs FIN_CAP_50 | Silent Soft-Frozen clip flip |
| Optional cutover PR (later) | Named FIN_CAP_50 ledger + keep BASE paper forever | History rewrite; claim MDD≤15% |
| Optional | Default=`E22_v2s_tw` cutover-only | Silent default flip |
| New loss-engine (only if needed) | Fresh charter (sealed CAGR giveback was L1 failure mode) | Retune L1_FINCAP50_COMBO_50 |

### WON’T
S1/L1 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50 from this proposal.

## Snapshot
| Topic | Number |
|---|---|
| Formal E22_v2s | ~13.8% / −22.6% |
| FIN_CAP_50 held-out vs BASE | MDD **+3.06 pp**; CAGR giveback **1.63 pp** |
| FIN_CAP_50 held MDD | ~−19.6% (still short of ≤15%) |
| L1 sealed failure | CAGR giveback 8.9 pp |

## Pointers
- `research/gaps/FIN_CAP_50_PROMOTE_PROPOSAL.md`
- `repro/fincap50-dual-paper/`
- `research/gaps/FIN_CAP_HELDOUT.md`
- `research/gaps/MDD_L1_HELDOUT.md` (on #42)
