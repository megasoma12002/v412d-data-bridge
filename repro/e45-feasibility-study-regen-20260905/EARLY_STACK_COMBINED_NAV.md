# Early-Stack Combined NAV + Named E45 Module

**EXPERIMENTAL.** Named E45 exists but is **not** promoted to SOFT_FROZEN_CRITICAL.

Module: `scripts/e45_crisis_core.py` — `CHALLENGER_CANDIDATE_NOT_PROMOTED`

## Results

| Variant | CAGR | MDD | Util | Mean E45 exp |
|---|---:|---:|---:|---:|
| E16_E18 | 7.29% | -22.77% | -0.0409 | 1.0 |
| E16_E18_E22_V2 | 11.25% | -22.11% | 0.0019 | 1.0 |
| E16_E18_E22 | 13.78% | -22.64% | 0.0246 | 1.0 |
| E16_E18_E22_E45LEGACY | 12.79% | -20.62% | 0.0248 | 0.9621307072515667 |
| E16_E18_E22_E45_E3 | 10.79% | -20.76% | 0.0042 | 0.9067972943914351 |
| E16_E18_E22_E45_E1 | 13.14% | -22.64% | 0.0182 | 0.9935840047746941 |

- E22 CAGR lift: `6.4898%`
- Stock vs cash-only CAGR: `2.5337%`
- Stock div events / shares added: `34` / `78233.0`
- E45-E3 MDD delta vs E22: `1.8804%`
- Claimed MDD -13.16%: `NOT_VERIFIED_HISTORICAL_NARRATIVE`

## Decisions

- `e16_full_history_reconstruction`: DONE_IN_CHALLENGER
- `e22_wired_into_nav_copy`: DONE_IN_CHALLENGER
- `e22_stock_share_increase`: DONE_IN_CHALLENGER_ON_STOCK_EX_DATE
- `e22_v2_official_cash_only_unchanged`: True
- `e45_named_module`: CREATED_CHALLENGER_CANDIDATE
- `e45_promoted_to_soft_frozen_critical`: False
- `e45_mdd_claim_13_16`: NOT_FOUND_IN_ARTIFACTS
- `combined_four_layer_engine`: CORE_EXEC_DIV_PLUS_NAMED_E45_CANDIDATE
- `next`: Named module scripts/e45_crisis_core.py exists and is wired. Stock dividends applied in challenger only. Promote stock-aware E22 only via explicit new version + governance approval.

See `research/e45/E45_MODULE_STATUS.md`.
