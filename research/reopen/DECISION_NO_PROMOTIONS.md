# Delegated Promotion Decision — No Upgrades

Date: **2026-09-04**  
Authority: user directive **「交給你決定是否升級」**  
Decider: research agent (evidence-bound)  
Status: **`NO_PROMOTIONS`**

## Verdict

**不升級任何正式版本。**  
Research may continue under challenger charters; production stack stays as-is.

| Track | Promote? | Binding decision |
|---|---|---|
| **E45 → E45_v1 (E3)** | **NO** | Keep **B** — V4.12-D remains crisis baseline |
| **E22_v3** | **NO** | Keep **E22_v2**; v3 stays sandbox |
| **E16 / E18 variants** | **NO** | Variants registered only; not run / not promoted |
| **Alpha 3A model** | **NO** | Features not built; nothing to freeze |
| **G4 hedge sleeve** | **NO** | H1/H2 illustrative only; no production hedge |

## E45 rationale (primary call)

Validation (original v412e0):

| | D | E3 |
|---|---:|---:|
| Return | 52.7% | 38.6% (**~73% of D**, fails ≥80% floor) |
| MDD | −24.1% | −20.2% (better) |
| Sharpe | 0.81 | 0.76 (fails ≥ D) |

Why not promote despite better MDD:

1. E45 is **SOFT_FROZEN_CRITICAL** — higher bar, not “MDD-only wins”.  
2. Pre-registered return/Sharpe floors **failed on both PIT and original panels**.  
3. Promoting now would be **lowering the bar after seeing results**.  
4. Named `e45_crisis_core.py` already usable as API for paper alpha-cut; formal crisis engine stays **D**.

Phrase **not** issued: `APPROVE E45_v1_E3_LOCKED_ACCEPT_RETURN_TRADEOFF`.

## Other tracks (brief)

- **E22_v3:** payment-date sim not matured; tax haircut only illustrative; v2 just went live.  
- **E16/E18:** no completed side-by-side yet.  
- **3A:** menu only — promoting without a held-out model would violate protocol.  
- **G4:** toy antithetic ≠ tradable hedge book.

## What stays official

```
E16 + E18  → forward/e21 (preserved)
E22_v2     → forward/e22_v2  (SOFT_FROZEN)
E45        → not promoted; V4.12-D formal
Alpha      → paper/monitor (3B old panel; 3A research only)
Hedge      → none in production
```

## What research may still do

Continue Round-2+ challengers under `research/reopen/*` **without** claiming SOFT_FROZEN.  
Any future upgrade still needs a **new** explicit approval after PASS evidence.

## Decision id

`DECISION_NO_PROMOTIONS_20260904`
