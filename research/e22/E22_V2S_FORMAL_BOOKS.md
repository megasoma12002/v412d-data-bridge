# E22_v2s Formal Books

Date: 2026-09-04  
Status: **Formal operating books** for E16/E18/E21 NAV (new version id; does not silently rewrite E22_v2).

## Rule

| Layer | Price | Corporate action |
|---|---|---|
| E16 signals | `adj_close` | none (relative strength only) |
| Books / fills / NAV | raw `open` / `close` | E22_v2s |

### E22_v2s
- Cash: credit on `cash_ex_date`
- Stock: on `stock_ex_date`, `shares *= 1 + stock_dividend/10` (FinMind 元/股, par 10)
- **Forbidden:** mark NAV with `adj_close` and also increase shares

### E22_v2 (preserved)
- Cash only on `cash_ex_date`
- Kept as labeled cash-only baseline (~11.2% CAGR research figure)

## Code

| Path | Role |
|---|---|
| `scripts/e22_dividend_accounting.py` | Canonical books module (`E22_v2` / `E22_v2s`) |
| `scripts/e21_forward_pipeline.py` | Live forward default `--e22-version E22_v2s` |
| `scripts/e50_early_stack_combined_nav.py` | Research sim uses same module |

## Live cutover note

Forward E21 applies dividends **from the cutover day onward** (idempotent keys in `dividends_applied.csv`). Historical live NAV rows are not rewritten. Full-history total-return comparison remains in research (`E22_v2` vs `E22_v2s`).

Historical research recompute (side-by-side, no live rewrite):
- Script: `scripts/e22_v2s_historical_recompute.py`
- Report: `research/e22/E22_V2S_HISTORICAL_RECOMPUTE.md`
- Artifacts: `repro/e22-v2s-historical-recompute/`

## Governance

- E22_v2 cash-only semantics preserved as a named baseline.
- E22_v2s is the formal books path for raw-price NAV (default).
- Candidate successors for fractional shares (gap 6.5):
  - **`E22_v2s_tw`** — Taiwan practice: floor + **par NT$10** CIL (元以下捨去). See `research/e22/TW_ODD_LOT_APPLY.md`.
  - **`E22_v2s_cil`** — research mark: floor + raw-close CIL. See `research/e22/E22_V2S_CIL_FORMAL.md`.
  Neither is default until explicit promotion; no live history rewrite.
- Exact T+1 unchanged.
- Payment-date experiments (E22_v3 H1) remain separate and are not promoted here.
