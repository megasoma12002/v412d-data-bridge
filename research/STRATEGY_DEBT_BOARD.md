# Strategy Debt Board

Date: 2026-09-05 (L3 Exact T+1 OOF screen)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.  
Live E16 Financial clip: **[0.50, 0.95]** (unchanged).

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Stage-8 / debt closeout | On main (#35, #36) |
| Dual-track A + B S1 | S1 held-out FAIL (#40) → keep A |
| L1 MDD loss-engine | Held-out MIXED (#42) → **STOP L1** |
| L1 sealed attribution | COMBO ~38% in sealed; CAGR giveback 8.9pp |
| FIN_CAP_50 dual-paper proposal | #43 — Soft-Frozen unchanged |
| L2 loss-engine charter | #44 — sealed-aware / bull-day gates frozen |
| FIN_CAP_50 month-end monitor | #44 — paper runbook live for ops |
| L2 Exact T+1 OOF → adv-lite → held-out | #45 — `STOP_L2_HELDOUT_MIXED_KEEP_BASE` |
| L2 sealed CAGR attribution | FIN 78.9%→50%; giveback 2024/25/26; not COMBO timing |
| L3 sealed-CAGR charter | #46 — MILD/BLEND/BULL-RESTORE/DD-ONLY + tight OOF CAGR gates |
| **L3 Exact T+1 OOF (MILD+BLEND)** | Locked **`L3_MILD_35_60`**; 4 passers → **`OOF_L3_READY_FOR_ADV_LITE`** |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Month-end KPI | **KEEP** |
| FIN_CAP_50 paper | Month-end dual-paper monitor | **OPERATING (paper)** |
| Live | E16+E18+E22_v2s | Unchanged |
| BASE | Keep Soft-Frozen **[0.50, 0.95]** | **KEEP** |
| L3 locked | `L3_MILD_35_60` (FIN hi=0.60) | Adv-lite **NEXT** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| L3 adv-lite | Placebo FIN intensity + year-split + late-bull on locked | Retune MILD/BLEND cuts; reopen L1/L2 |
| If adv-lite PASS | One held-out (val + sealed) | Live-wire; Soft-Frozen flip |
| Deferred L3 families | BULL-RESTORE / DD-ONLY only if OOF/held-out stop | Expand grid before stop |
| FIN_CAP month-end reviews | ≥1 clean cycle before cutover talk | Silent Soft-Frozen flip |

### WON’T
L1/L2 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50.

## Snapshot
| Topic | Number |
|---|---|
| L3 OOF locked | **`L3_MILD_35_60`** (MDD **+2.88 pp**; CAGR gb **+0.10 pp**; late-bull gb **+0.15 pp**) |
| L3 OOF passers | 4 (`L3_MILD_35_60`=`L3_MILD_50_60`, `L3_BLEND_050`, `L3_BLEND_075`) |
| L2 sealed CAGR giveback | **+4.33 pp** (FAIL; MDD +4.41 pp) |
| L1 sealed CAGR giveback | **+8.91 pp** (FAIL) |

## Pointers
- `research/gaps/MDD_L3_OOF.md` / `MDD_L3_OOF_SUMMARY.json`
- `research/gaps/MDD_L3_SEALED_CAGR_CHARTER.md`
- `research/gaps/MDD_L2_SEALED_CAGR_ATTRIBUTION.md`
- `research/gaps/FIN_CAP_50_MONTH_END_RUNBOOK.md`
