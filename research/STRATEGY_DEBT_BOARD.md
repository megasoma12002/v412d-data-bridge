# Strategy Debt Board

Date: 2026-09-05 (MDD loss-engine charter frozen)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Gap 6.5 / debt closeout / Stage-8 archive | **On main** (#35, #36) |
| Stage-8 TECH2 stress controllers | **SATURATED** — do not re-grid |
| Dual-track A monitor + B S1 | Charter #37; OOF #38; S1 held-out **FAIL** #40 → **keep A** |
| FIN_CAP_50 research | PASS held-out on #39 — **not live**; held MDD ~−19.6% |
| MDD diagnosis + L1 charter | This PR — `MDD_LOSS_ENGINE_CHARTER_FROZEN__DIAGNOSIS_READY` |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 paper monitor | Month-end KPI cadence | **KEEP** |
| **L1 MDD loss engine** | Exact T+1 OOF screen per charter | **NEXT HARNESS** |
| Live | E16+E18+E22_v2s only | Unchanged |

### NEXT
| Item | Action | Do not |
|---|---|---|
| L1-CRISIS-EQ / L1-STRESS-DET OOF | Exact replay harness; frozen gates | Treat proxy scales as PASS |
| Optional FIN_CAP_50 promote | Explicit dual-ledger cutover PR | Silent prior retune |
| Optional | Default=`E22_v2s_tw` cutover-only | Silent default flip |

### WON’T
S1 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; promote 2.5%/0.70; live-wire overlay; proxy-as-PASS.

## Snapshot
| Topic | Number |
|---|---|
| Formal E22_v2s | 13.78% / −22.64% |
| Target | ≥20% / ≤15% depth |
| E45 scale on formal books | **1.000 (inert)** |
| Worst DD episode | 2020-01-20→03-19 −22.6%; Crisis share 13.9% |

## Pointers
- `research/gaps/MDD_LOSS_ENGINE_CHARTER.md`
- `research/gaps/MDD_LOSS_ENGINE_DIAGNOSIS.md`
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md` (on #40: A keep / B S1 stop)
