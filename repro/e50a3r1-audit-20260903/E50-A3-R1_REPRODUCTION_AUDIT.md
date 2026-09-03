# E50-A3-R1 Reproduction Audit

Isolated sandbox: `repro/e50a3r1-audit-20260903/`  
Date: 2026-09-03  
Branch: `cursor/e50a3r1-reproduction-audit-d049`  
PR: https://github.com/megasoma12002/v412d-data-bridge/pull/17

This audit did **not** modify E16, E18/E22, E44, or E45.  
It did **not** retune models.  
It did **not** promote any new threshold, bootstrap cutoff, rebalance rule, or model-selection rule to FROZEN.

Rule-status vocabulary used below:

- **FROZEN** — already frozen in `FROZEN_STRATEGY_SPEC.md` / `CURSOR_RULES.md` before this audit
- **VALIDATED** — reproduced with artifact evidence in this sandbox
- **EXPERIMENTAL** — exists in current A3/R1 research code or is a proposed next experiment; not frozen by this audit
- **PROPOSED** — introduced by this audit as an audit/diagnostic idea; not frozen

A companion table is in `reports/rule_classification.json`.

## Reproduction Status

**A3 + A3-R1 local rerun: VALIDATED.**  
**R1 promotion to E50-A4: not met (`RESEARCH_ONLY`).** That promotion rule is a pre-existing **EXPERIMENTAL** R1 gate, not a new freeze.

| Stage | Method | Result |
|---|---|---|
| E50-A0 | Pinned Actions run `33532322856` + SHA-256 vs artifact QC | Pre-existing A0 QC `PASS`; hashes match |
| E50-A1 | Pinned Actions run `33637154310` | Pre-existing A1 QC `PASS`; A3/R1 inputs present |
| E50-A2 | Pinned Actions run `33645002188` + SHA-256 vs artifact QC | Pre-existing A2 QC `PASS`; hashes match |
| E50-A3 | Local `scripts/e50a3_train_exact_open.py` | Engineering QC `PASS`; decision `RESEARCH_ONLY` |
| E50-A3-R1 | Local `scripts/e50a3r1_repair.py` | Engineering QC `PASS`; decision `RESEARCH_ONLY` |

A3 `--self-test` printed `E50-A3 self-test PASS`.

A0–A2 were downloaded, not rebuilt. That follows the pre-existing `START_CURSOR.md` instruction, not a new freeze.

No required A3/R1 input was guessed. A0 `adjusted_rows = 0` is the pre-existing archive-path contract.

R1 did not fail to run. The pre-existing R1 experimental promotion checks recorded:

- `turnover_feasible_candidates = 0` (2.5% OOF turnover ceiling in `scripts/e50a3r1_repair.py`)
- validation CAGR below the PIT market proxy
- validation bootstrap 0.2614 vs the pre-existing 0.70 experimental cutoff

## Reproduced Artifacts

Root: `repro/e50a3r1-audit-20260903/`

Required audit outputs:

| Requested | Path |
|---|---|
| Dataset manifest | `reports/dataset_manifest.json` |
| File hashes | `reports/file_hashes.json` |
| QC status | `outputs/a3/qc_status.json`, `outputs/a3r1/qc_status.json` |
| Train / validation / test periods | `reports/period_definitions.json` |
| Model config | `outputs/a3/frozen_model.json`, `outputs/a3r1/frozen_repair_model.json` |
| Period metrics | `outputs/a3/period_metrics.csv`, `outputs/a3r1/period_metrics.csv` |
| Trades | `outputs/a3/trades.csv`, `outputs/a3r1/trades.csv` |
| Daily NAV | `outputs/a3/daily_nav.csv`, `outputs/a3r1/daily_nav.csv` |
| Turnover / exposure / costs | `reports/exposure_turnover_summary.json` plus NAV/metrics |
| Exact T+1 samples | `reports/exact_t1_trace_samples.csv` |
| Leakage summary | `reports/leakage_audit.json` |
| Rule classification | `reports/rule_classification.json` |

