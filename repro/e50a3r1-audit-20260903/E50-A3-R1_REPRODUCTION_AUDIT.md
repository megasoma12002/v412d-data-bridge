# E50-A3-R1 Reproduction Audit

Isolated sandbox: `repro/e50a3r1-audit-20260903/`
Date: 2026-09-03
Branch: `cursor/e50a3r1-reproduction-audit-d049`

This run did **not** modify frozen baselines, did **not** overwrite `forward/` or prior research outputs, and did **not** rebuild E50-A0/A1/A2.

## Reproduction Status

**Local A3 + A3-R1 rerun: SUCCESSFUL.**
**Promotion / research gate: NOT PASS (`RESEARCH_ONLY`).**

| Stage | Method | Result |
|---|---|---|
| E50-A0 | Download pinned artifact `33532322856` + SHA-256 verify | QC `PASS`; hashes match artifact QC |
| E50-A1 | Download pinned artifact `33637154310` + SHA-256 compute | QC `PASS`; required files present |
| E50-A2 | Download pinned artifact `33645002188` + SHA-256 verify | QC `PASS`; hashes match artifact QC |
| E50-A3 | Local rerun of `scripts/e50a3_train_exact_open.py` | Engineering QC `PASS`; decision `RESEARCH_ONLY` |
| E50-A3-R1 | Local rerun of `scripts/e50a3r1_repair.py` | Engineering QC `PASS`; decision `RESEARCH_ONLY` |

A3 self-test (`--self-test`) printed `E50-A3 self-test PASS` before training.

A0–A2 were **not rebuilt**. That matches `START_CURSOR.md`: rebuild only after a reproducible upstream defect. No such defect was found in the pinned artifacts.

Bit-identical versus CI on economic artifacts:

- A3 `period_metrics.csv`, `daily_nav.csv`, `trades.csv`, `train_portfolio_grid.csv`, `exact_open_labels_research_only.parquet`
- R1 `period_metrics.csv`, `daily_nav.csv`, `trades.csv`, `train_repair_grid.csv`

Hash differences remaining are float/parquet/timestamp serialization (`qc_status.json`, `frozen_model.json`, `causal_scores.parquet`, CV tables). Coefficients differ only at ~1e-16.

## Reproduced Artifacts

Root: `repro/e50a3r1-audit-20260903/`

### Frozen inputs (downloaded, gitignored because A0 is 1.2GB)

- `inputs/a0/qc_status.json`
- `inputs/a0/point_in_time_universe.csv`
- `inputs/a0/security_master.csv`
- `inputs/a0/delistings.csv`
- `inputs/a0/trading_calendar.csv`
- `inputs/a0/download_manifest.csv`
- `inputs/a1/qc_status.json`
- `inputs/a1/causal_financials.csv.gz`
- `inputs/a1/causal_monthly_revenue.csv.gz`
- `inputs/a1/corporate_action_ledger.csv.gz`
- `inputs/a1/dividend_results_ex_post.csv.gz`
- `inputs/a1/download_manifest.csv`
- `inputs/a2/qc_status.json`
- `inputs/a2/causal_factor_panel.parquet`
- `inputs/a2/forward_labels_research_only.parquet`
- `inputs/a2/financial_factor_snapshots.parquet`
- `inputs/a2/monthly_revenue_factor_snapshots.parquet`
- `inputs/a2/factor_dictionary.json`
- `inputs/a2/univariate_ic_diagnostics.csv`

### Local A3 outputs

- `outputs/a3/qc_status.json`
- `outputs/a3/frozen_model.json`
- `outputs/a3/cv_model_selection.csv`
- `outputs/a3/train_portfolio_grid.csv`
- `outputs/a3/period_metrics.csv`
- `outputs/a3/daily_nav.csv`
- `outputs/a3/trades.csv`
- `outputs/a3/causal_scores.parquet`
- `outputs/a3/exact_open_labels_research_only.parquet`

### Local R1 outputs

- `outputs/a3r1/qc_status.json`
- `outputs/a3r1/frozen_repair_model.json`
- `outputs/a3r1/model_cv.csv`
- `outputs/a3r1/train_repair_grid.csv`
- `outputs/a3r1/period_metrics.csv`
- `outputs/a3r1/daily_nav.csv`
- `outputs/a3r1/trades.csv`
- `outputs/a3r1/causal_scores.parquet`

### Audit reports

- `reports/dataset_manifest.json`
- `reports/file_hashes.json`
- `reports/period_definitions.json`
- `reports/ci_vs_local_hash_diff.json`
- `reports/leakage_audit.json`
- `reports/exposure_turnover_summary.json`
- `reports/exact_t1_trace_samples.csv`

