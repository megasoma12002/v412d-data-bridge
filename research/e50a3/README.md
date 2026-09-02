# V4.12-E50-A3 Causal Alpha + Exact T+1 Open

E50-A3 trains the first auditable cross-sectional alpha baseline on the frozen
E50-A2 point-in-time panel and marks every holding with the complete E50-A0 raw
price history before executing with raw T+1 opens. It is a research
gate, not an authorization to trade or a promise of 20% annual returns.

## Frozen clocks

- Features on row T must be known by T close.
- Forward labels stay in a physically separate file and enter only training.
- A T signal maps once, and only once, to the next market session's raw open.
- If a selected stock has no raw open, the order does not fill. The simulator
  does not replace it with a stock selected using future information.
- A stock that temporarily leaves the E50-A2 alpha universe is still marked
  from E50-A0. Alpha-universe membership never freezes an existing position.
- A date with fewer than 75% of its trailing 21-session median quote count is
  treated as an incomplete source snapshot, not a valid market session. Price
  continuity is carried directly to the next complete session.
- Cash dividends and share multipliers enter open-to-open holding returns on
  their effective dates. Duplicate split/par-value descriptions are applied once.

## Model selection

- Model family: transparent cross-sectional ridge regression.
- Targets: daily percentile of the exact raw-open total return from T+1 open
  through 21 market sessions after entry. Corporate actions are included.
- Candidate feature families and ridge penalties are selected only with
  embargoed 2011-2018 walk-forward folds.
- Historical par-value-based value proxies are excluded.
- Portfolio breadth/rebalance interval is selected only from train OOF scores,
  using `CAGR - 0.50 * abs(max drawdown)`.
- Validation is 2019-2022 with the model fit only through the 22-session
  pre-validation cutoff.
- 2023-latest is sealed evaluation; hyperparameters remain frozen.

## Execution assumptions

- Equal-weight long-only portfolio; train selects 20/30/50 names.
- Minimum known T trading value: NT$20 million.
- Buy commission 14.25bp, sell commission 14.25bp, stock transaction tax
  30bp, and 5bp slippage on each side.
- Unexplained >50% price jumps identified in E50-A2 are excluded from orders
  and neutralized in holding-return continuity.

E45 is deliberately not applied here. The next gate, E50-A4, must test the
frozen A3 attack sleeve under the E45 crisis multiplier without retuning A3.

## Outputs

- `qc_status.json`
- `frozen_model.json`
- `cv_model_selection.csv`
- `train_portfolio_grid.csv`
- `period_metrics.csv`
- `daily_nav.csv`
- `trades.csv`
- `causal_scores.parquet`
- `exact_open_labels_research_only.parquet`
