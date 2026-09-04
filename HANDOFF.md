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
目前 Frozen Portfolio Baseline（**角色定義**）：

E16 Core Allocation
+
E18/E22 Execution
+
E50-A Alpha Overlay
+
E45 Crisis Protection

**Live 實況（2026-09-04）：** `forward/e21` = E16 + Exact T+1 E18 + **E22_v2s cutover-forward**（不改寫歷史 NAV）。  
E50-A = `RESEARCH_ONLY`，**未**配置 live 資金。E45 = named challenger；MDD ≈ −13.16% = **`NOT_VERIFIED`**。  
四層合帳引擎尚未 wiring。債務看板：`research/STRATEGY_DEBT_BOARD.md`。

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
**E50-A3-R1** — turnover/held-out 診斷已收尾：OOF 可過 TO（reb→42），held-out 為 **`MIXED_HELDOUT`**；仍 `RESEARCH_ONLY`，禁止 live-wire。  
下一研究重心：失敗體制 / stress-sleeve（Stage-8 路徑），不是再微調 reb。  
執行帳本：`E22_v2s` default；台灣畸零股 named `E22_v2s_tw`（面額 CIL，待明確 promote）。

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
Audit / Exact T+1 / R1 reproduce / turnover·held-out 診斷 **已完成**（見 `E50_HANDOFF_VERIFICATION.md`、PR #19 closeout）。

現階段優先：
1. ~~合併策略債收尾~~ — done (#35)
2. ~~Stage-8 failure-signature / stress-sleeve~~ — **SATURATED** (see `research/e50a/STAGE8_STRESS_SLEEVE_CLOSEOUT.md`); do not re-grid TECH2 cash/sleeves
3. **Next:** Option-2 S9A1 paper/monitor (not live) **or** new stress return engine under a new EXPERIMENTAL id
4. **禁止：** live overlay、改寫歷史 NAV、發明 E45 −13.16%、升格實驗門檻「硬過關」、重跑已飽和 Stage-8 grids
