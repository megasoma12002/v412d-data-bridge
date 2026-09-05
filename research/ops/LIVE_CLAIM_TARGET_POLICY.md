# Live Claim & Target Closure Policy

Date: 2026-09-05  
Status: **BINDING for claims** — Soft-Frozen **[0.50, 0.95] KEEP**  
Authority: `HUMAN_DECISION_REGISTER.md` · `STRATEGY_DEBT_BOARD.md`

## Problem this closes

Research and paper sleeves can print CAGR / MDD numbers. Without a claim policy, those prints are easy to misread as **live strategy achievement**. This file defines what may be claimed on live vs paper.

## What live may claim (only)

| Claim | Allowed? | Basis |
|---|---|---|
| Live stack = E16 Soft-Frozen + Exact T+1 E18 + E22_v2s_tw | **YES** | Production path `forward/e21/` |
| Live Financial clip = **[0.50, 0.95]** | **YES** | Soft-Frozen KEEP |
| Live meets a named CAGR≥X / MDD≤Y target | **NO** | No challenger cut over; Soft-Frozen has no authorized target badge |
| FIN50 / L4 / BLEND_025 is live | **NO** | Paper / observe only |
| Dual-paper PASS / held-out PASS = live promote | **NO** | Explicitly forbidden |

## Paper / research may report (with label)

- Windowed CAGR, MDD, giveback vs BASE on named sleeves  
- Charter screen / sealed diagnostics  
- Month-end PAUSE / ALERT status  

Every paper metric must stay labeled **PAPER** or **RESEARCH** and must not be restated as live performance.

## Target closure rules

1. A **numeric target** (e.g. CAGR / MDD band) is **closed for live** only after:  
   - dedicated cutover checklist all YES, and  
   - merged human cutover PR, and  
   - post-cutover live QC green.  
2. Until then, targets stay **OPEN on research / paper** — missing strategy upgrade, not missing a live badge.  
3. Soft-Frozen KEEP means live’s job is **operate the frozen core**, not claim research targets.

## Current closure map

| Objective | Live | Paper path |
|---|---|---|
| Operable Soft-Frozen core | **CLOSED (KEEP)** | — |
| Lower MDD via L4 DD-path | Not live | OPERATING; cutover DEFER |
| FIN50 static clip upgrade | Not live | REJECT for now (`NOT_READY_SEALED_CAGR`) |
| Sealed-CAGR successor | Not live | BLEND_025 OPERATING OBSERVE |
| Alpha / E45 stitch | Not live | DEFER (needs charter) |

## Forbidden language in ops / CI summaries

- “Target met” / “strategy complete” referring to live without cutover  
- “Promote ready” from a single clean month-end  
- Equating BLEND observe clean with Soft-Frozen replacement  

## Process pointer

How a claim becomes live-eligible (checklist + human cutover PR + post-QC):  
`research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md` Stages 6–8.

## Label

`LIVE_CLAIM_TARGET_POLICY_2026-09-05`
