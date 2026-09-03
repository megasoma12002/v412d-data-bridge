# CURSOR_RULES.md

## 0. Required Context
開始研究前必須讀：
- FROZEN_STRATEGY_SPEC.md
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
