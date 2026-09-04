# E50-A3-R1_TODO.md

## Mission
修復並驗證 E50-A3，使 A2 因子能在真正 causal / OOS / Exact T+1 環境下接受測試。

## Phase 1 — Full Repository Audit
- [x] E16 — INCOMPLETE (live E21 target path; no e16 package / no full-history NAV)
- [x] E18 — FOUND (`scripts/e21_forward_pipeline.py`, `forward/e21/`)
- [x] E22 — FOUND (`data/dividend_events/` + `e22_dividend_accounting.py`; **wired into E21 as E22_v2s cutover-forward** as of PR #30; historical live NAV not rewritten). Named TW odd-lot: `E22_v2s_tw` (not default).
- [x] E44 — INCOMPLETE (clock FOUND in E18/A3; no e44 package)
- [x] E45 — INCOMPLETE (named `scripts/e45_crisis_core.py` challenger exists; MDD −13.16% = **`NOT_VERIFIED_NO_ARTIFACT_MATCH`**)
- [x] E50-A0 — FOUND (pinned artifact + QC)
- [x] E50-A1 — FOUND
- [x] E50-A2 — FOUND
- [x] E50-A3 — FOUND (reproduced)
- [x] E50-A3-R1 — FOUND (reproduced, RESEARCH_ONLY; turnover/held-out diagnosis = **MIXED_HELDOUT**, no live wire)
- [x] Financial Router — FOUND
- [x] Telecom Router — FOUND
- [x] 0050 modules — FOUND (leveraged 0050 not in core)
- [x] Cash/Short Bond modules — INCOMPLETE
- [x] Crisis modules — FOUND (not a single E45 controller)

See `E50_HANDOFF_VERIFICATION.md`.

每項標：
FOUND / INCOMPLETE / MISSING / SUSPICIOUS

先產 audit report，不修改程式。

## Phase 2 — Dataset Audit
Verified in `E50_HANDOFF_VERIFICATION.md` §4 and `reports/dataset_manifest.json`.
- [x] version
- [x] date range
- [x] rows
- [x] symbols
- [x] schema
- [x] duplicate keys
- [x] hashes
- [x] PIT eligibility
- [x] corporate actions
- [x] delisted stocks
- [x] announcement timing
- [x] feature timing
- [x] label timing
- [x] trading calendar

## Phase 3 — Frozen Strategy Audit
Verified in `E50_HANDOFF_VERIFICATION.md` §2. Combined four-layer engine is not wired.
- [x] E16 是否真為核心配置 — live E21 path yes; full-history NAV missing
- [x] E18/E22 是否真負責執行 — E18 yes; E22 dataset yes; **E22_v2s cutover wired in E21** (no history rewrite)
- [x] E44 是否落實 Exact T+1 — clock yes; no e44 package
- [x] E45 是否為危機防守核心 — role yes; named challenger module; **−13.16% NOT_VERIFIED**
- [x] E50-A 是否只作 Alpha Overlay — contract yes; not a live overlay on E16
- [x] Alpha 弱與 Crisis 是否有分開 — spec yes; combined engine no
- [x] 0050 正二是否未進核心 — yes

## Phase 4 — Exact T+1 Audit
Verified in `E50_HANDOFF_VERIFICATION.md` §5.
- [x] 無 same-bar fill
- [x] next trading day 正確
- [x] suspension / holiday 正確 — holidays via trading calendar; no dedicated halt feed
- [x] missing open 有 policy
- [x] corporate action 不污染 execution — raw open for fills; 30 A1 CA timing residuals remain

## Phase 5 — Leakage Attack
Verified in `E50_HANDOFF_VERIFICATION.md` §6.
- [x] global normalization
- [x] full-sample ranks
- [x] future labels
- [x] revised financial data
- [x] future universe
- [x] future delisting knowledge
- [x] hyperparameter leakage
- [x] threshold leakage
- [x] feature selection leakage

## Phase 6 — Baseline Alpha
Handoff verification complete. R1 remains `RESEARCH_ONLY` / held-out **`MIXED_HELDOUT`**.
Debt board: `research/STRATEGY_DEBT_BOARD.md`.

**Next (only):** Stage-8 failure-signature / stress-sleeve OOF → one held-out.  
**Not next:** reb micro-grids, live overlay, gate promotion, E45 invent.

順序（歷史清單；勿在 R1 未過門前當主線重跑）：
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
Follow `FROZEN_GOVERNANCE.md` and `E50_RESEARCH_OPERATING_RULES.md`.

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

Handoff decision: **HANDOFF_COMPLETE_WITH_WARNINGS** (`E50_HANDOFF_VERIFICATION.md`).
R1 numeric gates stay EXPERIMENTAL. E45 is SOFT_FROZEN_CRITICAL. Do not auto-promote.
