# Frozen Governance

This document is the Frozen Governance contract for the whole research program.

Authoritative class definitions:

```
HARD_FROZEN
= 研究正確性底線
  Point-in-Time correctness
  No look-ahead
  No survivorship bias
  causal information/signal/order/execution clock
  Exact T+1 execution principle
  Walk-Forward
  Embargo
  no future-aware normalization / ranking / model selection

SOFT_FROZEN
= E16 / E18 / E22 / E45 目前正式策略版本
  E16 Core Allocation
  E18 Execution Layer
  E22 execution/dividend/turnover extensions
  E45 Crisis Protection Core

SOFT_FROZEN_CRITICAL
= E45 only
  may be challenged only by a separate challenger experiment
  with a higher validation bar than E16 / E18 / E22

EXPERIMENTAL
= 新模型、新門檻、新權重、新 Router、新 rebalancing
  any newly introduced threshold
  any new weight
  bootstrap cutoff
  rebalance rule
  model-selection rule
  new Router logic
  new Alpha model
  any new acceptance gate
```

English equivalent:

- HARD_FROZEN = the research-correctness floor listed above. It is not a strategy version.
- SOFT_FROZEN = the current official strategy versions of E16, E18, E22, and E45.
- SOFT_FROZEN_CRITICAL = E45, a SOFT_FROZEN official version that requires a higher challenger bar.
- EXPERIMENTAL = a new model, threshold, weight, bootstrap cutoff, rebalance rule, model-selection rule, router, Alpha model, or acceptance gate.

If a later note disagrees with this file, this file wins until a new frozen version is explicitly approved.

Day-to-day research workflow (order, held-out, promotion labels, versioning) is in `E50_RESEARCH_OPERATING_RULES.md`. Class membership still follows this file.

This contract applies to E16, E18, E22, E45, E50-A overlay research, and all future E50 challengers.

---

## 0. Purpose

Frozen rules exist to protect causal correctness and to keep the current official E16 / E18 / E22 / E45 versions readable beside any challenger.

They do **not** exist to lock in a performance number.

Long-term targets (CAGR >= 20%, MDD about 10–15%) remain targets. They are not a license to relax HARD_FROZEN rules.

---

## 1. Rule classes

Every research rule is one of:

### HARD_FROZEN — 研究正確性底線

The correctness floor of the research. It cannot be relaxed to improve CAGR, Sharpe, turnover, or drawdown.

A HARD_FROZEN rule may be *implemented more strictly*, but it may not be weakened, bypassed, or renamed as “research-only” in a production-claiming result.

HARD_FROZEN is not a strategy version. It is the set of rules that make a result causally valid.

### SOFT_FROZEN — E16 / E18 / E22 / E45 目前正式策略版本

Only these four current official strategy versions are SOFT_FROZEN:

- E16 Core Allocation
- E18 Execution Layer
- E22 execution / dividend / turnover extensions
- E45 Crisis Protection Core

The current official implementation is retained. It may be challenged only through a separate challenger experiment. The original baseline artifacts, code path, and reported metrics must be preserved. The challenger must not overwrite or delete the prior frozen baseline.

A SOFT_FROZEN challenger that looks better is still not the new official version until the promotion path completes.

### SOFT_FROZEN_CRITICAL — E45

E45 is SOFT_FROZEN and additionally SOFT_FROZEN_CRITICAL.

It may be challenged only by a separate challenger experiment that:

1. keeps the original E45 code, artifacts, and reported metrics readable;
2. completes the full promotion path below;
3. meets a **higher validation bar** than an E16 / E18 / E22 challenger: crisis-window stress, Monte Carlo / block-bootstrap of drawdown protection, and side-by-side proof that the challenger does not weaken crisis protection versus the preserved E45 baseline;
4. receives explicit approval before any new frozen version is recorded.

This higher bar is a **process** requirement. It does not invent a new MDD, turnover, bootstrap, or handoff number. Any numeric gate proposed for an E45 challenger is EXPERIMENTAL until explicitly approved.

Not SOFT_FROZEN:

- E50-A0 / A1 / A2 datasets (PIT contracts are HARD_FROZEN; do not silent-rebuild)
- E50-A3 / E50-A3-R1 models and numeric gates (EXPERIMENTAL)
- a new router, a new rebalancing calendar, a new weight scheme, a new Alpha model, or a new acceptance gate (EXPERIMENTAL)

### EXPERIMENTAL — 新模型、新門檻、新權重、新 Router、新 rebalancing

Temporary research settings. This class includes, without limitation:

- any newly introduced threshold
- any new weight
- bootstrap cutoff
- rebalance rule
- model-selection rule
- new Router logic
- new Alpha model
- any new acceptance gate

EXPERIMENTAL rules **never become frozen automatically**, including when:

- a backtest looks strong
- sealed-period CAGR is high
- CI is green
- a filename contains `frozen_`
- a README says “selected configuration”

Default: any newly introduced model, threshold, weight, bootstrap cutoff, rebalance rule, model-selection rule, router, Alpha model, or acceptance gate is **EXPERIMENTAL** unless it is explicitly promoted.

