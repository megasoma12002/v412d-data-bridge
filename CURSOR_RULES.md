# CURSOR_RULES.md

## 0. Required Context
開始研究前必須讀：
- FROZEN_STRATEGY_SPEC.md
- FROZEN_GOVERNANCE.md
- E50_RESEARCH_HISTORY.md
- HANDOFF.md
- E50-A3-R1_TODO.md

## 1. Never Restart Blindly
先搜尋 repository，再決定缺什麼。
不得因交接文件提到某檔案就假設它存在；
也不得因第一眼沒看到就直接重建。

## 2. Frozen Baseline
以下不得直接修改：
- E16 Core Allocation
- E18 + E22 Execution Layer
- E44 Exact T+1 Clock
- E45 Crisis Protection Core
- PIT
- Walk Forward
- Embargo
- No Look-ahead
- No Survivorship Bias
- 0050 正二不進核心

若要挑戰 Frozen Baseline：
建立獨立 branch / experiment。
不得覆蓋或刪除原 baseline。

完整分級與晉升路徑見 `FROZEN_GOVERNANCE.md`。

## 2.1 Frozen Governance
Every rule is HARD_FROZEN, SOFT_FROZEN, or EXPERIMENTAL.

HARD_FROZEN = 研究正確性底線. Cannot be relaxed for performance. This is the causal floor: Exact T+1, PIT, walk-forward, embargo, no look-ahead, no survivorship, and no overwrite / no false PASS.

SOFT_FROZEN = E16 / E18 / E22 / E45 目前正式策略版本. Challenge only with a separate experiment that keeps the original official version.

EXPERIMENTAL = 新模型、新門檻、新權重、新 Router、新 rebalancing. Never becomes frozen automatically.

Promotion path:

FROZEN_BASELINE
-> CHALLENGER
-> OOS VALIDATION
-> COST VALIDATION
-> STRESS / MONTE CARLO VALIDATION
-> GOVERNANCE REVIEW
-> EXPLICIT APPROVAL
-> NEW FROZEN VERSION

This governance applies to E16, E18, E22, E45, E50-A, and all future E50 challengers.

## 3. Causal Clock
Information(T)
-> Feature(T)
-> Signal(T)
-> Order
-> Next Trading Day
-> T+1 Open Fill

禁止 same-bar execution。

## 4. Portfolio Semantics
E50-A = Alpha Overlay。
不得把 E50-A 當整套 Portfolio。

Alpha weak:
先降 Alpha。

Crisis:
再由 E45 控制整體曝險。

## 5. Point-in-Time
禁止：
- future financial releases
- revised data leaked backward
- future constituent membership
- future corporate actions
- future normalization statistics
- future delisting knowledge

## 6. Walk Forward
所有 fit / transform / calibration 只使用 train window。
Validation/Test 不得回灌。

## 7. Reproducibility
每個 experiment 保存：
- hypothesis
- code/config version
- dataset version/hash
- train/validation/test windows
- params
- metrics
- diagnostics
- decision
- failure reason

## 8. Performance
目標 CAGR >=20%，MDD 約10–15%。
但不得用 leakage、hidden leverage、unrealistic fill、same-bar execution 換績效。

## 9. Stop Condition
發現資料或時鐘污染時：
停止績效優化，
先建立 reproducible bug report。
