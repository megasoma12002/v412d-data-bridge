# Formal Books Charter — Dividend Tax & Receivable / Pay-Date

Date: 2026-09-05  
Status: **CHARTER DRAFTED — RESEARCH / SANDBOX ONLY**  
Soft-Frozen: **[0.50, 0.95] KEEP**  
Formal default today: **`E22_v2s`** with **TAX0** and **cash on ex-date** (no receivable asset)

Authority: `HUMAN_DECISION_REGISTER.md` #6 · Gap #6 brief `research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md` · `STRATEGY_UPDATE_STANDARD_PROCESS.md`

## Problem

Live/formal books simplify custody economics:

| Topic | Formal today | Gap |
|---|---|---|
| Cash dividend clock | Credit on **ex-date** | No receivable; cash early vs custody pay |
| Pay-date | In ledger fields; **not** cash clock | Ops liquidity timing undocumented in NAV |
| Dividend / withholding tax | **TAX0** (pre-tax) | After-tax live books not named |
| Sensitivity | Gap6 KPI haircuts report-only | Must not silently become default |

This charter defines how to promote **named** formal versions — not in-place edits of `E22_v2s`.

## In scope

1. Spec a **receivable / pay-date** books family (sandbox → named version).  
2. Spec a **dividend-tax** books family (named net-of-tax rule).  
3. KPI / dual-book compare vs `E22_v2s` TAX0 ex-date.  
4. Human promote path via checklist + dedicated PR.

## Out of scope / WON’T

- Soft-Frozen flip  
- Rewrite `forward/e21` history  
- In-place change of `E22_v2s` semantics  
- Odd-lot default promote (separate pack)  
- E45 stitch  
- Sell-side 證交稅 redesign (already separate)  
- Auto-promote from Gap6 KPI prints  

## Proposed named versions (draft — not implemented as default)

| Version id | Rule sketch | Role |
|---|---|---|
| `E22_v2s` | Cash on ex; TAX0; float stock | **Current formal default** |
| `E22_v3_recv_pay` | Receivable on ex; cash on pay-date; TAX0 | Timing-fidelity candidate |
| `E22_v3_tax10` / `tax20` | Ex-date cash × (1 − w); w∈{0.10,0.20} | After-tax sensitivity → pick one if promote |
| `E22_v3_recv_pay_taxW` | Receivable + chosen withholding | Combined (only after each axis alone is clear) |

Exact field schemas and idempotent `dividends_applied` keys land in implementation PRs under this charter.

## Pass / fail (research → promote proposal)

| Gate | Pass |
|---|---|
| Identity | New version id; `E22_v2s` behavior bit-identical when selected |
| Exact T+1 | Unchanged |
| Soft-Frozen | KEEP unless separate clip PR |
| Compare artifact | Side-by-side NAV/CAGR/MDD vs v2s on sealed window |
| Tax rule | One written withholding assumption (resident/non-resident explicit) |
| Receivable | Balance-sheet identity: receivable + cash = ex-date credit; clears on pay |
| History | Forward cutover only |

Fail → stay sandbox; do not retune v2s.

## Stage plan

```
A  Label & KPI (DONE-ish via Gap6) 
B  Sandbox dual books under this charter (implementation PR)
C  Human picks one tax rule + whether receivable is wanted
D  Promote checklist (new file) all YES
E  Dedicated human PR flips DEFAULT only if accepted
```

## Human ballot (charter level)

| Ballot | Effect |
|---|---|
| **ACCEPT charter** | Allows Stage B sandbox work; register #6 tax/receivable → RESEARCH OPEN |
| **DEFER charter** | No implementation; keep TAX0 ex-date formal |
| **REJECT** | Close tax/receivable promote path for this cycle |

Promote of any `E22_v3_*` default still needs a **second** human PR after sandbox evidence.

## Label

`FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER_2026-09-05__DRAFTED`
