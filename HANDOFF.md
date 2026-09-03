# HANDOFF.md — E50 Full Research Handoff v2

## 0. Read Order
Cursor 必須依序讀：
1. `FROZEN_STRATEGY_SPEC.md`
2. `FROZEN_GOVERNANCE.md`
3. `E50_RESEARCH_OPERATING_RULES.md`
4. `E50_RESEARCH_HISTORY.md`
5. `CURSOR_RULES.md`
6. `E50-A3-R1_TODO.md`
7. 本文件

## 1. 專案定位
這不是新專案。
這是從 V4.11 / V4.12 一路演化到 E45，再進入 E50 Alpha Program 的延續研究。

禁止從零重新設計。

## 2. 現行 Portfolio 架構
目前 Frozen Portfolio Baseline：

E16 Core Allocation
+
E18/E22 Execution
+
E50-A Alpha Overlay
+
E45 Crisis Protection

E50-A 不是整套 Portfolio。
它只負責正常市場的 Alpha 進攻。

## 3. 核心運作邏輯
Normal Market:
- E16 核心持續運作
- 部分資金配置 E50-A

Alpha weak:
- 降低 Alpha Layer
- 不一定動核心底倉

Risk transmission:
- 優先關閉 Alpha
- 降低核心風險

Crisis:
- E45 接管整體風險控制

## 4. Current Research
目前：
**E50-A3-R1**

目標：
先驗證因果 Alpha 是否存在，
再做績效優化。

## 5. Long-term Target
- CAGR >= 20%
- MDD 約 10–15%

但優先順序：
1. causal correctness
2. no leakage
3. exact T+1
4. OOS survival
5. drawdown control
6. transaction-cost survival
7. CAGR optimization

## 6. Frozen Baseline
不得擅自修改：
- E16
- E18/E22
- E44 timing
- E45
- PIT
- Walk Forward
- Embargo
- No Look-ahead
- No Survivorship Bias
- 0050 正二不進核心

Governance（`FROZEN_GOVERNANCE.md`）適用於 E16、E18、E22、E45，以及所有未來 E50 challenger：

- HARD_FROZEN = 研究正確性底線，不得為績效放寬
- SOFT_FROZEN = E16 / E18 / E22 / E45 目前正式策略版本；只能用獨立實驗挑戰，且必須保留原正式版本
- SOFT_FROZEN_CRITICAL = E45；challenger 必須用更高驗證門檻
- EXPERIMENTAL = 新門檻 / 權重 / bootstrap / rebalance / model-selection / Router / Alpha / acceptance gate；不得自動變成 Frozen

晉升路徑：
FROZEN_BASELINE -> CHALLENGER -> OOS VALIDATION -> COST VALIDATION -> STRESS / MONTE CARLO VALIDATION -> GOVERNANCE REVIEW -> EXPLICIT APPROVAL -> NEW FROZEN VERSION

不得覆蓋或刪除先前 Frozen Baseline。

## 7. Repository Audit Rule
本交接文件中的「完成」是研究交接紀錄。
Cursor 必須檢查實體 repo / dataset / artifacts / logs 後才能確認。

如果某元件：
- 沒找到 -> MISSING
- 找到但不完整 -> INCOMPLETE
- 時鐘/資料可疑 -> SUSPICIOUS
- 有可重現實體證據 -> FOUND

不得只相信文件。

## 8. Current Mission
第一步不是訓練模型。
第一步是完整 Repository Audit + Dataset Audit + Exact T+1 Audit。

之後才從最新有效 checkpoint 繼續 E50-A3-R1。