---

## 2. Promotion path

No SOFT_FROZEN or EXPERIMENTAL rule may replace a baseline except through:

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

Required properties of a challenger:

1. New experiment branch / output folder.
2. Named hypothesis.
3. Original frozen baseline kept intact (code, artifacts, metrics, hashes).
4. Side-by-side report: baseline, challenger, incremental benefit, additional risk, OOS stability, transaction-cost impact.
5. Decision: PASS / FAIL / INCONCLUSIVE.
6. Explicit human approval before any new frozen version is recorded.
7. Prior frozen version remains readable forever. Never overwrite. Never delete.

A new frozen version, if approved, is additive: `FROZEN_vN` stays, `FROZEN_vN+1` is published beside it.

---

## 3. HARD_FROZEN contents

These are the research-correctness floor. They cannot be relaxed for performance.

### Causal clock

- Information(T) -> Feature(T) -> Signal(T) -> Order -> next market session -> T+1 open fill
- Exact T+1 execution principle
- No same-bar execution
- No Close(T) signal filled at Close(T)
- No replacing a missing T+1 open with a future-selected substitute name

### Point-in-time and leakage

- Point-in-Time correctness
- No look-ahead
- No survivorship bias
- No future financial releases
- No revised data leaked backward
- No future constituent membership
- No future corporate actions as pre-event signals
- No future-aware normalization / ranking / model selection
- No future delisting knowledge
- No full-sample ranking or full-sample scaling
- No label leakage into features
- No train/validation/test contamination

### Walk-forward

- Walk-Forward
- Embargo remains in force where the current causal pipeline requires it
- Fit / transform / calibration use only the allowed train window
- Validation and sealed/test windows are not used to select the model or portfolio rule being tested

### Result integrity

- Do not overwrite or delete a prior frozen baseline
- Do not claim PASS without reproducible evidence
- Failed experiments are retained
- Do not rebuild E50-A0/A1/A2 unless a reproducible upstream defect is identified
- A result must measure the object it claims (overlay NAV is not core NAV; crisis NAV is not alpha NAV)

HARD_FROZEN does **not** freeze a model, a threshold, a weight, a router, or a rebalancing calendar.

---

## 4. SOFT_FROZEN contents

These four current official strategy versions may be challenged only with a preserved-baseline challenger.

### E16 Core Allocation — current official version

Public-financial sleeve, telecom sleeve, 0050 sleeve, and the current E16 target-construction path (including the E21 forward ledger). 0050 leveraged ETF (0050 正二) is not in this official core.

A new E16 weight, membership list, sleeve mix, router, or rebalancing calendar is EXPERIMENTAL. It does not edit the official E16 version in place.

### E18 Execution Layer — current official version

Current live/forward fill policy, lot handling, and turnover/rebalance friction as coded in the E21/E18 path.

Exact T+1 as a clock remains HARD_FROZEN. Changing fees, tax, slippage, lot policy, or rebalancing friction in that baseline path is EXPERIMENTAL and requires a challenger folder.

### E22 Dividend layer — current official versions

- **E22_v2** (preserved cash-only baseline): credit cash on `cash_ex_date` only.
- **E22_v2s** (formal books): raw-price NAV; cash on `cash_ex_date`; stock share increase on `stock_ex_date` (`1 + stock_dividend/10`). Signals may still use `adj_close`; never mark books NAV with `adj_close` while also increasing shares.

Canonical module: `scripts/e22_dividend_accounting.py`. Live forward defaults to E22_v2s.

Changing dividend cashflow timing (e.g. payment-date credit) or tax treatment beyond these two labeled versions is EXPERIMENTAL and requires a challenger folder.

### E45 Crisis Protection Core — current official version (SOFT_FROZEN_CRITICAL)

Current crisis implementation and parameters. E45 is the official crisis-protection **class**, not an alpha model. Alpha weakening is not treated as crisis in this official operating logic.

**Canonical status (2026-09-05):** see `research/e45/E45_OFFICIAL_STATUS.md`

| Constant | Value |
|---|---|
| `E45_ARTIFACT_STATUS` | **`NOT_VERIFIED`** |
| `E45_STITCH_STATUS` | **`DEFERRED`** |
| `E45_GOVERNANCE_CLASS` | **`SOFT_FROZEN_CRITICAL`** |
| `E45_LIVE_AUTHORIZATION` | **`NO`** |

**Historical narrative (preserved, not deleted):** handoff/spec “MDD about −13.16%” is labeled **`NOT_VERIFIED_HISTORICAL_NARRATIVE`**. No research CSV/JSON MDD equals −0.1316 (scan 2026-09-04; reconfirmed 2026-09-05). Do **not** treat −13.16% as verified fact or PASS evidence.

**Verified dated-artifact values (use these instead):**

| Metric | Value |
|---|---:|
| Closest lineage validation MDD | **−15.81%** |
| E3 locked winner validation MDD | **−18.49%** |
| Early-stack + E45_E3 MDD | **−20.76%** |
| Early-stack + E45_E3 CAGR | **~10.79%** |

