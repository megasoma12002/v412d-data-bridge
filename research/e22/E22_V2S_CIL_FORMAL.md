# E22_v2s_cil — Floor Shares + Cash-in-Lieu (Gap 6.5)

Generated: `2026-09-04T18:19:32.453813+00:00`

**Named books version.** Does **not** rewrite live history. Default remains `E22_v2s` until explicit promotion.

## Rule

On `stock_ex_date` (raw books; never adj_close NAV + shares):

1. `shares_gross = shares × (1 + stock_dividend/10)`
2. `shares = floor(shares_gross)`
3. `cash += (shares_gross − shares) × raw_close`

Cash dividends unchanged (`cash_ex_date`). Exact T+1 unchanged.

## Side-by-side historical recompute

| Variant | CAGR | MDD | End NAV | CIL cash | End frac dust |
|---|---:|---:|---:|---:|---:|
| E22_v2 | 11.25% | -22.11% | 12,375,276 | 0.00 | 0.0000 |
| E22_v2s | 13.78% | -22.64% | 16,695,202 | 0.00 | 2.1956 |
| E22_v2s_cil | 13.78% | -22.64% | 16,694,167 | 391.86 | 0.0000 |

### Deltas (cil − v2s)

- CAGR: `-0.0005` pp
- MDD: `0.0017` pp
- End NAV: `-1,034.50` (ratio `0.9999380361621277`)
- Fractional shares cashed: `17.9338`
- End fractional dust: v2s `2.1956` → cil `0.0000`

## Decision

- Gap 6.5: `NAMED_VERSION_LANDED`
- Live default: `KEEP_E22_v2s_UNTIL_EXPLICIT_PROMOTE`
- Promote CIL: `RECOMMENDED_CANDIDATE_DELTA_NEGLIGIBLE`
- Live history: `DO_NOT_REWRITE`
- Board-lot / pay-date / tax: still out of scope here

## Code

- `scripts/e22_dividend_accounting.py` — `E22_v2s_cil`
- `scripts/e50_early_stack_combined_nav.py` — passes raw close mark prices
- `scripts/e21_forward_pipeline.py` — `--e22-version E22_v2s_cil` selectable (not default)

## Artifacts

- `research/e22/E22_V2S_CIL_FORMAL.json`
- `repro/e22-v2s-cil-historical-recompute/`

