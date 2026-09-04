# Strategy Debt Board

Date: 2026-09-04 (updated after #35 merge + Stage-8 archive)  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.

## Now / Next / Later / Won’t

### DONE
| Item | Status |
|---|---|
| Gap 6.5 odd-lot TW (`E22_v2s_tw`) | **On main** (#35); default still `E22_v2s` |
| Turnover / held-out diagnosis | **On main**; `MIXED_HELDOUT` |
| Gap5/6 paper stitch / risk budget / board-lot | **On main** |
| HANDOFF / TODO identity | **On main** |
| STOP draft PR archive | **Closed** (#19, #22–#27, #33, #34) |
| **Stage-8 stress-sleeve** | **SATURATED** — archived (`research/e50a/STAGE8_STRESS_SLEEVE_CLOSEOUT.md`); S8B1/S8C1 = `MIXED_HELDOUT` |

### NEXT (single focus)
| Item | Action | Do not |
|---|---|---|
| Option-2 paper monitor | Run S9A1 as **research feed** (runbook in repro); not live capital | Live-wire; retune cuts |
| New stress return engine | New EXPERIMENTAL id / non-TECH2 family — only if continuing alpha | More TECH2 cash/sleeve/freeze grids |
| Optional | Explicit promote default=`E22_v2s_tw` cutover-only | Silent default flip |

### LATER (ops-driven)
| Item | When |
|---|---|
| Receivable / pay-date books (`E22_v3_*`) | Ops needs cash timing |
| Dividend tax named books | After-tax reporting required |
| Board-lot 1000 live | Real order capacity constraint |
| Four-layer combined engine | Only after overlay clears dual held-out + handoff approval |

### WON’T FIX NOW
- Re-run Stage-8 TECH2 cash / multi-sleeve grids  
- Invent E45 MDD −13.16% replacement number  
- Promote experimental 2.5% TO / 0.70 bootstrap to Frozen to “make R1 pass”  
- Live-wire E50-A while `RESEARCH_ONLY` / `MIXED_HELDOUT`  
- Rewrite `forward/e21` historical NAV for backfilled dividends  
- Force board-lot 1000 as formal books (TW 零股 allows 1–999)  

## Identity labels

| Label | Meaning |
|---|---|
| `E21 live` | Forward ledger; E22_v2s from cutover; short sample |
| `E22_v2s` | Formal raw TR (**default**) |
| `E22_v2s_tw` | TW par CIL (named; not default) |
| `E50-A RESEARCH_ONLY` | Standalone sleeve; C4 bull reference + S9A1 paper monitor |
| `E45 NOT_VERIFIED −13.16%` | Challenger; claim has no artifact |

## Gap / alpha snapshot

| Topic | Status |
|---|---|
| #5 overlay | Disconnected; TO fixable on OOF; held-out **MIXED**; Stage-8 **saturated** |
| #6.5 odd-lot | Closed as `E22_v2s_tw` |
| S9A1 | Best directional stress transfer; still MIXED under 0.70 boot; Option-2 paper/monitor |

## Success criteria (current)

1. Stage-8 evidence on main + debt board says **do not re-grid TECH2 controllers**  
2. Next work is Option-2 monitor **or** a **new** stress engine id  
3. Live still has no overlay and no history rewrite  
