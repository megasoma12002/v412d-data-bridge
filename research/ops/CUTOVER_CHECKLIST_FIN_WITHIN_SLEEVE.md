# Cutover checklist — FIN within-sleeve

Date: 2026-09-09  
Status: **DRAFTED — NOT AUTHORIZED**  
Human ballot required: dedicated **`ACCEPT live FIN within-sleeve cutover: <POLICY>`**  
Soft-Frozen live Financial clip: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live capital: **500M** (ACCEPT ballot; PR pending merge if not yet on main)  
Board-lot: **1000 KEEP**  
E45 stitch: **FORBIDDEN** (separate agenda)

Authority: `FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md` · `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md` · `FIN_WITHIN_SLEEVE_ALLOC_DECISION_PACK.md` · `HUMAN_DECISION_REGISTER.md`  
Ballot draft: `FIN_WITHIN_SLEEVE_CUTOVER_BALLOT_DRAFT.md`

This file satisfies **“cutover checklist drafted.”**  
It does **not** authorize live-wire, Soft-Frozen flip, or `e21` within-sleeve change.

## What cutover would change (future human PR only)

- Replace live Financial **within-sleeve equal-split** with the **chosen** paper policy:
  - **`MIX_L75`** = `FIN_MIX_EQUAL_RS_EXDIV` λ=0.75, or
  - **`KD_OPT`** = `FIN_PRE_EXDIV_KD` (`KD_APR15_MAY15_Klt30_T15`), or
  - **`FIN_RS_SOFT_TILT_EXDIV`** (only if tip PAUSE is explicitly accepted)
- Soft-Frozen sleeve **weights / clips** unchanged unless a **separate** clip PR  
- DEFAULT books stay **`E22_v2s_tw`** unless a **separate** books PR  
- Telecom within-sleeve stays **EQUAL** (isolate FIN line)  
- Forward-only; no silent Soft-Frozen edit; no invent MDD narrative

## Candidate tip snapshot (paper, asof 2026-09-08)

| Book | YTD giveback | 1y giveback | Tip | Held-out score |
|---|---:|---:|---|---:|
| `FIN_RS_SOFT_TILT_EXDIV` | ~6.3 pp | ~6.7 pp | **PAUSE** | ~+0.53 |
| `MIX_L75` | ~2.1 pp | ~2.3 pp | **PASS** | ~+0.13 |
| `KD_OPT` | ~1.3 pp | ~1.6 pp | **PASS** | ~+0.65 |

Source: `FIN_WITHIN_SLEEVE_MONTH_END_MONITOR.json` / dual-paper observe (KD_OPT via observe PR if not yet on main).  
Re-run before any ACCEPT — numbers freeze at ballot time.

## Gates (all required before ACCEPT)

| # | Gate | Current (2026-09-09) | Pass? |
|---|---|---|---|
| 1 | Charter **ACCEPT** + Stage B **STOP** + Stage C **LOCKED** | Decision pack | **YES** |
| 2 | Stage D multi-paper **OPERATING OBSERVE** | EQUAL ∥ RS ∥ MIX_L75 (+ KD_OPT when merged) | **YES** / **WATCH** KD merge |
| 3 | Human **chooses exactly one** cutover policy | Not chosen | **NO** |
| 4 | Chosen policy tip YTD + trailing_1y **PASS** (giveback ≤3 pp; no PAUSE) | MIX / KD PASS; RS PAUSE | **YES** if MIX or KD |
| 5 | Chosen policy held-out score **> 0** vs `FIN_EQUAL` | MIX ~+0.13; KD ~+0.65 | **YES** if MIX or KD |
| 6 | ≥1 **fresh** month-end print after policy choice (same tip PASS) | Need re-run at ballot | **WATCH** |
| 7 | Prefer **sustained** clean trailing (not single print) | One clean tip window so far | **WATCH** |
| 8 | Exact T+1 OK on BASE + chosen book @ charter exec (500M / lot 1000) | Dual-paper harness | **YES** (paper) |
| 9 | Live capital aligned with charter exec (**500M**) | `ACCEPT live capital 500M` | **WATCH** until capital PR merged |
| 10 | Soft-Frozen clip unchanged until separate clip PR | [0.50, 0.95] KEEP | **YES** |
| 11 | DEFAULT books unchanged until separate books PR | `E22_v2s_tw` KEEP | **YES** |
| 12 | Checklist all YES + dedicated cutover PR | This file drafted; ballot **not** cast | **NO** |
| 13 | Must **not** bundle Soft-Frozen flip, E45 stitch, FIN50/L4/BLEND, odd-lot/tax DEFAULT, history rewrite | Policy | Policy |

## Blockers now

1. **No policy choice** — human must pick `MIX_L75` or `KD_OPT` (RS only with explicit tip-PAUSE accept).  
2. **No cutover ACCEPT ballot** cast.  
3. KD_OPT observe + capital-500M may still be open PRs — merge / refresh tip before wire.  
4. Sustained trailing still thin (extend observe if operator wants more month-ends).  
5. Soft-Frozen / DEFAULT / E45 stitch stay out of this PR.

## When gates clear — PR shape (do not pre-merge)

1. Title: `Cutover: live FIN within-sleeve EQUAL → <POLICY>`  
2. Body quotes **this checklist** with all gates YES + fresh `FIN_WITHIN_SLEEVE_MONTH_END_MONITOR.json`  
3. Body names the **exact** policy id + params (λ or KD season/K/T)  
4. Implementation: forward-only wire in `e21` / early-stack Financial sleeve alloc only  
5. Forbidden in that PR: Soft-Frozen retune, E45 stitch, Telecom within-sleeve flip, capital change, books DEFAULT flip, history rewrite  

## Operator loop until then

```bash
python3 scripts/e16_fin_within_sleeve_dual_paper_ledgers.py
python3 scripts/e16_fin_within_sleeve_month_end_monitor.py
# or: python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers
# review research/ops/FIN_WITHIN_SLEEVE_MONTH_END_MONITOR.md
```

## Selection guide (not a cutover license)

| Prefer | When |
|---|---|
| **`MIX_L75`** | Tip-clean + want RS/ex-div mix continuity; smaller MDD lift |
| **`KD_OPT`** | Tip-clean + want larger held-out score (~+0.65) with light CAGR giveback |
| **`FIN_RS_SOFT_TILT_EXDIV`** | Max MDD lift and **explicitly accept tip PAUSE** |
| Stay **`FIN_EQUAL`** | Default until ACCEPT |

## Label

`CUTOVER_CHECKLIST_FIN_WITHIN_SLEEVE__DRAFTED__NOT_AUTHORIZED__2026-09-09`