## Missing Inputs

None for the pinned A3/R1 command set.

Not present in the A0 artifact, and **not guessed**:

- Adjusted-price shards (`adjusted_rows = 0`). Archive ingestion path stores raw OHLCV only. A2/A3 total-return uses raw open/close plus the A1 corporate-action ledger. This is the frozen A0 contract, not a missing A3 input.
- A0 per-security FinMind download shards (replaced by `ALL_MARKET_ARCHIVE`).
- A1 raw per-code shards inside the aggregate artifact (normalized tables are present and are what A2/A3 consume).

## Failed Stages

No stage failed to reproduce.

R1 **promotion gate did not pass**, by design of the current code:

- `turnover_feasible_candidates = 0`
- `turnover_constraint_satisfied = false` (2.5% daily turnover ceiling)
- Validation 2019–2022 CAGR 14.95% **below** PIT market-proxy CAGR 20.97%
- Validation block-bootstrap positive-excess probability 0.2614 < 0.70
- Sealed 2023–latest looks strong (CAGR 48.01%, bootstrap 0.9986) but cannot promote while validation fails and turnover is infeasible

Decision recorded in `outputs/a3r1/qc_status.json`: `RESEARCH_ONLY`.

## Exact T+1 Verification

Evidence from local R1 `trades.csv` joined to A0 raw opens:

- Same-bar fills (`execution_date <= signal_date`): **0 / 8461**
- A3 same-bar fills: **0 / 8663**
- Synthetic clock self-test: **PASS**
- Sample chain (R1 validation): `2019-01-02` signal on `2313` → order → `2019-01-03` raw open `19.95` fill → position/NAV
- Sample chain (R1 sealed): `2023-01-03` signal on `1101` → `2023-01-04` raw open `33.65`
- SELL `2371` on `2023-01-10` → fill `2023-01-11` even though `alpha_universe=false` on both dates: existing position is marked from A0, not dropped by a future-aware universe freeze

Calendar-day lags of 12–13 days cluster on `2019-01-30`, `2023-01-17`, `2025-01-22` (Lunar New Year). Execution uses the **next complete market session**, not next calendar day. This is consistent with Exact T+1, not same-bar trading.

Unavailable-open policy is active: R1 `stale_positions_max = 1` (position held when that name has no raw open).

Costs used (frozen in A3 code, not retuned): buy 14.25bp, sell 14.25bp, stock tax 30bp, 5bp slippage each side.

## Leakage Verification

| Check | Result | Evidence |
|---|---|---|
| Same-bar execution | **Not found** | 0 clock violations in A3 and R1 trades |
| Future-aware universe | **Not found in A0 flags** | `alpha_universe` never true on/after `delisting_date`; 0 alpha rows with `listed_and_trading=false` |
| Full-sample normalization | **Not found** | A2 ranks are cross-sectional `over("date")` only (`factor_dictionary.json`) |
| Label leakage | **Not found** | Panel has no `fwd_*` / `target_rank` / exact-open label columns; A3 `forbidden_feature_columns=[]` |
| Corporate-action leakage into features | **Not found as pre-event signal** | A2 joins fundamentals by `available_date <= signal date`; CA cash/share enter returns on `effective_date` |
| Train/test contamination | **Not found in fit cutoffs** | Validation fit through `2018-11-30`; sealed through `2022-12-01`; R1 selection is 2011–2018 OOF only |
| Survivorship bias | **Anti-survivorship present** | 2,259 ever-traded codes in A0; delistings retained; first tradable date inferred from first raw observation |
| Hidden leverage | **Not found** | Gross exposure ≤ 1.000; 0 days with exposure > 1.001; cash never materially negative |

Residual data issues (documented, not patched):

1. **30 A1 dividend rows** have `available_date > effective_date` (announcement on/after ex-date; 15 cash + 15 stock). Returns still apply on `effective_date`. This is late vendor timing, not future-price leakage. Count is 30 / 23,524 CA rows.
2. A0 `adjusted_rows = 0` (archive path). Ranking/execution do not use a vendor adjusted-price file.
3. FinMind industry master is a current snapshot; 30,162 panel rows have null/`historical_unknown` industry. R1 selected `neutralization=NONE`, so this did not enter the chosen score.
4. A0 skipped 85,738 malformed archive rows during ingestion (`archive_ingestion.rows_skipped`).

## Metrics Verification

Local R1 metrics **byte-match** CI run `33713890731`:

