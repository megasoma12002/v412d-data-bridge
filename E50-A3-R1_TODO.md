# E50-A3-R1_TODO.md

## Mission
修復並驗證 E50-A3，使 A2 因子能在真正 causal / OOS / Exact T+1 環境下接受測試。

## Phase 1 — Full Repository Audit
- [ ] E16
- [ ] E18
- [ ] E22
- [ ] E44
- [ ] E45
- [ ] E50-A0
- [ ] E50-A1
- [ ] E50-A2
- [ ] E50-A3
- [ ] E50-A3-R1
- [ ] Financial Router
- [ ] Telecom Router
- [ ] 0050 modules
- [ ] Cash/Short Bond modules
- [ ] Crisis modules

每項標：
FOUND / INCOMPLETE / MISSING / SUSPICIOUS

先產 audit report，不修改程式。

## Phase 2 — Dataset Audit
- [ ] version
- [ ] date range
- [ ] rows
- [ ] symbols
- [ ] schema
- [ ] duplicate keys
- [ ] hashes
- [ ] PIT eligibility
- [ ] corporate actions
- [ ] delisted stocks
- [ ] announcement timing
- [ ] feature timing
- [ ] label timing
- [ ] trading calendar

## Phase 3 — Frozen Strategy Audit
驗證：
- [ ] E16 是否真為核心配置
- [ ] E18/E22 是否真負責執行
- [ ] E44 是否落實 Exact T+1
- [ ] E45 是否為危機防守核心
- [ ] E50-A 是否只作 Alpha Overlay
- [ ] Alpha 弱與 Crisis 是否有分開
- [ ] 0050 正二是否未進核心

## Phase 4 — Exact T+1 Audit
逐筆抽樣：
Information Date
Feature Date
Signal Date
Order Date
Execution Date
Execution Price
Position Start
PnL Start

驗收：
- [ ] 無 same-bar fill
- [ ] next trading day 正確
- [ ] suspension / holiday 正確
- [ ] missing open 有 policy
- [ ] corporate action 不污染 execution

## Phase 5 — Leakage Attack
- [ ] global normalization
- [ ] full-sample ranks
- [ ] future labels
- [ ] revised financial data
- [ ] future universe
- [ ] future delisting knowledge
- [ ] hyperparameter leakage
- [ ] threshold leakage
- [ ] feature selection leakage

## Phase 6 — Baseline Alpha
順序：
- [ ] Single Factor
- [ ] Equal Weight Multi-Factor
- [ ] Linear / Regularized

先回答：是否存在穩定 OOS Alpha？

## Phase 7 — Cost & Stability
- [ ] gross/net
- [ ] commission
- [ ] tax
- [ ] slippage
- [ ] turnover
- [ ] yearly results
- [ ] rolling results
- [ ] regime results
- [ ] concentration
- [ ] exposure

## Phase 8 — Adversarial Testing
- [ ] higher cost
- [ ] higher slippage
- [ ] one-day extra delay
- [ ] missing trades
- [ ] factor noise
- [ ] price gaps
- [ ] reduced liquidity
- [ ] crisis misclassification

## Phase 9 — Advanced Models
只有 baseline 通過後才進：
- [ ] Tree
- [ ] Boosting
- [ ] Ensemble
- [ ] Regime-aware

## Phase 10 — Portfolio Integration
- [ ] E16 Core
- [ ] E18/E22 Execution
- [ ] E50-A Alpha
- [ ] E45 Crisis handoff
- [ ] combined CAGR
- [ ] combined MDD
- [ ] transition costs
- [ ] false crisis signals
- [ ] Alpha-off / Core-on behavior

## Governance
Follow `FROZEN_GOVERNANCE.md`.

- HARD_FROZEN = 研究正確性底線. Clock / PIT / walk-forward / embargo / no future-aware selection cannot be relaxed to chase CAGR.
- SOFT_FROZEN = E16 / E18 / E22 / E45 目前正式策略版本. Challengers go to a new folder.
- SOFT_FROZEN_CRITICAL = E45. Separate challenger plus a higher validation bar.
- EXPERIMENTAL = 新模型、新門檻、新權重、新 Router、新 rebalancing、bootstrap、model-selection、acceptance gate.
- R1 numeric gates (2.5% turnover, 0.70 bootstrap, beat-proxy, grid, overlay costs) are EXPERIMENTAL.
- They do not become frozen because a sealed window looks strong.

Promotion, if ever proposed:
FROZEN_BASELINE -> CHALLENGER -> OOS VALIDATION -> COST VALIDATION -> STRESS / MONTE CARLO VALIDATION -> GOVERNANCE REVIEW -> EXPLICIT APPROVAL -> NEW FROZEN VERSION

## PASS Gate
R1 不以 CAGR >=20% 單獨判 PASS。

至少：
- causal clock PASS
- frozen architecture verified
- Exact T+1 PASS
- leakage audit PASS
- OOS alpha survives
- costs survive
- stability acceptable
- reproducible
