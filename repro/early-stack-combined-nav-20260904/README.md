# Early-Stack Combined NAV Challenger (2026-09-04)

**EXPERIMENTAL.** Does **not** edit or promote SOFT_FROZEN E16 / E18 / E22 / E45.

## Named E45 module (new)

- Code: `scripts/e45_crisis_core.py`
- Status doc: `research/e45/E45_MODULE_STATUS.md`
- Machine status: `research/e45/e45_status.json`
- Label: **`CHALLENGER_CANDIDATE_NOT_PROMOTED`**
- Claimed MDD −13.16%: still **UNVERIFIED**

## Headline results (2012-12 → 2026-09)

| Variant | CAGR | MDD | Mean E45 exp |
|---|---:|---:|---:|
| E16_E18 | 7.22% | −22.77% | 1.00 |
| E16_E18_E22 | **11.19%** | −22.11% | 1.00 |
| E16_E18_E22_E45LEGACY | 10.39% | −20.13% | 0.96 |
| E16_E18_E22_E45_E3 | 8.59% | **−20.53%** | 0.91 |
| E16_E18_E22_E45_E1 | 10.67% | −22.11% | 0.99 |

E22 ≈ **+4 pp CAGR**. Named E45-E3 improves MDD vs E22 but is **not** promoted.

## Run

```bash
python3 scripts/e50_early_stack_combined_nav.py \
  --market forward/e21/live_market.csv \
  --dividends data/dividend_events/e22_dividend_events.csv \
  --out repro/early-stack-combined-nav-20260904
```

## Explicit non-actions

- No overwrite of `forward/e21/` ledgers
- No self-promotion of E45 to `SOFT_FROZEN_CRITICAL`
- Formal strategy remains **V4.12-D** until governance approval
