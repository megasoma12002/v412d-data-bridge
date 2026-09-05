# E50 HANDOFF VERIFICATION


> **2026-09-05 E45 status correction (do not delete prior rows):**  
> Historical handoff claim MDD ≈ −13.16% = **`NOT_VERIFIED_HISTORICAL_NARRATIVE`**.  
> Official: `E45_ARTIFACT_STATUS=NOT_VERIFIED`, `E45_STITCH_STATUS=DEFERRED`, `E45_GOVERNANCE_CLASS=SOFT_FROZEN_CRITICAL`, `E45_LIVE_AUTHORIZATION=NO`.  
> Verified dated artifacts: closest lineage val MDD **−15.81%**; E3 winner val MDD **−18.49%**; early-stack+E45_E3 MDD **−20.76%** / CAGR **~10.79%**.  
> Documented research lineage `E38→E43→E44→E45` ≠ importable code lineage `E1→E1.1→E2→E2.1→E3→E45 wrapper`.  
> Canonical: `research/e45/E45_OFFICIAL_STATUS.md`. Prior “NOT FOUND / INCOMPLETE” audit rows below are retained as history.


Date: 2026-09-03  
Sandbox: `repro/e50a3r1-audit-20260903/`  
Reproduction PR: https://github.com/megasoma12002/v412d-data-bridge/pull/17  
Governance PR: https://github.com/megasoma12002/v412d-data-bridge/pull/18  

This verification did **not** start performance tuning.  
It did **not** modify E16, E18, E22, E44, or E45.  
It did **not** promote any new threshold, rule, weight, rebalance frequency, bootstrap cutoff, model-selection rule, router rule, Alpha model, or acceptance gate to frozen status.

Companion evidence:

- `E50-A3-R1_REPRODUCTION_AUDIT.md`
- `reports/dataset_manifest.json`
- `reports/file_hashes.json`
- `reports/leakage_audit.json`
- `reports/period_definitions.json`
- `reports/exposure_turnover_summary.json`
- `reports/exact_t1_trace_samples.csv`
- `reports/rule_classification.json`
- `reports/ci_vs_local_hash_diff.json`

---

## 1. Governance Classification