The filename `frozen_repair_model.json` is the **pre-existing R1 output name** in `scripts/e50a3r1_repair.py`. This audit does not treat that selected R1 config as a newly frozen strategy rule.

Large A0/A1/A2 inputs remain gitignored and are re-downloadable from the pinned run IDs already hardcoded in `.github/workflows/e50a3-exact-open.yml` and `e50a3r1-repair.yml`.

Economic artifacts byte-matched CI:

- A3: `period_metrics.csv`, `daily_nav.csv`, `trades.csv`, `train_portfolio_grid.csv`, `exact_open_labels_research_only.parquet`
- R1: `period_metrics.csv`, `daily_nav.csv`, `trades.csv`, `train_repair_grid.csv`

Remaining hash differences are float/parquet/timestamp serialization only.

## Exact T+1 Verification

Pre-existing clock (FROZEN role, already in E44 / A3 / E21): Information(T) → Signal(T) → next market session raw open.

Reproduced evidence (**VALIDATED** for these A3/R1 trade files):

- Same-bar fills (`execution_date <= signal_date`): **0 / 8,663** A3, **0 / 8,461** R1
- `2019-01-02` signal `2313` → `2019-01-03` raw open `19.95`
- `2023-01-03` signal `1101` → `2023-01-04` raw open `33.65`
- `2023-01-10` SELL `2371` still fills `2023-01-11` while `alpha_universe=false` (A0 mark-to-market of an existing position; pre-existing A3 policy)
- Calendar lags of 12–13 days on `2019-01-30`, `2023-01-17`, `2025-01-22` are next **market** sessions (Lunar New Year), not same-bar fills
- Unavailable-open policy fired: R1 `stale_positions_max = 1`

A3 sleeve cost numbers used in the simulator (buy 14.25bp, sell 14.25bp, tax 30bp, 5bp slippage) **already existed** in `scripts/e50a3_train_exact_open.py`. They are **EXPERIMENTAL** overlay-research assumptions. This audit does not freeze them, and they are distinct from the frozen E18/E22 execution layer.

## Leakage Verification

| Check | Result | Existed before this audit? |
|---|---|---|
| Same-bar execution | Not found (0 violations) | Yes — E44 / A3 clock |
| Future-aware universe | Not found (`alpha_universe` never on/after delisting) | Yes — A0 eligibility flags |
| Full-sample normalization | Not found (ranks `over("date")` only) | Yes — A2 factor dictionary |
| Label leakage | Not found (labels physically separate) | Yes — A2/A3 contract |
| Corporate-action feature leakage | Fundamentals joined on `available_date <= T`; CA returns on `effective_date` | Yes — A1/A2 |
| Train/test contamination | Fit cutoffs `2018-11-30` / `2022-12-01`; R1 selection 2011–2018 OOF | Yes — A3/R1 code |
| Survivorship | 2,259 ever-traded codes; delistings retained | Yes — A0 policy |
| Hidden leverage | Observed gross exposure ≤ 1.0 | Simulator is cash-constrained in pre-existing A3 `simulate()`; the **1.001 diagnostic cutoff is PROPOSED by this audit** |

Residual data notes (not patched, not turned into new frozen rules):

1. 30 / 23,524 A1 dividend rows have `available_date > effective_date` (announcement on/after ex-date).
2. A0 `adjusted_rows = 0` (archive path).
3. 30,162 panel rows have null/`historical_unknown` industry; chosen R1 config used `neutralization=NONE`.
4. A0 skipped 85,738 malformed archive rows.

## Metrics Verification

Local R1 metrics byte-match CI run `33713890731`:

