# Early-Stack Combined NAV Challenger (2026-09-04)

**EXPERIMENTAL.** Does **not** edit or promote SOFT_FROZEN E16 / E18 / E22 / E45 / E50-A.

## Named E45 module

- Code: `scripts/e45_crisis_core.py`
- Status: **`CHALLENGER_CANDIDATE_NOT_PROMOTED`**
- Docs: `research/e45/E45_MODULE_STATUS.md`

## Core stack (full history)

| Variant | CAGR | MDD |
|---|---:|---:|
| E16_E18 | 7.22% | −22.77% |
| E16_E18_E22 | **11.19%** | −22.11% |
| + E45_E3 | 8.59% | −20.53% |

## Four-layer book (2019–2026 overlap)

Script: `scripts/e50_four_layer_combined_nav.py`  
Doc: `FOUR_LAYER_COMBINED_NAV.md`

80% core / 20% A3-R1 alpha, **alpha-cut-first** when named E45 exposure < 1:

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| CORE_ONLY | 15.04% | −22.11% | 0.0399 |
| ALPHA_ONLY | 19.62% | −50.25% | −0.0551 |
| MIX_STATIC_80_20 | **16.80%** | −23.62% | **0.0499** |
| MIX_ALPHA_CUT_FIRST | 15.54% | −23.13% | 0.0397 |
| FULL_CORE_E45_PLUS_ALPHA_CUT | 11.64% | −21.75% | 0.0076 |

Finding: static 80/20 beats core util; alpha alone is too deep-drawdown; named E45 on core is costly on this window.

## Run

```bash
python3 scripts/e50_early_stack_combined_nav.py \
  --market forward/e21/live_market.csv \
  --dividends data/dividend_events/e22_dividend_events.csv \
  --out repro/early-stack-combined-nav-20260904

python3 scripts/e50_four_layer_combined_nav.py \
  --out repro/early-stack-combined-nav-20260904
```
