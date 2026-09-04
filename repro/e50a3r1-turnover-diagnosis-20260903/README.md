# E50-A3-R1 Turnover Diagnosis + Challenger Rounds

Active experimental research branch. Keep as **draft**.

## Round status

| Challenger | Config | OOF | Held-out |
|---|---|---|---|
| C1 | top_k=20 reb=42 exit=2.0 | dual PASS | MIXED (val turn FAIL, boot FAIL) |
| C2 | top_k=20 reb=42 exit=2.5 | dual PASS | MIXED (val turn PASS 2.43%, boot FAIL 0.51) |
| **C3** | **top_k=25** reb=42 exit=2.0 | dual PASS (boot **0.808**) | **MIXED** (val turn 2.53% FAIL, boot **0.37** FAIL, proxy FAIL) |

C3 selected OOF-only with bootstrap-first rule. Did **not** improve held-out bootstrap vs C2.
Exact T+1 intact. No promotion. E45 untouched.

### C3 held-out snapshot
- Val: CAGR 18.6%, MDD -29.9%, turn 2.53%, boot 0.372, beats_proxy=False
- Sealed: CAGR 51.5%, MDD -26.6%, turn 1.77%, boot 1.000

## Next research note

OOF bootstrap margin did not transfer to 2019–2022. Next challenger (C4) needs a **different hypothesis** (not more book-size chasing OOF bootstrap), still selected on OOF only; do not retune C1/C2/C3 from held-out.

## Reports
- `E50-A3-R1-C3_HELDOUT.md`
- `E50-A3-R1-ROUND3_OOF.md`
- `reports/round3_oof_summary.json` / `c3_heldout_decision.json`
