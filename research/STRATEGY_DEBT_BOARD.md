# Strategy Debt Board

Date: 2026-09-05 (L3 Exact T+1 held-out MIXED stop)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Stage-8 / debt closeout | On main (#35, #36) |
| Dual-track A + B S1 | S1 held-out FAIL (#40) → keep A |
| L1 MDD loss-engine | Held-out MIXED (#42) → **STOP L1** |
| FIN_CAP_50 dual-paper proposal | #43 — Soft-Frozen unchanged |
| L2 charter + month-end monitor | #44 |
| L2 Exact T+1 OOF → held-out | #45 — `STOP_L2_HELDOUT_MIXED_KEEP_BASE` |
| L2 sealed CAGR attribution | FIN 78.9%→50%; giveback 2024/25/26 |
| L3 sealed-CAGR charter | #46 |
| L3 Exact T+1 OOF (MILD+BLEND) | #47 — locked `L3_MILD_35_60` |
| **L3 adv-lite → held-out** | Adv-lite **PASS** (placebo P=0.042); held-out **val PASS / sealed FAIL** → **`STOP_L3_HELDOUT_MIXED_KEEP_BASE`** |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Month-end KPI | **KEEP** |
| FIN_CAP_50 paper | Month-end dual-paper monitor | **OPERATING (paper)** |
| Live | E16+E18+E22_v2s | Unchanged |
| BASE | Soft-Frozen **[0.50, 0.95]** | **KEEP** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| FIN_CAP month-end reviews | ≥1 clean cycle before any cutover talk | Silent Soft-Frozen flip |
| New charter only | Address sealed-only CAGR giveback (L1+L2+L3 all failed sealed ≤3.0pp) | Retune L1/L2/L3 locks; reopen S1 |
| Optional | `E22_v2s_tw` default cutover-only | Silent default flip |

### WON’T
L1/L2/L3 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50.

## Snapshot
| Topic | Number |
|---|---|
| L3 locked | `L3_MILD_35_60` (FIN [0.35, 0.60]) |
| L3 val 2019–2022 | MDD **+1.91 pp**; CAGR giveback **−0.61 pp** (PASS) |
| L3 sealed 2023+ | MDD **+5.29 pp**; CAGR giveback **+4.08 pp** (FAIL ≤3.0) |
| L2 sealed CAGR giveback | **+4.33 pp** (FAIL) |
| L1 sealed CAGR giveback | **+8.91 pp** (FAIL) |

## Pointers
- `research/gaps/MDD_L3_HELDOUT.md` / `MDD_L3_HELDOUT_DECISION.json`
- `research/gaps/MDD_L3_ADV_LITE.md` / `MDD_L3_OOF.md`
- `research/gaps/MDD_L3_SEALED_CAGR_CHARTER.md`
- `research/gaps/FIN_CAP_50_MONTH_END_RUNBOOK.md`