| Portfolio | Start | End | CAGR | Max DD | Avg daily turnover | Total cost | Trades |
|---|---|---|---|---|---|---|---|
| VALIDATION_2019_2022 | 2019-01-02 | 2022-12-30 | 14.95% | -33.50% | 7.05% | 0.358 | 4562 |
| VALIDATION market proxy | 2019-01-02 | 2022-12-30 | 20.97% | -29.58% | 0 | 0 | 0 |
| SEALED_2023_LATEST | 2023-01-03 | 2026-08-28 | 48.01% | -32.51% | 4.68% | 0.253 | 3899 |
| SEALED market proxy | 2023-01-03 | 2026-08-28 | 20.99% | -25.59% | 0 | 0 | 0 |

Local A3 metrics byte-match CI run `33680157521` (also hardcoded as R1 `BASELINE`):

| Portfolio | CAGR | Max DD | Avg daily turnover | Total cost |
|---|---|---|---|---|
| A3 VALIDATION_2019_2022 | 1.44% | -27.94% | 6.53% | 0.256 |
| A3 SEALED_2023_LATEST | 22.26% | -21.37% | 7.21% | 0.280 |

R1 **selected** config under the pre-existing train-only search (EXPERIMENTAL, not frozen by this audit): `TECH2`, `BREADTH_REGIME`, `lambda=1.0`, `top_k=20`, `rebalance_every=5`, `exit_multiple=2.0`, `neutralization=NONE`, `industry_cap=5`.

Observed R1 NAV exposure: mean gross ~0.999, max 1.000, mean daily turnover 5.93%, max daily turnover 1.99 on a rebalance day.

## Differences vs Handoff Claims

| Handoff claim | Reproduction evidence |
|---|---|
| A0 2004-02-11 ~ 2026-08-28 | Match |
| 5,551 trading days | Match |
| 2,259 ever-traded stocks | Match |
| 7,943,783 raw rows | Match |
| 795,000 PIT eligible rows | Match |
| duplicate keys = 0 | Match |
| OHLC anomalies = 0 | Match |
| download failures = 0 | Match |
| adjusted_rows was 0 | Match |
| A2 ~795k rows / 1,347 stocks / ~5,300 days | Match (795000 / 1347 / 5300) |
| E45 MDD ≈ -13.16% | **Not verified**. A3/R1 do not apply E45. No E45 NAV artifact was consumed. |
| A3 has tradable OOS alpha | Engineering clock PASS; validation loses to PIT proxy; `RESEARCH_ONLY` |
| R1 does not read 2019–2022 during selection | Match by code path |
| R1 2.5% turnover ceiling | Match as **pre-existing EXPERIMENTAL** gate; 0 candidates satisfied it |

## Frozen Baseline Integrity

Unchanged:

- E16 core allocation code/ledgers
- E18/E22 execution / dividend files
- E44 Exact T+1 role (no trainer rewrite)
- E45 / E1 / E11 crisis modules
- No 0050 leveraged ETF
- E50-A remains an overlay research sleeve
- No overwrite of `forward/` or prior experiment folders
- No edits to A0/A1/A2/A3/R1 scripts in this audit

Pinned A0/A1/A2 hashes were checked before the local A3/R1 rerun. New files were written only under `repro/e50a3r1-audit-20260903/`.

## New Assumptions Introduced

These items were **introduced by this audit**. None of them is FROZEN.

| Item | Existed in repo before this audit? | Classification |
|---|---|---|
| Hidden-leverage diagnostic cutoff `gross_exposure > 1.001` | **No.** Pre-existing A3 `simulate()` is cash-scaled and cannot borrow, but it does not encode a 1.001 test. | **PROPOSED** audit diagnostic. Observed 0 breaches. |
| Audit pass = SHA-256 match of pinned A0/A2 QC hashes plus byte-match of A3/R1 NAV/trades/metrics vs CI | **Partially.** Pinned run IDs and SHA-256 emission already exist in A0/A2/A3 workflows. Treating hash/byte-match as the audit success definition is new. | **PROPOSED** reproducibility check. |
| Interpreting 12–13 calendar-day lags as Lunar New Year next-session fills | **No** as a documented acceptance rule. The next-session mapping already exists in A3. | Observation only, **PROPOSED** as an audit interpretation, not a trading rule. |
| “Expand rebalance/buffer beyond the current R1 grid if 2.5% remains infeasible” | **No.** Current R1 grid already has rebalance `{5,10,21}` and exit `{1.25,1.5,2.0}`. | **EXPERIMENTAL** next-challenger idea. **Not implemented. Not selected. Not frozen.** |

