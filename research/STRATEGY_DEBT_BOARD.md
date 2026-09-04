# Strategy Debt Board

Date: 2026-09-04  
Branch intent: consolidate closeouts + operating plan (this PR).  
Live rule: **E16 + E18 + E22_v2s cutover-only**. No overlay. No history rewrite.

## Now / Next / Later / Won’t

### NOW (this closeout)
| Item | Action | Status |
|---|---|---|
| Gap 6.5 odd-lot TW | Land `E22_v2s_tw` (par NT$10 CIL); default stays `E22_v2s` | **IN THIS PR** |
| Gap #5 diagnosis | Archive turnover/held-out closeout (`MIXED_HELDOUT`) | **IN THIS PR** |
| Gap #5/#6 paper | Archive paper stitch / risk budget / board-lot re-sim | **IN THIS PR** |
| Doc identity | Fix HANDOFF / TODO stale “E22 not in E21” / MDD claim | **IN THIS PR** |
| STOP draft PRs | Close archive noise (#22–#27 class) | **PROCESS** |

### NEXT (single research focus)
| Item | Action | Do not |
|---|---|---|
| Alpha failure regime | Stage-8A/B stress-sleeve path (OOF then one held-out) | Reb micro-grids; sealed peek; live-wire |
| Optional promote | Explicit PR to set default=`E22_v2s_tw` cutover-only | Silent default flip |

### LATER (ops-driven)
| Item | When |
|---|---|
| Receivable / pay-date books (`E22_v3_*`) | Ops needs cash timing |
| Dividend tax named books | After-tax reporting required |
| Board-lot 1000 live | Real order capacity constraint |
| Four-layer combined engine | Only after overlay clears dual held-out + handoff approval |

### WON’T FIX NOW
- Invent E45 MDD −13.16% replacement number  
- Promote experimental 2.5% TO / 0.70 bootstrap to Frozen to “make R1 pass”  
- Live-wire E50-A while `RESEARCH_ONLY` / `MIXED_HELDOUT`  
- Rewrite `forward/e21` historical NAV for backfilled dividends  
- Force board-lot 1000 as formal books (TW 零股 allows 1–999)  
- Model 拼湊 window / 劃撥費充抵 as portfolio alpha  

## Identity labels (use these)

| Label | Meaning |
|---|---|
| `E21 live` | Forward ledger; E22_v2s from cutover; short sample |
| `E22_v2` | Cash-only baseline research |
| `E22_v2s` | Formal raw TR + float stock shares (**default**) |
| `E22_v2s_tw` | TW practice floor + par CIL (named; not default) |
| `E50-A RESEARCH_ONLY` | Standalone sleeve; not live capital |
| `E45 NOT_VERIFIED −13.16%` | Challenger module; claim has no artifact |

## Gap status snapshot

| Gap | Status |
|---|---|
| #5 overlay | Correctly disconnected; TO repairable on OOF; held-out **MIXED**; no live wire |
| #6.4/#6.7 stock books | E22_v2s on main cutover |
| #6.5 odd-lot | Closed as `E22_v2s_tw` named |
| #6.1–6.3 / #6.6 | Deferred (won’t now) |
| E45 −13.16% | `NOT_VERIFIED` |

## Success criteria

1. This PR merged → debt board + closeouts on `main`  
2. STOP drafts archived  
3. Next agent work = **Alpha stress-sleeve only** (or explicit TW default promote)  
4. Live still has no overlay and no history rewrite  
