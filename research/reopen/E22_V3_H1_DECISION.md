# E22_v3 H1 Decision — Payment Date Challenger

Date: **2026-09-04**  
Sandbox: `repro/e22-v3-h1-20260904/`  
Script: `scripts/research_e22_v3_h1.py`  
Baseline preserved: **`E22_v2_CASH_EX_OFFICIAL_PATH`**

## Context

Round-1 flagged payment-date H1 as data-gapped; Round-2 kept ex-date with incomplete early `cash_payment_date`.  
After Yahoo TW backfill, coverage is **144/144 (100%)** — this rerun is the fair H1 test.

## Pre-registered bar

- Util(pay) > Util(ex) + **0.002**
- |MDD(pay)| ≤ |MDD(ex)| + **0.005**
- Exact T+1 must hold

## Result

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| EX_DATE_TAX0 (v2 rule) | 11.25% | −22.11% | 0.001941 |
| PAY_DATE_TAX0 (H1) | 11.51% | −22.18% | 0.004151 |
| Δ | +0.26 pp | −0.07 pp worse | **+0.00221** |

- `pay_beats_ex` = **True** (clears bar; util margin is thin)
- Exact T+1 = **True** on all books
- Dividend cash credited: pay 2.84M vs ex 2.61M (timing / share interaction)

## Decision

**`H1_PAY_DATE_INTERESTING_CONTINUE_SANDBOX`**

| Action | Status |
|---|---|
| Auto-promote to replace E22_v2 | **No** |
| Edit `forward/e22_v2/` | **Forbidden** |
| Next if governance wants | Paper `forward/e22_v3_challenger/` + explicit approval phrase for `E22_v3_CASH_PAY_*` |
| Default ops | Keep running **E22_v2 ex-date** daily |

## Why not promote yet

1. Util lift only ~0.00221 over a 0.002 bar — fragile to cost / sample tweaks.  
2. MDD is slightly worse (still within epsilon).  
3. Delegated no-promotion posture still applies until explicit approval.  
4. Tax haircuts (H2) destroy util for both clocks — cash credit assumption remains optimistic.
