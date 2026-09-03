# V4.12-E50-A2 Causal Alpha Factor Engineering

E50-A2 turns the frozen E50-A0 price universe and E50-A1 corporate-action /
fundamental layer into a point-in-time factor panel. It does not change E16,
E18, E22, or the E45 crisis controller, and it does not select a production
portfolio. Feature-timing and separate-label contracts are HARD_FROZEN.
Numeric factor choices are a new model / new threshold and remain
EXPERIMENTAL until explicitly promoted (`FROZEN_GOVERNANCE.md`).

## Clock contract

- A row dated T contains only information whose `available_date <= T`.
- The row is a T-close signal row. Tradable execution remains T+1 open.
- Forward return labels are stored in a separate file and are forbidden as
  model inputs.
- Financial period-end dates are never used as knowledge dates.
- Corporate-action cash and share multipliers enter the total-return chain on
  their effective date only.
- Duplicate SplitPrice / ParValueChange descriptions of one structural event
  are applied once.
- Unexplained price discontinuities above 50% after the first 20 sessions are
  neutralized in the total-return chain and explicitly flagged for audit.

## Feature families

1. Momentum: 21/63/126/252-day total return and 12-1 momentum.
2. Defensive risk: realized volatility, downside volatility, drawdown and
   Amihud illiquidity.
3. Quality: margins, ROA, ROE, cash-flow quality, accruals and leverage.
4. Growth: quarterly TTM growth, monthly revenue YoY, three-month YoY and
   revenue acceleration.
5. Value research proxies: book, earnings and sales yield using reported
   ordinary-share capital under a TWD10 par assumption. These stay
   research-only until a historical par-value master is complete.

Every raw feature receives a daily cross-sectional percentile where 0 is least
desirable and 1 is most desirable. Family scores are equal-weight averages of
available percentile features; there is no optimized all-factor score in A2.

## Research partitions

- Train diagnostics: 2005-2018.
- Validation diagnostics: 2019-2022.
- 2023 onward is not used to tune A2 feature definitions.

The IC file contains descriptive point estimates only. Overlapping forward
labels require block bootstrap / HAC inference in E50-A3 before any factor can
be promoted.

## Outputs

- `causal_factor_panel.parquet`
- `forward_labels_research_only.parquet`
- `financial_factor_snapshots.parquet`
- `monthly_revenue_factor_snapshots.parquet`
- `univariate_ic_diagnostics.csv`
- `factor_dictionary.json`
- `qc_status.json`

