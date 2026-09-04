# E50-A3-R1 Automatic Research Ledger (C1–C8)

Draft only. No promotion. Exact T+1 intact across rounds. E45 untouched.

## Summary

| ID | Config | Held-out | Val turn | Val boot | Val boot value |
|---|---|---|---|---|---|
| C1 | `k20 reb42 exit2.0` | MIXED | FAIL | FAIL | 0.514 |
| C2 | `k20 reb42 exit2.5` | MIXED | PASS | FAIL | 0.514 |
| C3 | `k25 reb42 exit2.0` | MIXED | FAIL | FAIL | 0.372 |
| C4 | `k22 reb42 exit2.25 gap5 cap5 floor20m` | MIXED_HELDOUT | PASS | FAIL | 0.559 |
| C5 | `k24 reb42 exit2.0 gap0 cap5 floor20m` | MIXED_HELDOUT | FAIL | FAIL | 0.393 |
| C6 | `k20 reb42 exit2.25 gap0 cap4 floor20m` | MIXED_HELDOUT | FAIL | FAIL | 0.503 |
| C7 | `k25 reb42 exit2.0 gap0 cap5 floor40m` | MIXED_HELDOUT | FAIL | FAIL | 0.372 |
| C8 | `k22 reb42 exit2.25 gap10 cap5 floor20m` | MIXED_HELDOUT | PASS | FAIL | 0.554 |

## Findings after 5 auto rounds (C4–C8)

- **0 / 5** reached `PASS_HELDOUT`.
- All sealed windows continued to pass turnover + bootstrap.
- Validation bootstrap remains the hard blocker (~0.37–0.56 vs gate 0.70).
- Best val-bootstrap among auto rounds: **C4 (0.559)** and **C8 (0.554)** — both also **PASS** validation turnover.
- C2/C4/C8 form the only cluster with validation turnover PASS so far.
- Chasing higher OOF bootstrap / liquidity / industry caps did **not** transfer to 2019–2022 excess stability.

## Stop recommendation

Portfolio-rule grid search around TECH2/BREADTH/λ=1.0 is saturating on MIXED_HELDOUT.
Next research (if continued) should change the **alpha/model hypothesis** on OOF only
(not more top_k/reb/exit micro-tunes), or diagnose validation excess failure without retuning locks.

## Artifacts

- `reports/auto_rounds_c4_c8_summary.json`
- `E50-A3-R1-C4_HELDOUT.md` … `E50-A3-R1-C8_HELDOUT.md`
- `outputs/round_c*_oof_grid.csv`
