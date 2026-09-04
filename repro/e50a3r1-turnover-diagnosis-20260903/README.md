# E50-A3-R1 Turnover Diagnosis + Challenger Rounds

Active experimental research branch (`cursor/e50a3r1-turnover-diagnosis-d049`). Keep as **draft**.

## Round status

| Challenger | OOF dual-gate | Held-out label | Notes |
|---|---|---|---|
| **C1** `top_k=20 reb=42 exit=2.0` | PASS | **MIXED_HELDOUT** | Val turnover FAIL (2.69%), bootstrap FAIL |
| **C2** `top_k=20 reb=42 exit=2.5` | PASS | **MIXED_HELDOUT** | Val turnover PASS (2.43%), bootstrap still FAIL (0.51) |

C2 selected on 2011–2018 OOF only (new challenger; C1 not retuned).
Exact T+1 intact. E45 untouched. No promotion.

## Locked C2

```
TECH2 / BREADTH_REGIME / lambda=1.0
top_k=20
rebalance_every=42
exit_multiple=2.5
neutralization=NONE
industry_cap=5
```

## Reports

- `E50-A3-R1-C2_HELDOUT.md` — Round-2 held-out
- `E50-A3-R1_HELDOUT_DETAILED.md` — C1 detailed held-out
- `E50-A3-R1_TURNOVER_DIAGNOSIS.md` — OOF turnover diagnosis
- `reports/round2_oof_summary.json`
- `reports/c2_heldout_decision.json`
