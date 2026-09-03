# E50-A3-R1 Turnover Diagnosis + Locked Held-Out

Active experimental research branch (`cursor/e50a3r1-turnover-diagnosis-d049`). Keep as **draft**.

## Locked challenger (no retune)

```
TECH2 / BREADTH_REGIME / lambda=1.0
top_k=20
rebalance_every=42
exit_multiple=2.0
neutralization=NONE
industry_cap=5
```

## Decision

**`MIXED_HELDOUT`** — see `E50-A3-R1_HELDOUT_DETAILED.md`.

Validation 2019–2022 fails experimental turnover/bootstrap gates; sealed 2023–latest passes both.
Exact T+1 intact. No promotion. E45 not touched. Frozen baselines unchanged.


## Reports

- `E50-A3-R1_HELDOUT_DETAILED.md` — detailed held-out metrics
- `E50-A3-R1_TURNOVER_DIAGNOSIS.md` — OOF turnover diagnosis
- `reports/heldout_detailed_decision.json`
- `reports/heldout_decision.json`