| Portfolio | Start | End | CAGR | Max DD | Avg daily turnover | Total cost | Trades |
|---|---|---|---|---|---|---|---|
| VALIDATION_2019_2022 | 2019-01-02 | 2022-12-30 | 14.95% | -33.50% | 7.05% | 0.358 | 4562 |
| VALIDATION market proxy | 2019-01-02 | 2022-12-30 | 20.97% | -29.58% | 0 | 0 | 0 |
| SEALED_2023_LATEST | 2023-01-03 | 2026-08-28 | 48.01% | -32.51% | 4.68% | 0.253 | 3899 |
| SEALED market proxy | 2023-01-03 | 2026-08-28 | 20.99% | -25.59% | 0 | 0 | 0 |

Local A3 metrics **byte-match** CI run `33680157521` and the hardcoded R1 `BASELINE` block:

| Portfolio | CAGR | Max DD | Avg daily turnover | Total cost |
|---|---|---|---|---|
| A3 VALIDATION_2019_2022 | 1.44% | -27.94% | 6.53% | 0.256 |
| A3 SEALED_2023_LATEST | 22.26% | -21.37% | 7.21% | 0.280 |

R1 selected config (train-only): `TECH2` + `BREADTH_REGIME` + `lambda=1.0` + `top_k=20` + `rebalance_every=5` + `exit_multiple=2.0` + `neutralization=NONE` + `industry_cap=5`.

Exposure (R1 NAV): mean gross ~0.999, max 1.000, mean daily turnover 5.93%, max daily turnover 1.99 on a rebalance day (not leverage).

## Differences vs Handoff Claims

| Handoff claim | Reproduction evidence |
|---|---|
| A0 2004-02-11 ~ 2026-08-28 | **Match** (`2004-02-11` to `2026-08-28`) |
| 5,551 trading days | **Match** (`universe_dates=5551`) |
| 2,259 ever-traded stocks | **Match** |
| 7,943,783 raw OHLCV rows | **Match** |
| 795,000 PIT eligible rows | **Match** (`alpha_eligible_rows=795000`) |
| duplicate keys = 0 | **Match** (0 duplicate `date,code`) |
| OHLC anomalies = 0 | **Match** (`invalid_ohlc_rows=0`) |
| download failures = 0 | **Match** |
| adjusted_rows was 0 | **Match** (`adjusted_rows=0`) |
| A2 ~795,000 rows / 1,347 stocks / ~5,300 days | **Match** (795000 / 1347 / 5300) |
| E45 MDD ≈ -13.16% | **Not verified here**. A3/R1 explicitly do not apply E45. No E45 NAV artifact was consumed. |
| A3 is current research with tradable OOS alpha | A3 engineering clock **PASS**, but validation **loses** to the PIT market proxy; decision `RESEARCH_ONLY` |
| R1 repairs A3 without reading 2019–2022 during selection | **Match** by code path; validation is evaluated after selection |
| R1 turnover ceiling 2.5% | **Match**, and **no candidate satisfied it** |

## Frozen Baseline Integrity

Unchanged in this experiment:

- No edits to `scripts/e50a0_build_point_in_time.py`, A1, A2, A3, or R1 trainers
- No edits to E16 / E18 / E21 forward ledgers
- No edits to E22 dividend files
- No edits to E45 / E1 / E11 crisis modules
- No 0050 leveraged ETF introduced
- A3/R1 still treat E50-A as a research overlay and leave E45 untouched (`risk_controller: E45 not applied in R1`)

Pinned A0/A1/A2 artifact hashes were verified before the A3/R1 rerun. Outputs were written only under `repro/e50a3r1-audit-20260903/outputs/`.

## Recommended Next Step

Do **not** tune CAGR yet.

Smallest safe follow-up, still as a challenger experiment (new output folder, no baseline overwrite):

1. Keep the frozen A0/A1/A2 artifacts and Exact T+1 simulator.
2. Investigate why **every** R1 portfolio-grid candidate exceeds 2.5% average daily turnover on 2011–2018 OOF (`turnover_feasible_candidates=0`).
3. Add diagnostics only: turnover-by-rebalance, name-level hold period, and a **longer rebalance / stricter buffer** grid that remains selected on 2011–2018 OOF.
4. Re-evaluate 2019–2022 and 2023-latest **after** a feasible candidate exists.
5. Do not integrate E45 until R1 (or R2) beats the PIT market proxy after costs on **both** held-out windows with bootstrap ≥ 0.70.

Stop condition already hit for performance work: R1 is reproducible but **not promotion-eligible**. Next work is a turnover-feasibility experiment, not model shopping on sealed data.
