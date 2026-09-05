# Strategy Debt Board

Date: 2026-09-05 (Track B S1 held-out STOP — keep A)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Gap 6.5 / debt closeout / Stage-8 archive | **On main** (#35, #36) |
| Stage-8 TECH2 stress controllers | **SATURATED** — do not re-grid |
| Dual-track charter + Track A monitor | **PR #37** (charter frozen) |
| Track B S1 OOF | Winner **S1-QRES / COMBO_VOL80_VAL00** (PR #38) |
| Track B S1 adv-lite → held-out | Adv-lite **PASS**; held-out **`FAIL_HELDOUT`** → **`STOP_S1_HELDOUT_KEEP_TRACK_A`** |
| FIN_CAP_50 research (parallel) | OOF + held-out **PASS** on PR #39 — **not live** |

### NOW
| Track / item | Action | Status |
|---|---|---|
| **A** S9A1 paper monitor | Month-end / panel refresh KPI cadence | **OPERATING — KEEP** |
| **B** E50-A3-S1 residual stress | Axis closed after held-out fail | **STOPPED** |
| Live | E16+E18+E22_v2s only | Unchanged |

### NEXT
| Item | Action | Do not |
|---|---|---|
| Track A | Continue S9A1 paper monitor | Retune cuts; claim PASS |
| Optional FIN_CAP_50 | Explicit promote PR (dual paper ledgers); default stays BASE | Silent live prior retune |
| MDD / loss engine | New charter for ≤15% drawdown path (FIN_CAP alone still ~−19.6% held MDD) | Assume FIN_CAP or S1 closes MDD |
| Optional | Explicit promote default=`E22_v2s_tw` cutover-only | Silent default flip |

### LATER / WON’T
Unchanged: pay-date/tax/board-lot live; invent E45 −13.16%; promote 2.5%/0.70; live-wire overlay; TECH2 remix as stress engine; **S1 cut retune**.

## Pointers
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md` — label `DUAL_TRACK_A_KEEP_B_S1_HELDOUT_STOP`
- `research/e50a/E50A_S1_HELDOUT.md` / `E50A_S1_HELDOUT_DECISION.json`
- `research/e50a/TRACK_A_S9A1_MONITOR_STATUS.md`
- FIN_CAP / CAGR gap: PR #39 (`research/gaps/` on that branch)