**Lineage distinction:**

- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45` (narrative preserved)
- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`

Retuning E45 thresholds, vote rules, exposure schedules, or handoff cuts is an EXPERIMENTAL challenger. Because E45 is SOFT_FROZEN_CRITICAL, that challenger must use a separate folder, keep the original baseline, and clear the higher validation bar in §1 before any new frozen version. Stitch remains **DEFERRED** until a later human ballot after artifact PASS.

#### Official class vs live cutover (read carefully)

- **SOFT_FROZEN / SOFT_FROZEN_CRITICAL** names the *official strategy-version class* (E16 / E18 / E22 / E45). Class membership alone does **not** mean a module is live-wired into the forward book.
- **Current live cutover default** (ops / debt board): **E16 + E18 + E22_v2s_tw cutover-only**, with live E16 Financial clip **[0.50, 0.95]**. No overlay. No silent Soft-Frozen flip. Live DEFAULT books = **`E22_v2s_tw`**.
- **E45** remains SOFT_FROZEN_CRITICAL as the official crisis-protection *version*, but **`E45_LIVE_AUTHORIZATION=NO`**. Any live attach requires a separate challenger PASS **and** an explicit human cutover PR. The historical −13.16% narrative must not be treated as PASS evidence.
- Research challengers (FIN_CAP_50, MDD L1–L4, E50-A overlays) stay EXPERIMENTAL / paper until that human cutover path completes.

---

## 5. EXPERIMENTAL contents

Never auto-promoted. Includes, without limitation:

### New model

- Feature sets (`TECH2`, `PRICE8`, family scores)
- Ridge / tree / boosting / ensemble / regime-aware models
- Neutralization mode
- Incomplete-session quote-count rules inside E50-A
- Any `frozen_model.json` / `frozen_repair_model.json` selected config (filename does not confer frozen status)

### New threshold

- Breadth-regime cutoffs
- `top_k`, `exit_multiple`, `industry_cap`
- Rank-buffer multiples 1.25 / 1.5 / 2.0
- R1 2.5% average daily turnover ceiling
- Bootstrap positive-excess cutoff 0.70
- “Beat PIT market proxy after costs” promotion test
- NT$20 million liquidity filter
- Audit-only diagnostics (for example gross-exposure > 1.001)
- New crisis-overlay handoff thresholds between Alpha and E45

### New weight

- Utility `CAGR - 0.5 * abs(MDD)`
- New E16 sleeve weights or mix
- A3 overlay simulator costs (14.25bp, 30bp tax, 5bp slippage) when used inside E50-A research, as distinct from the official E18/E22 version
- New cost, slippage, or delay assumptions

### New Router

- A new financial / private-financial / telecom / 0050 / cash router
- New router weights, lookbacks, or sleeve membership rules
- Dynamic-router replacements

Existing routers that already sit inside the official E16 / E18 / E22 / E45 versions remain part of those SOFT_FROZEN versions. A *new* router is EXPERIMENTAL.

### New rebalancing

- `rebalance_every` and any new rebalance calendar
- Rank-buffer / turnover-smoothing schedules used as portfolio rules
- New lot or rebalance-friction numbers used as a trading rule

If a number is not the research-correctness floor and is not one of the four official strategy versions above, it is EXPERIMENTAL.

---

## 6. Layer-specific application

| Layer | HARD_FROZEN | SOFT_FROZEN | EXPERIMENTAL |
|---|---|---|---|
| E16 | Causal clock / PIT / no overwrite | Current official E16 version | New model, threshold, weight, router, or rebalancing |
| E18 | Exact T+1; no same-bar | Current official E18 version | New fee, tax, slippage, lot, or rebalance friction |
| E22 | No future corporate-action leakage | Current official E22 version | New dividend timing or tax treatment |
| E44 | Causal clock contract | — (not an official strategy version) | Extra diagnostic cutoffs |
| E45 | Result must measure crisis, not alpha | Current official version, **SOFT_FROZEN_CRITICAL** | New vote cuts, scales, ramps, handoff thresholds, or acceptance gates |
| E50-A | Overlay result integrity; PIT; walk-forward; Exact T+1 | — (not an official strategy version) | All models, grids, routers, thresholds, weights, rebalancing |
| Future E50 challengers | Inherit the correctness floor | Must keep the then-current E16/E18/E22/E45 versions beside the challenger | Default class for every new rule |

---

## 7. Cursor / agent constraints

Agents may not:

- weaken HARD_FROZEN rules to hit CAGR or MDD targets
- edit E16, E18, E22, or E45 official files in place and still call them the original official version
- promote an EXPERIMENTAL model, threshold, weight, router, or rebalancing rule because a sealed window looks strong
- delete failed experiments
- rebuild A0/A1/A2 without a reproducible upstream defect
- treat `frozen_*.json` output names as governance promotion

Agents must:

- write challengers to a new folder / branch
- classify every new model, threshold, weight, router, or rebalancing rule as EXPERIMENTAL
- keep official-version vs challenger artifacts
- stop performance work when leakage or clock contamination is found
