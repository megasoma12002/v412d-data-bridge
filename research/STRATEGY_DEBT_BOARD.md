# Strategy Debt Board

Date: 2026-09-05 (L4 dual-paper observation opened)  
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
| L4 Exact T+1 OOF → adv-lite → held-out | **`PASS_HELDOUT_L4`** — on main via #51 |
| Dual-track A/B | On main via #37 — A KEEP / B S1 STOP |
| Code-review fixes | Month-end `0→nan`; fin_cap single-source; Soft-Frozen vs live wording |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Paper/monitor harness + month-end KPI | **KEEP** |
| Live Soft-Frozen | **[0.50, 0.95]** | **KEEP (no auto flip)** |
| FIN_CAP_50 paper | Dual-paper observation; cutover frozen | **OPERATING (paper; NOT_READY)** |
| **L4 dual-paper** | BASE vs `L4_DD_PATH_08_50` Exact T+1 books + month-end | **OPERATING (paper)** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| L4 month-end | ≥1 clean review via `e16_l4_dd_path_month_end_monitor.py` | Auto live-wire / Soft-Frozen flip |
| Human cutover PR | Only after clean month-end + explicit approval (wires DD-path logic) | Path-logic without named PR |
| Track A month-end | Refresh KPI via `scripts/e50a_dual_track_s9a1_monitor.py` | Retune S9A1 cuts |
| FIN_CAP month-end | Continue; cutover frozen while PAUSE/sealed fail | Auto-promote FIN50 / conflate with L4 |
| New alpha charter | Only with a **new** charter (not S1 residual re-grid) | Reopen S1 / TECH2 remix |

### WON’T
L1/L2/L3/FIN50 lock retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50 / L4 without human PR; reopen S1 residual detector grid.

## Snapshot
| Topic | Number |
|---|---|
| Go-live (FIN50) | **`NOT_READY_SEALED_CAGR`** |
| L4 held-out | **`PASS_HELDOUT_L4`** (`L4_DD_PATH_08_50`) |
| L4 dual-paper | **OPERATING** (Soft-Frozen unchanged) |
| Track A | **KEEP** (S9A1 paper/monitor) |
| Track B S1 | **`STOP_S1_HELDOUT_KEEP_TRACK_A`** |
| Soft-Frozen clip | **[0.50, 0.95]** |

## Pointers
- `research/gaps/L4_DD_PATH_PROMOTE_PROPOSAL.md`
- `research/gaps/L4_DD_PATH_MONTH_END_RUNBOOK.md`
- `research/gaps/L4_DD_PATH_MONTH_END_MONITOR.md`
- `research/gaps/MDD_L4_HELDOUT.md`
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md`
- `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`
