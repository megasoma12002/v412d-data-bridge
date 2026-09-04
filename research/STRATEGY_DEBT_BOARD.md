# Strategy Debt Board

Date: 2026-09-05 (dual-track #37 rebase onto main after L4/#51)  
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
| Code-review fixes | Month-end `0→nan`; fin_cap single-source; Soft-Frozen vs live wording |
| **Track B E50-A3-S1** | OOF lock → adv-lite PASS → **`FAIL_HELDOUT` → `STOP_S1_HELDOUT_KEEP_TRACK_A`** (#40 closed) |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 | Paper/monitor harness + month-end KPI | **KEEP** |
| Live Soft-Frozen | **[0.50, 0.95]** | **KEEP (no auto flip)** |
| FIN_CAP_50 paper | Dual-paper observation; cutover frozen | **OPERATING (paper)** |
| L4 challenger | `L4_DD_PATH_08_50` held-out PASS | **RESEARCH PASS — dual-paper candidate only** |
| Dual-track board | A monitor live-as-paper; B S1 axis stopped | **A KEEP / B STOP** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| Human review | Decide L4_DD_PATH dual-paper vs Soft-Frozen | Auto live-wire / Soft-Frozen flip |
| Track A month-end | Refresh KPI via `scripts/e50a_dual_track_s9a1_monitor.py` | Retune S9A1 cuts |
| New alpha charter | Only with a **new** charter (not S1 residual re-grid) | Reopen S1 / TECH2 remix |
| FIN_CAP month-end | Continue; cutover frozen while PAUSE/sealed fail | Auto-promote FIN50 |

### WON’T
L1/L2/L3/FIN50 lock retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; live-wire overlay; proxy-as-PASS; auto-promote FIN_CAP_50 / L4 without human PR; reopen S1 residual detector grid.

## Snapshot
| Topic | Number |
|---|---|
| Go-live (FIN50) | **`NOT_READY_SEALED_CAGR`** |
| L4 held-out | **`PASS_HELDOUT_L4`** (`L4_DD_PATH_08_50`) |
| Track A | **KEEP** (S9A1 paper/monitor) |
| Track B S1 | **`STOP_S1_HELDOUT_KEEP_TRACK_A`** |
| Soft-Frozen clip | **[0.50, 0.95]** |

## Pointers
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md`
- `research/e50a/TRACK_A_S9A1_MONITOR_STATUS.md`
- `research/e50a/E50A_S1_HELDOUT.md` (when present)
- `research/gaps/MDD_L4_HELDOUT.md`
- `research/gaps/FIN_CAP_50_GO_LIVE_VERIFY.md`
