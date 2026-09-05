# Strategy Debt Board

Date: 2026-09-05 (L1 MDD loss-engine held-out MIXED — keep BASE)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Gap 6.5 / debt closeout / Stage-8 archive | **On main** (#35, #36) |
| Stage-8 TECH2 stress controllers | **SATURATED** — do not re-grid |
| Dual-track A monitor + B S1 | Charter #37; OOF #38; S1 held-out **FAIL** #40 → **keep A** |
| FIN_CAP_50 research | PASS held-out on #39 — **not live**; held MDD ~−19.6% |
| MDD diagnosis + L1 charter | #41 — charter frozen |
| **L1 Exact T+1 OOF → adv-lite → held-out** | OOF **PASS** lock `L1_FINCAP50_COMBO_50`; adv-lite **PASS** (placebo P=0.0); held-out **`STOP_L1_HELDOUT_MIXED`** (val PASS / sealed FAIL — CAGR giveback 8.9pp) → **keep BASE** |

### NOW
| Item | Action | Status |
|---|---|---|
| Track A S9A1 paper monitor | Month-end KPI cadence | **KEEP** |
| Live | E16+E18+E22_v2s only | Unchanged |
| L1 MDD axis | Closed under frozen cuts | **STOPPED** |

### NEXT
| Item | Action | Do not |
|---|---|---|
| Optional FIN_CAP_50 promote | Explicit dual-ledger cutover PR | Silent prior retune |
| New loss-engine charter (if any) | Must fix sealed CAGR giveback / different mechanism | Retune L1_FINCAP50_COMBO_50 cuts |
| Optional | Default=`E22_v2s_tw` cutover-only | Silent default flip |

### WON’T
S1 cut retune; Stage-8 TECH2 re-grid; invent E45 −13.16%; promote 2.5%/0.70; live-wire overlay; proxy-as-PASS; **L1 cut retune after MIXED held-out**.

## Snapshot
| Topic | Number |
|---|---|
| Formal E22_v2s | 13.78% / −22.64% |
| Target | ≥20% / ≤15% depth |
| L1 locked (research) | FIN_CAP_50 + COMBO×0.50 |
| L1 OOF | MDD +8.3pp / CAGR giveback 1.4pp — PASS |
| L1 sealed held-out | MDD +7.7pp but CAGR giveback **8.9pp** — FAIL gate |

## Pointers
- `research/gaps/MDD_L1_OOF.md` / `MDD_L1_ADV_LITE.md` / `MDD_L1_HELDOUT.md`
- `research/gaps/MDD_LOSS_ENGINE_CHARTER.md`
- `research/e50a/DUAL_TRACK_OPERATING_BOARD.md`