Canonical class definitions (also recorded in PR #18 `FROZEN_GOVERNANCE.md`):

```
HARD_FROZEN = 研究正確性底線
SOFT_FROZEN = E16 / E18 / E22 / E45 目前正式策略版本
SOFT_FROZEN_CRITICAL = E45 (separate challenger + higher validation bar)
EXPERIMENTAL = new model / threshold / weight / Router / rebalancing /
               bootstrap cutoff / model-selection rule / acceptance gate
```

Promotion path (unchanged, not a new freeze):

```
FROZEN_BASELINE
-> CHALLENGER
-> OOS VALIDATION
-> COST VALIDATION
-> STRESS / MONTE CARLO VALIDATION
-> GOVERNANCE REVIEW
-> EXPLICIT APPROVAL
-> NEW FROZEN VERSION
```

Never overwrite or delete the previous frozen baseline.

| Rule / module | Class | Notes |
|---|---|---|
| Point-in-Time correctness | HARD_FROZEN | A0/A1/A2 contracts |
| No look-ahead | HARD_FROZEN | available_date / embargo |
| No survivorship bias | HARD_FROZEN | delistings retained |
| Causal information/signal/order/execution clock | HARD_FROZEN | E44 principle; E18/A3 implementation |
| Exact T+1 execution principle | HARD_FROZEN | fill at next session open |
| Walk-Forward | HARD_FROZEN | A3/R1 folds |
| Embargo | HARD_FROZEN | 22 sessions before each A3 fold |
| No future-aware normalization / ranking / model selection | HARD_FROZEN | ranks `over("date")`; selection on 2011–2018 OOF |
| Do not overwrite / delete a prior frozen baseline | HARD_FROZEN | process integrity |
| Do not claim PASS without reproducible evidence | HARD_FROZEN | process integrity |
| E16 Core Allocation | SOFT_FROZEN | current official core version |
| E18 Execution Layer | SOFT_FROZEN | current official execution version |
| E22 execution/dividend/turnover extensions | SOFT_FROZEN | current official dividend version |
| E45 Crisis Protection Core | SOFT_FROZEN_CRITICAL | official crisis version; higher challenger bar |
| E44 named package | HARD_FROZEN principle / no official strategy version | clock is HARD; no isolated `e44` package |
| E50-A0 / A1 / A2 datasets | HARD_FROZEN contracts; not SOFT_FROZEN strategy | do not silent-rebuild |
| E50-A3 / E50-A3-R1 Alpha model | EXPERIMENTAL | new Alpha model |
| R1 2.5% OOF turnover ceiling | EXPERIMENTAL | pre-existing gate |
| R1 bootstrap ≥ 0.70 | EXPERIMENTAL | pre-existing cutoff |
| R1 beat-PIT-proxy gate | EXPERIMENTAL | pre-existing acceptance gate |
| R1 utility `CAGR - 0.5*|MDD|` | EXPERIMENTAL | pre-existing weight |
| R1 grid (`top_k`, `rebalance_every`, `exit_multiple`, neutralization, industry_cap) | EXPERIMENTAL | pre-existing model-selection / rebalance rules |
| A3 overlay costs 14.25bp / 30bp tax / 5bp slip | EXPERIMENTAL | overlay simulator, not E18 official fees |
| A3 NT$20m liquidity filter | EXPERIMENTAL | pre-existing threshold |
| Audit diagnostic `gross_exposure > 1.001` | EXPERIMENTAL | introduced by this audit; diagnostic only |
| New Router logic | EXPERIMENTAL | existing routers inside E16 remain with E16 |
| New acceptance gate | EXPERIMENTAL | including any overlay-to-E45 handoff number |
| 0050 leveraged ETF in core | REJECTED / not in official E16 | not a new freeze |

The E45 higher bar is a **process** requirement (separate folder, preserved baseline, crisis-window stress, Monte Carlo / block-bootstrap of drawdown protection, no weakening vs preserved E45, explicit approval). It does not invent a new MDD, turnover, or bootstrap number.

---

## 2. Frozen Architecture Verification

Specified architecture:

```
E16 Core Allocation
+
E18/E22 Execution Layer
+
E50-A Alpha Overlay
+
E45 Crisis Protection Core
```

| Claim | Status | Evidence |
|---|---|---|
| E16 is the core allocation | PARTIALLY VERIFIED | Live E16 target is built in `scripts/e21_forward_pipeline.py` (`FIN+TEL+0050`, causal target history). Live ledger covers 2026-08-24–2026-09-03 only (9 signal days). No separate `e16/` package. |
| E18/E22 is the execution layer | PARTIALLY VERIFIED | E18 fills are next-session open ±5bp in `forward/e21/fills.csv`. E22 dividend ledger exists under `data/dividend_events/`. E22 is not wired into the E21 fill loop. |
| E50-A is an overlay, not the full portfolio | VERIFIED as research contract; NOT FOUND as combined live portfolio | A3/R1 simulate a standalone long-only sleeve. `qc_status.json` records `E45 not applied`. No combined E16+E50-A NAV. |
| Alpha weakening ≠ crisis | VERIFIED in spec; NOT FOUND in combined engine | `FROZEN_STRATEGY_SPEC.md` and E21 regime labels (`Bull/Bear/Sideways/Crisis`) exist. A3/R1 do not consume E45 and do not implement an Alpha-weak state distinct from crisis. |
| Alpha is reduced before core liquidation | VERIFIED in spec; NOT FOUND in combined engine | Operating logic is documented. No live state machine that cuts A3 first then E16. |
| E45 handles crisis-level risk control | PARTIALLY VERIFIED | Crisis lineage exists (`scripts/v412e1_crisis_buffer.py`, `v412e11_graduated_crisis.py`, `v412e2_e3_three_rounds.py`). No module named `e45`. A3/R1 explicitly leave E45 untouched. |
| 0050 leveraged ETF is not in core | VERIFIED | E21 universe is `2880,2886,2892,5880,2412,3045,4904,0050` plus TAIEX. No 0050L / 00631L / 正二 codes in live market or orders. |

Architecture conclusion: the **roles** are specified and E16/E18 live core path exists. The four-layer **combined portfolio** (overlay on core, Alpha-off before crisis, E45 handoff) is not implemented as one engine. That is a research-gap warning, not a license to rebuild from scratch.

---

## 3. Repository Verification

Status vocabulary: FOUND / INCOMPLETE / MISSING / SUSPICIOUS.

| Component | Status | Exact paths |
|---|---|---|
| E16 | INCOMPLETE | Code: `scripts/e21_forward_pipeline.py` (comment: “Rebuild frozen E16 target history causally”; columns `e16_financial/e16_telecom/e16_0050`). Live outputs: `forward/e21/signals.csv`, `forward/e21/nav.csv` (`nav_e16_e18`), `forward/e21/portfolio_state.json`. No `scripts/e16_*.py`, no full-history E16 NAV artifact. |
| E18 | FOUND | Execution in `scripts/e21_forward_pipeline.py` (pending orders filled when `signal_date < latest` at today’s open ±5bp). Ledgers: `forward/e21/orders.csv`, `forward/e21/fills.csv`, `forward/e21/audit_chain.jsonl`. QC: `scripts/e21_qc.py`, `forward/e21/qc_status.json` (`status=PASS`). |
| E22 | FOUND | `scripts/v412e22_fetch_dividend_events.py`, `.github/workflows/v412e22-dividend-events.yml`, `data/dividend_events/e22_dividend_events.csv`, `e22_dividend_raw.json`, `e22_dividend_fetch_status.json` (`status=PASS`, 150 rows, E16 universe). Related research: `scripts/v412e6_dividend_lifecycle.py`, `research/v412e6/`. |
| E44 | INCOMPLETE | Principle FOUND in E18/A3 clocks and `E50_RESEARCH_HISTORY.md` §E44. No `scripts/e44_*.py` and no isolated E44 audit package. |
| E45 | INCOMPLETE (artifact) | Named module: `scripts/e45_crisis_core.py`. Importable code lineage: E1→E1.1→E2→E2.1→E3→wrapper. Documented research lineage: E38→E43→E44→E45. Historical MDD ≈ -13.16% = **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** (see §7 / `research/e45/E45_OFFICIAL_STATUS.md`). |
| E50-A0 | FOUND | Code: `scripts/e50a0_build_point_in_time.py`, `research/e50a0/README.md`, `.github/workflows/e50a0-point-in-time.yml`. Pinned run `33532322856`. Local QC: `repro/e50a3r1-audit-20260903/inputs/a0/qc_status.json`. Large parquet/csv gitignored; hashes in that QC file. |
| E50-A1 | FOUND | Code: `scripts/e50a1_build_causal_layer.py`, `scripts/e50a1_probe_schemas.py`, `research/e50a1/`. Pinned run `33637154310`. QC: `inputs/a1/qc_status.json`. |
| E50-A2 | FOUND | Code: `scripts/e50a2_build_causal_factors.py`, `research/e50a2/`. Pinned run `33645002188`. QC: `inputs/a2/qc_status.json`, `inputs/a2/factor_dictionary.json`. |
| E50-A3 | FOUND | Code: `scripts/e50a3_train_exact_open.py`, `research/e50a3/README.md`, `.github/workflows/e50a3-exact-open.yml`. Local rerun: `outputs/a3/`. CI reference: `ci_reference/a3/`. CI run `33680157521`. |
| E50-A3-R1 | FOUND | Code: `scripts/e50a3r1_repair.py`, `research/e50a3r1/README.md`, `.github/workflows/e50a3r1-repair.yml`. Local rerun: `outputs/a3r1/`. CI reference: `ci_reference/a3r1/`. CI run `33713890731`. |
| Financial Router | FOUND | `scripts/v412d_formal_router.py`, `scripts/v412d_dynamic_router.py`, `scripts/v412d_stock_level_trainer.py`, `research/V412D_FORMAL_ROUTER_REPORT_2026-08-24.md`. Live E16 financial sleeve is the four public names in E21, not the full R1–R4 12-name router. |
| Telecom Router | FOUND | `scripts/v412e10_telecom_harvest_reentry.py`, `scripts/v412e9_telecom_sleeve.py`, `forward/e10/`, `forward/e9/`, `research/V412D_FORMAL_ROUTER_REPORT_2026-08-24.md`. |
| 0050 modules | FOUND | `scripts/fetch_telecom_0050_ohlcv.py`, `scripts/v412e10s2_thousand_point_0050.py`, `data/telecom_0050_complete/`, `forward/e10s2/`. Live E16 includes 0050. Leveraged 0050 not present. |
| Cash / Short Bond | INCOMPLETE | Formal-router R0 cash is documented (`research/V412D_FORMAL_ROUTER_REPORT_2026-08-24.md`, average R0 11.68%). E27 short-bond/money-market concept is in `E50_RESEARCH_HISTORY.md` only. No `e27_*.py`, no dedicated short-bond dataset, no cash/bond sleeve in E21. |
| Crisis modules | FOUND | E1/E11/E2/E3/E4/E5 scripts and `research/v412e*` artifacts. E21 also labels `Crisis` regime and E20 shadow overlay. Not a single E45 controller. |
| Manifests | FOUND | A0 `inputs/a0/download_manifest.csv`; A1 `inputs/a1/download_manifest.csv`; audit `reports/dataset_manifest.json`; E21 `forward/e21/audit_chain.jsonl`. |
| Hashes | FOUND | A0/A2 QC `files.*.sha256`; audit `reports/file_hashes.json`; `reports/ci_vs_local_hash_diff.json`; E21 hash chain. |
| QC | FOUND | A0/A1/A2/A3/R1 `qc_status.json`; E21 `forward/e21/qc_status.json`; telecom `data/telecom_0050_complete/qc_summary.json`; E22 fetch status. |
| Training code | FOUND | `scripts/e50a3_train_exact_open.py`, `scripts/e50a3r1_repair.py`, plus V4.12-D/E trainers under `scripts/v412*.py`. |
| Backtest engine | FOUND | A3/R1 `simulate()` Exact-T+1 sleeve; V4.12-D/E historical trainers. |
| Execution engine | FOUND | `scripts/e21_forward_pipeline.py` live ledger. |
| Latest outputs | FOUND | E21 live: `forward/e21/` through 2026-09-03. A3/R1 research: `outputs/a3`, `outputs/a3r1` through 2026-08-28. |

SUSPICIOUS items (not patched):

1. Two E21 BUY fills with `quantity=0` (`2026-09-01-5880-BUY`, `2026-09-02-5880-BUY`) after cash clipping. Fill rows still recorded.
2. E21 live QC reports `signal_rows=9` — real but short live sample, not a full-history core backtest.
3. 30 / 23,524 A1 dividend rows have `available_date > effective_date`.
4. A0 skipped 85,738 malformed archive rows; `adjusted_rows=0` on the archive path (pre-existing contract).

---

## 4. Reproduction Verification

**A3 and A3-R1 reproduce end-to-end. VALIDATED.**  
A0/A1/A2 were **downloaded, not rebuilt**, from pinned Actions artifacts.

| Item | Path / result |
|---|---|
| Dataset manifest | `reports/dataset_manifest.json` |
| Hashes | `reports/file_hashes.json`; economic artifacts byte-match CI |
| QC status | A0/A1/A2 `PASS`; A3 `PASS` / `RESEARCH_ONLY`; R1 `PASS` / `RESEARCH_ONLY` |
| Train / validation / test | `reports/period_definitions.json` |
| Model config | `outputs/a3/frozen_model.json`, `outputs/a3r1/frozen_repair_model.json` (filename does **not** confer frozen status) |
| Period metrics | `outputs/a3/period_metrics.csv`, `outputs/a3r1/period_metrics.csv` (byte-match CI) |
| Trades | `outputs/a3/trades.csv` (8,663), `outputs/a3r1/trades.csv` (8,461) |
| Daily NAV | `outputs/a3/daily_nav.csv`, `outputs/a3r1/daily_nav.csv` (byte-match CI) |
| Turnover / exposure / costs | `reports/exposure_turnover_summary.json` plus metrics columns |
| Exact T+1 samples | `reports/exact_t1_trace_samples.csv` |

Pinned inputs:

| Stage | Run | Artifact |
|---|---|---|
| A0 | 33532322856 | `v412-e50a0-point-in-time` |
| A1 | 33637154310 | `v412-e50a1-full-causal-database` |
| A2 | 33645002188 | `v412-e50a2-causal-alpha-factors` |

A0 manifest check vs handoff: 2004-02-11–2026-08-28, 5,551 dates, 2,259 codes, 7,943,783 raw rows, 795,000 PIT eligible rows, duplicate keys 0, OHLC anomalies 0, download failures 0, `adjusted_rows=0`.

A2: 795,000 rows, 1,347 codes, 5,300 dates.

Windows:

- Walk-forward folds: 2011–2012, 2013–2014, 2015–2016, 2017–2018; embargo 22 sessions.
- R1 selection: 2011–2018 OOF only.
- Validation fit cutoff: 2018-11-30; sealed fit cutoff: 2022-12-01.
- Validation: 2019-01-02–2022-12-30.
- Sealed: 2023-01-03–2026-08-28.

R1 selected config (EXPERIMENTAL, train-only, **not frozen**): `TECH2`, `BREADTH_REGIME`, `lambda=1.0`, `top_k=20`, `rebalance_every=5`, `exit_multiple=2.0`, `neutralization=NONE`, `industry_cap=5`. `turnover_feasible_candidates=0`; `turnover_constraint_satisfied=false`.

R1 metrics (byte-match CI `33713890731`):

| Portfolio | CAGR | MDD | Avg daily turnover | Total cost | Trades |
|---|---:|---:|---:|---:|---:|
| VALIDATION_2019_2022 | 14.95% | -33.50% | 7.05% | 0.358 | 4562 |
| VALIDATION market proxy | 20.97% | -29.58% | 0 | 0 | 0 |
| SEALED_2023_LATEST | 48.01% | -32.51% | 4.68% | 0.253 | 3899 |
| SEALED market proxy | 20.99% | -25.59% | 0 | 0 | 0 |

A3 metrics (byte-match CI `33680157521`):

| Portfolio | CAGR | MDD | Avg daily turnover | Total cost | Trades |
|---|---:|---:|---:|---:|---:|
| VALIDATION_2019_2022 | 1.44% | -27.94% | 6.53% | 0.256 | 4526 |
| SEALED_2023_LATEST | 22.26% | -21.37% | 7.21% | 0.280 | 4137 |

R1 exposure: mean gross ≈ 0.999, max 1.000, mean daily turnover 5.93%, max daily turnover 1.99 on a rebalance day, `stale_positions_max=1`.

Hash mismatches vs CI are parquet/float/timestamp serialization only (`causal_scores.parquet`, some JSON/CSV whitespace). NAV / trades / period_metrics / grids byte-match.

---

## 5. Exact T+1 Verification

Clock under test:

```
Information(T) -> Feature(T) -> Signal(T) -> Order
-> Next Trading Day Open -> Fill -> Position -> PnL
```

### A3 / R1 sleeve (reproduced)

| Check | Result |
|---|---|
| Same-bar fill (`execution_date <= signal_date`) | 0 / 8,663 A3; 0 / 8,461 R1 |
| Next-session mapping | `next_date = calendar[i+1]`; last calendar day cannot order |
| Missing open | Pre-existing A3 policy: “A missing raw open means the order cannot trade; the position stays frozen.” R1 `stale_positions_max = 1` |
| Holiday / long calendar gap | Lags of 12–13 days on 2019-01-30, 2023-01-17, 2025-01-22 are next **market** sessions (Lunar New Year), not same-bar |
| Corporate-action contamination of execution | Execution prices are A0 **raw** open. Adjusted prices are ranking-only. Labels are a separate file |

Traced samples (`reports/exact_t1_trace_samples.csv`):

| Signal | Exec | Code | Side | Signal close | Exec open | t1_ok | same_bar |
|---|---|---|---|---:|---:|---|---|
| 2019-01-02 | 2019-01-03 | 2313 | BUY | 19.85 | 19.95 | true | false |
| 2019-01-02 | 2019-01-03 | 2337 | BUY | 17.75 | 17.45 | true | false |
| 2023-01-03 | 2023-01-04 | 1101 | BUY | 33.50 | 33.65 | true | false |
| 2023-01-10 | 2023-01-11 | 2371 | SELL | 33.85 | 33.85 | true | false |

The 2023-01-10 SELL of 2371 still fills 2023-01-11 while `alpha_universe=false` (mark-to-market of an existing position). Pre-existing A3 policy, not a same-bar fill.

Self-test: `python3 scripts/e50a3_train_exact_open.py --self-test` printed `E50-A3 self-test PASS` during the isolated rerun (asserts include 2020-01-02 signal → 2020-01-03 execution).

### E18 live core path

| Check | Result |
|---|---|
| Same-bar fill | 0 / 64 fills (`fill_date > signal_date` required by `signal_date < latest`) |
| Fill vs next open ±5bp | max abs error ≈ 0 (1.4e-14) |
| Trading calendar | fills skip 2026-08-29/30 weekend; 2026-08-28 signal fills 2026-08-31 |
| Suspension / halt | no dedicated halt feed in E21; missing instrument on a date drops that common-date (pipeline requires all of FIN+TEL+0050+TAIEX) |
| Missing open | E21 would KeyError if open missing for an ordered code; no substitute-name policy. Not observed in the 64 fills |
| Corporate actions | E21 uses `close` / `open` from `live_market.csv` and `adj_close` only inside feature scores. E22 dividend cashflows are **not** applied to E21 NAV |

---

## 6. Leakage Verification

Actively tested against reproduced A0/A1/A2/A3/R1 artifacts and source:

| Attack | Result | Evidence |
|---|---|---|
| Look-ahead bias | Not found in A2 join / A3 fit cutoffs | A2 `financial_lookahead_violations=0`, `revenue_lookahead_violations=0`; fundamentals on `available_date <= T` |
| Survivorship bias | Not found as survivor-only universe | 295 delisted codes retained; 2,259 ever-traded; `alpha_universe` never on/after delisting (0 rows) |
| Future-aware universe | Not found | `alpha_when_not_listed_and_trading=0` |
| Full-sample normalization | Not found | `pct_*` ranks `over("date")` only (`factor_dictionary.json` / A2 code) |
| Ranking leakage | Not found as full-sample rank | Cross-section within signal date |
| Label leakage | Not found | Labels physically separate; `label_columns_in_feature_panel=[]`; `forbidden_labels_in_panel=[]` |
| Future corporate actions as pre-event features | Residual | 30 / 23,524 A1 rows `available_date > effective_date`. Not patched. Execution still uses raw open |
| Future delisting knowledge | Not found as alpha membership after delist | Delisting date is known historically in the master; eligibility uses `date < delisting_date` |
| Train/test contamination | Not found in R1 selection | Selection 2011–2018 OOF; validation/sealed not used to pick config |
| Hyperparameter leakage | Not found into 2019–2022 for R1 selection | Code path restricts utility ranking to embargoed OOF |
| Threshold-selection leakage | Not found into sealed window for R1 | Same; 2.5% / 0.70 remain EXPERIMENTAL gates, not re-fit on 2023+ |
| Feature-selection leakage | Not found as 2023-aware A2 lock | A2 diagnostics lock 2005–2018 / 2019–2022; 2023+ not used to tune A2 definitions |

Residual leakage notes (warnings, not new frozen rules): FinMind industry is a current snapshot (A0 known limitation); 30,162 panel industry nulls/`historical_unknown`; chosen R1 config used `neutralization=NONE`.

---

## 7. Differences vs Handoff Claims

Sources: `HANDOFF.md`, `FROZEN_STRATEGY_SPEC.md`, `E50_RESEARCH_HISTORY.md`, `research/e50a0|a1|a2|a3|a3r1/README.md`.

| Claim | Classification | Evidence |
|---|---|---|
| This is a continuation, not a greenfield rebuild | VERIFIED | Repo contains V4.12-D through E50-A3-R1 scripts and artifacts |
| Frozen architecture = E16 + E18/E22 + E50-A overlay + E45 | PARTIALLY VERIFIED | Roles documented; combined engine not present |
| E50-A is overlay, not the whole portfolio | VERIFIED (contract) / NOT FOUND (live combined NAV) | A3/R1 standalone sleeve |
| Alpha weak → cut Alpha first; crisis → E45 | PARTIALLY VERIFIED | Written in spec; not implemented as one state machine |
| E16 = 公股金融 + 電信三雄 + 0050 | VERIFIED in live E21 | `FIN=['2880','2886','2892','5880']`, `TEL=['2412','3045','4904']`, `0050` |
| 0050 正二 not in core | VERIFIED | Absent from E21 universe and orders |
| Exact T+1 / no same-bar | VERIFIED | A3/R1 0 violations; E21 0 violations |
| PIT / no look-ahead / no survivorship | VERIFIED with residuals | A0/A1/A2 QC PASS; 30 CA timing residuals |
| Walk-forward + embargo | VERIFIED | `reports/period_definitions.json` |
| A0 2004-02-11–2026-08-28, 5551 days, 2259 codes, 7943783 raw, 795000 PIT | VERIFIED | `inputs/a0/qc_status.json` |
| A0 duplicate keys = 0, OHLC anomalies = 0, download failures = 0 | VERIFIED | same |
| A0 `adjusted_rows` was 0 | VERIFIED | `adjusted_rows=0` |
| A2 ~795k rows / 1347 stocks / ~5300 days | VERIFIED | 795000 / 1347 / 5300 |
| A3 is current research asking whether A2 has tradable OOS alpha | VERIFIED | Engineering PASS; validation loses to PIT proxy; `RESEARCH_ONLY` |
| R1 does not read 2019–2022 during selection | VERIFIED | code + selected-config `fitted_through=2018-11-30` for validation model |
| R1 2.5% turnover ceiling | VERIFIED as EXPERIMENTAL gate | 0 feasible candidates |
| E45 MDD ≈ -13.16% | **NOT_VERIFIED_HISTORICAL_NARRATIVE** (2026-09-05) / historically NOT FOUND | Number appears only in handoff/spec text. Closest crisis artifacts: E1 validation MDD -17.21%; E1.1 -15.81%; E3 validation -18.49%; V4.12-D validation -18.91%. No CSV/JSON equals -13.16% |
| E45 CAGR then ~10%, return insufficient | NOT FOUND | No E45-named NAV. Do not treat as verified |
| E22 is frozen execution/dividend layer | PARTIALLY VERIFIED | Dataset FOUND; not applied to E21 NAV |
| E44 causal-clock package | PARTIALLY VERIFIED | Principle FOUND; package MISSING |
| E27 cash/short-bond alternative | NOT FOUND as module | Concept only in history |
| Long-term CAGR >= 20% and MDD ~10–15% | NOT a current result | Targets only. R1 validation MDD -33.5%; sealed MDD -32.5%. Not promoted |
| `frozen_repair_model.json` is a frozen strategy | CONTRADICTED if read as governance freeze | Pre-existing output filename; config remains EXPERIMENTAL / `RESEARCH_ONLY` |

Do not silently assume old claims are true. Unverified E45 numbers stay unverified.

---

## 7A. Provenance Check — 2.5% OOF Turnover and Bootstrap 0.70

Required before any further research. Neither rule was introduced, inferred, or promoted by this audit. Both remain **EXPERIMENTAL**.

### A. 2.5% OOF turnover ceiling

| Field | Evidence |
|---|---|
| Exact path | `scripts/e50a3r1_repair.py` |
| Exact line / config | Line 297: `metric["turnover_feasible"] = metric["average_daily_turnover"] <= 0.025` |
| Related lines | Lines 301–308 (feasible pool / `turnover_constraint_satisfied` / `turnover_feasible_candidates`); lines 336–337 require `turnover_constraint_satisfied` for promotion |
| Documentation | `research/e50a3r1/README.md` lines 17–21: “A daily turnover ceiling of 2.5%…” |
| Introducing commit | `ea702996e167535f9c3f2e263cd88dfe5a8d2b29` (2026-09-03 12:02:14 +0800) — *E50-A3-R1: repair regime stability and turnover* |
| Hard-block commit | `8b968df80107a45d6313cfc0e4010afd6a2e4d35` (2026-09-03 12:07:25 +0800) — *E50-A3-R1: hard-block infeasible turnover selection* |
| Predates this handoff audit? | **YES.** Both commits are ancestors of `main` and of the first audit commit `74dfee7` (2026-09-03 16:32:57 UTC). |
| Governance class | **EXPERIMENTAL** |
| Introduced / inferred / promoted by this audit? | **NO / NO / NO** |

Not HARD_FROZEN, not SOFT_FROZEN, not SOFT_FROZEN_CRITICAL. Not PROPOSED (it already existed). Downgrade is not needed because provenance is proven; class stays EXPERIMENTAL.

### B. Bootstrap / acceptance threshold 0.70

| Field | Evidence |
|---|---|
| Exact path (R1) | `scripts/e50a3r1_repair.py` |
| Exact lines (R1) | Lines 338–339: `block_bootstrap_positive_probability] >= 0.70` on both VALIDATION and SEALED |
| Exact path (A3 parent) | `scripts/e50a3_train_exact_open.py` |
| Exact lines (A3) | Lines 559–560: same `>= 0.70` promotion test |
| Documentation | `research/e50a3r1/README.md` lines 25–27: “both 21-session block-bootstrap positive-excess probabilities reach 70%” |
| Introducing commit (A3) | `83ce63ff0f7987d1c14f293b10711981b8313b76` (2026-09-03 04:35:00 +0800) — *E50-A3: causal alpha exact T+1 open simulation* |
| Introducing commit (R1) | `ea702996e167535f9c3f2e263cd88dfe5a8d2b29` (same as turnover ceiling) |
| Predates this handoff audit? | **YES.** Both commits are ancestors of `main` and of `74dfee7`. |
| Governance class | **EXPERIMENTAL** |
| Introduced / inferred / promoted by this audit? | **NO / NO / NO** |

Not HARD_FROZEN, not SOFT_FROZEN, not SOFT_FROZEN_CRITICAL. Not PROPOSED. Downgrade is not needed; class stays EXPERIMENTAL.

### Provenance verdict

Both constraints are pre-existing EXPERIMENTAL research gates. This audit used them as-is for reproduction. It did not invent them, did not treat them as frozen, and does not promote them.

---

## 8. New Assumptions Introduced

None of the following is frozen. None changes E16 / E18 / E22 / E45 behavior.

| Item | Existed before audit | Governance status | Evidence | Changes frozen behavior? |
|---|---|---|---|---|
| Hidden-leverage diagnostic `gross_exposure > 1.001` | NO | EXPERIMENTAL (audit diagnostic; previously labeled PROPOSED) | `reports/rule_classification.json`; 0 breaches | NO |
| Audit success = SHA-256 of pinned A0/A2 QC hashes + byte-match of A3/R1 NAV/trades/metrics vs CI | PARTIALLY (pinned run IDs and SHA emission already existed) | EXPERIMENTAL audit criterion | `reports/ci_vs_local_hash_diff.json` | NO |
| Interpreting 12–13 calendar-day lags as Lunar New Year next-session fills | NO as a documented acceptance rule | EXPERIMENTAL observation, not a trading rule | `reports/leakage_audit.json` lag histogram | NO |
| “Expand rebalance/buffer beyond current R1 grid if 2.5% remains infeasible” | NO | EXPERIMENTAL idea only; **not implemented** | `reports/rule_classification.json` | NO |
| SOFT_FROZEN_CRITICAL label for E45 | NO as a named class (E45 was already the official crisis version) | SOFT_FROZEN_CRITICAL process class | PR #18 `FROZEN_GOVERNANCE.md` | NO — does not retune E45 |
| Higher E45 challenger bar (crisis stress + MC vs preserved baseline) | NO as written process | Process only; **no new numeric gate** | PR #18 | NO |

Pre-existing items used but **not frozen** by this verification:

| Item | Existed before audit | Status | Changes frozen behavior? |
|---|---|---|---|
| R1 2.5% OOF turnover ceiling | YES — `scripts/e50a3r1_repair.py` | EXPERIMENTAL | NO |
| R1 bootstrap 0.70 | YES | EXPERIMENTAL | NO |
| R1 beat-proxy acceptance gate | YES | EXPERIMENTAL | NO |
| R1 utility weight 0.5 on \|MDD\| | YES | EXPERIMENTAL | NO |
| A3 sleeve costs / NT$20m filter | YES | EXPERIMENTAL | NO |
| Do not apply E45 inside A3/R1 | YES — A3/R1 README | EXPERIMENTAL research policy; E45 itself remains SOFT_FROZEN_CRITICAL | NO |

---

## 9. Frozen Baseline Integrity

Expected: **UNCHANGED**. Observed: **UNCHANGED**.

`git diff --stat origin/main...cursor/e50a3r1-reproduction-audit-d049` contains only `repro/` sandbox files. No edits to:

- `scripts/e21_forward_pipeline.py` / `scripts/e21_qc.py`
- `scripts/v412e22_fetch_dividend_events.py`
- `scripts/v412e1_crisis_buffer.py` / `v412e11_graduated_crisis.py` / `v412e2_e3_three_rounds.py`
- `forward/e21/`
- `data/dividend_events/`
- A0/A1/A2/A3/R1 trainers

Governance-only edits live on a **separate** branch / PR #18 (`FROZEN_GOVERNANCE.md` and docs). They do not change strategy code.

A0/A1/A2 were not rebuilt. New files were written only under `repro/e50a3r1-audit-20260903/`.

---

## 10. Handoff Decision

**HANDOFF_COMPLETE_WITH_WARNINGS**

The audit itself is complete: repository paths were checked, A3/R1 reproduced, Exact T+1 was traced, leakage was attacked, handoff claims were classified with evidence, and the 2.5% / 0.70 gates were provenance-verified as pre-existing EXPERIMENTAL rules. Reproduction may continue from this checkpoint. Performance tuning is still forbidden.

Blockers that would have produced `HANDOFF_BLOCKED` were **not** found (no missing A3/R1 inputs that had to be guessed; no frozen-baseline overwrite).

Warnings (do not ignore, do not “fix” by retuning):

1. **Four-layer portfolio is not wired.** E50-A is a standalone research sleeve. Alpha-weak ≠ crisis is documented, not executed as a combined state machine.
2. **E45 is SOFT_FROZEN_CRITICAL but incomplete as a named module.** Lineage exists (E1/E11/E2–E3). MDD ≈ -13.16% is **`NOT_VERIFIED_HISTORICAL_NARRATIVE`**. Use dated lineage MDDs (−15.81% / −18.49% / −20.76%). Do not invent a replacement number. Stitch DEFERRED. See `research/e45/E45_OFFICIAL_STATUS.md`.
3. **E16 live ledger is short** (9 signal days). Historical E16 target code exists; a full-history official E16 NAV file does not.
4. **E22 is not applied to E21 NAV.** Dividend layer exists beside the live execution ledger.
5. **E44 has no isolated package.** Clock is implemented inside E18 and A3.
6. **Cash / short-bond is incomplete.** R0 cash exists in V4.12-D research; E27 has no module.
7. **E21 qty-0 BUY fills** (2) after cash clipping.
8. **A1 30 CA rows** with `available_date > effective_date`.
9. **R1 remains `RESEARCH_ONLY`.** Validation loses to PIT proxy; `turnover_feasible_candidates=0`; MDD far from the 10–15% long-term target. That is an experimental-gate failure, not a freeze.

---

## 11. Smallest Safe Next Research Step

Do **not** execute this step in this turn.

Do **not** tune CAGR.  
Do **not** modify E16 / E18 / E22 / E45.  
Do **not** freeze 2.5%, 0.70, any new rebalance interval, any new model-selection rule, or any overlay-to-E45 gate.  
Do **not** integrate E45 until an approved overlay gate exists.

**Next experiment (challenger folder only):** diagnose why **every current R1 grid point** exceeds the pre-existing 2.5% OOF turnover ceiling.

Scope:

1. Keep pinned A0/A1/A2 artifacts and the existing Exact T+1 simulator.
2. On the **current** R1 grid only (`rebalance_every` ∈ {5,10,21}, `exit_multiple` ∈ {1.25,1.5,2.0}, existing `top_k` / neutralization / industry_cap), report OOF turnover, name churn, and cost drag by cell.
3. Selection remains 2011–2018 OOF only. Do not read 2019–2022 or 2023-latest to pick a new cell.
4. If a later approved experiment expands the grid, label every new parameter EXPERIMENTAL.
5. Leave E45 untouched (SOFT_FROZEN_CRITICAL).

Long-term targets remain CAGR >= 20% and MDD about 10–15%. Causal correctness, frozen-baseline preservation, Exact T+1, OOS robustness, transaction-cost survival, reproducibility, and governance outrank those targets.