Pre-existing items this audit **used but did not freeze**:

| Item | Existed before this audit? | Classification for this audit |
|---|---|---|
| R1 2.5% OOF turnover ceiling | Yes — `scripts/e50a3r1_repair.py`, `research/e50a3r1/README.md` | **EXPERIMENTAL** (existing R1 gate) |
| R1 bootstrap ≥ 0.70 on both held-out windows | Yes — same files | **EXPERIMENTAL** |
| R1 must beat PIT market proxy after costs on both windows | Yes — same files | **EXPERIMENTAL** |
| R1 2011–2018 OOF-only selection; utility `CAGR - 0.5*|MDD|` | Yes | **EXPERIMENTAL** |
| A3 bootstrap ≥ 0.70 and CAGR > 0 promotion | Yes — `scripts/e50a3_train_exact_open.py` | **EXPERIMENTAL** |
| A3 sleeve cost/slippage constants | Yes — A3 script/README | **EXPERIMENTAL** overlay assumptions |
| Exact T+1, PIT, walk-forward, embargo, E16/E18/E22/E45 roles | Yes — frozen spec | **FROZEN** (already frozen; not newly frozen here) |

## Proposed Experimental Gates

None of the following is FROZEN. Do not use them as frozen baselines without explicit approval.

1. **Keep using, without freezing, the current R1 experimental promotion checks** already in `scripts/e50a3r1_repair.py`:
   - 2011–2018 OOF selection only
   - 2.5% average daily turnover feasibility before utility ranking
   - both held-out windows beat PIT market proxy after costs
   - both windows have 21-session block-bootstrap positive-excess ≥ 0.70  
   Status: **EXPERIMENTAL**, existed before this audit.

2. **Turnover-feasibility diagnostic (proposed next experiment, not a new freeze):**
   - Report why every current-grid candidate exceeds 2.5% OOF turnover
   - Do not change the 2.5% number unless a later approved experiment says so
   - If a challenger grid is tried, keep it labeled EXPERIMENTAL and select only on 2011–2018 OOF  
   Status: **PROPOSED** process, not a new threshold.

3. **Hidden-leverage reporting (proposed audit metric only):**
   - Continue reporting max gross exposure and days with exposure > 1.001
   - Do not treat 1.001 as a frozen risk limit  
   Status: **PROPOSED**.

4. **E45 integration remains deferred** until an approved overlay gate passes. That deferral already exists in `research/e50a3r1/README.md`. This audit does not add a new E45 freeze or a new overlay-to-E45 numerical gate.

## Recommended Next Step

Do **not** tune performance.  
Do **not** modify E16, E18/E22, E44, or E45.  
Do **not** freeze the 2.5% turnover ceiling, the 0.70 bootstrap cutoff, any new rebalance interval, or any new model-selection rule.

Smallest safe follow-up, still a challenger folder:

1. Keep the pinned A0/A1/A2 artifacts and the existing Exact T+1 simulator.
2. Diagnose OOF turnover on the **current** R1 grid only (already includes 5/10/21-day rebalance and 1.25/1.5/2.0 buffers).
3. If a later approved experiment expands that grid, label every new parameter **EXPERIMENTAL** and select only on 2011–2018 OOF.
4. Re-read 2019–2022 and 2023-latest only after a candidate is chosen without those windows.
5. Leave E45 untouched until an explicitly approved overlay gate says otherwise.

R1 is reproducible and remains `RESEARCH_ONLY` under its own pre-existing experimental gates. That is an audit conclusion, not a new frozen rule.
