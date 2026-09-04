# FROZEN_STRATEGY_SPEC.md

# E50 Frozen Strategy Specification

## 0. 文件目的
本文件定義目前研究中「不可被 Cursor 任意重寫」的 Frozen Portfolio Baseline。
規則分級、晉升路徑與不得自動凍結的實驗門檻，以 `FROZEN_GOVERNANCE.md` 為準。

E50-A 不是一套取代既有策略的新 Portfolio。
它是加在既有核心組合上的 Alpha Overlay。

整體架構：

Market
-> E16 Core Allocation
-> E18 + E22 Execution Layer
-> E50-A Alpha Attack Layer
-> E45 Crisis Protection Core

只有獨立 Research Branch / Experiment 可以測試 Frozen 規則的替代方案。
不得直接覆蓋 Baseline。

---

## 1. 四層 Frozen 架構

### Layer 1 — 核心配置：E16
角色：
- 公股金融
- 電信三雄
- 0050
- 提供主要底倉與基礎資產配置

核心原則：
- 核心組合不是因為 E50 Alpha 轉弱就全部退出
- 正常市場下核心持續運作
- Alpha 層只是額外進攻資金
- 核心層與 Alpha 層必須分帳觀察

狀態：
**FROZEN BASELINE**

---

### Layer 2 — 交易執行：E18 + E22
角色：
- Exact T+1 Open execution
- 換手限制
- 交易成本
- 股利
- 除權息
- 實際可成交性

核心原則：

Information(T)
-> Signal(T)
-> Order
-> Next Trading Day
-> T+1 Open Fill

禁止：
- Close(T) 訊號同價成交
- Same-bar execution
- Future corporate action leakage
- 用理論報酬替代實際成交報酬

股利 / 除權息要能支援：
1. 持有至除息
2. 除息前賣出

若持有至除息，需考慮：
- Ex-dividend
- Dividend receivable
- Payment date
- Tax
- Supplementary premium
- Reinvestment date
- Odd lot
- Fill / non-fill

目前正式執行路徑（2026-09-04 起）：
- **`E22_v2_CASH_EX_OFFICIAL_PATH`** — `scripts/e22_v2_forward_pipeline.py` / `forward/e22_v2/`
- 在 Exact T+1 成交後，於 `cash_ex_date` 將現金股利記入 cash
- 先前 `forward/e21/` 路徑永久保留可讀，不得回寫改史

狀態：
**FROZEN EXECUTION BASELINE（E22_v2）**

---

### Layer 3 — Alpha 進攻：E50-A
角色：
- 從約 1,347 檔可用台股 Universe 中尋找因果 Alpha
- 正常市場提高報酬
- 不取代 E16 核心組合

核心原則：
- E50-A 是 Alpha Overlay
- Alpha 弱時先降低進攻層
- 不因 Alpha 弱就自動清空核心底倉
- Alpha 層必須服從 E45 危機控制
- Alpha 層必須使用 PIT + Walk Forward + Exact T+1

長期研究目標：
- CAGR >= 20%
- Maximum Drawdown 約 10–15%

但不能以以下方式換取績效：
- leakage
- hidden leverage
- survivorship bias
- unrealistic fill
- future-aware universe
- same-bar execution

狀態：
**ACTIVE RESEARCH / FROZEN ROLE**

目前研究：
**E50-A3-R1**

---

### Layer 4 — 危機防守：E45
角色：
- 危機開始傳導時降低股票曝險
- 控制整體 Portfolio Drawdown
- 作為 E50 的 Protection Core

既有重要基準：
- Single Exact-T+1 Full Model
- MDD 約 -13.16%（需由 repo/result 驗證）

危機處理順序：

Normal
-> 核心組合 + Alpha

Alpha weakening
-> 降低 Alpha Layer

Risk transmission
-> 關閉 / 大幅降低 Alpha

Crisis
-> E45 降低整體股票曝險

重要：
E45 不是 Alpha Model。
E45 是危機保護層。

狀態：
**FROZEN CRISIS CORE**

---

## 2. Frozen Portfolio 運作邏輯

### Normal Market
- E16 核心組合持續運作
- E18/E22 控制執行
- 部分資金配置給 E50-A Alpha
- Alpha Layer 追求額外報酬

### Alpha 訊號轉弱
- 先減少 Alpha Attack Layer
- 不一定減少 E16 核心持股
- 不把 Alpha 弱直接解讀成全面危機

### Risk Transmission
當危機訊號開始擴散：
- Alpha Layer 優先退出
- 核心層降低風險
- 準備由 E45 接管

### Crisis
- E45 成為主要風險控制層
- 目標是降低整體股票曝險
- 不以追求短期 Alpha 為第一優先

---

## 3. 組合不是單一路徑

整體 Portfolio 應允許：

E50 Stock Alpha
<-> Financial
<-> Telecom
<-> 0050
<-> Cash / Short Bond

但 Crisis 時：
-> E45 Protection Core

Router 的目標：
**把資金配置給當下 Edge / Risk Ratio 較佳的策略。**

不是預測每一天漲跌。

---

## 4. 既有保留決策

### RETAINED
- 公股金融作為重要核心研究資產
- 民營金融走不同風險路徑
- Telecom Harvest -> Financial Reentry
- 0050 作為 Beta / Risk-on / Crisis indicator / allocation alternative
- Cash / 短債作為低 Edge 時的資金替代
- Crisis / Normal Market 分離
- Single-day Panic 與 persistent crisis 分離
- Exact T+1
- Point-in-Time
- Walk Forward
- Embargo
- Transaction cost awareness

### REJECTED / NOT CORE
- 0050 正二：曾評估，但不納入核心策略

---

## 5. Cursor 不得做的事

不得：
- 把 E50-A 當成整套 Portfolio 重建
- 刪除 E16 核心配置
- 用 E50 Alpha 直接取代 Financial / Telecom / 0050 架構
- 修改 E45 Crisis Core 後還稱為原 Baseline
- 將 Alpha 弱直接視為 Crisis
- 未經獨立實驗就加入槓桿 ETF
- 重新下載全部資料只因股票數不同
- 為了提高 CAGR 破壞 Exact T+1 或 PIT
- 為了績效放寬任何 HARD_FROZEN 規則
- 覆蓋或刪除先前 Frozen Baseline
- 把 EXPERIMENTAL 新模型、新門檻、新權重、新 Router、新 rebalancing 自動升格為 Frozen

---

## 6. Frozen 修改流程

規則分三級，詳見 `FROZEN_GOVERNANCE.md`：

- HARD_FROZEN = 研究正確性底線。不得為績效放寬（PIT、no look-ahead、no survivorship、causal clock、Exact T+1、Walk Forward、Embargo、no future-aware normalization / ranking / model selection）。
- SOFT_FROZEN = E16 / E18 / E22 / E45 目前正式策略版本。只能用獨立 challenger 挑戰，且必須保留原正式版本。
- SOFT_FROZEN_CRITICAL = E45。只能用獨立 challenger 挑戰，且驗證門檻高於 E16 / E18 / E22。
- EXPERIMENTAL = 新門檻、新權重、bootstrap cutoff、rebalance、model-selection、新 Router、新 Alpha、新 acceptance gate。預設如此，不得自動升格為 Frozen。

任何 Frozen 規則若要測試替代方案：

1. 建立新的 experiment branch
2. 清楚定義 hypothesis
3. 保留 original frozen baseline
4. 不覆蓋、不刪除原結果
5. 輸出：
   - baseline
   - challenger
   - incremental benefit
   - additional risk
   - OOS stability
   - transaction-cost impact
6. 結果標記：
   - PASS
   - FAIL
   - INCONCLUSIVE

晉升路徑：

FROZEN_BASELINE
-> CHALLENGER
-> OOS VALIDATION
-> COST VALIDATION
-> STRESS / MONTE CARLO VALIDATION
-> GOVERNANCE REVIEW
-> EXPLICIT APPROVAL
-> NEW FROZEN VERSION

只有有可重現證據且經 explicit approval 後，才有資格發布新的 Frozen Version。
前一版 Frozen Baseline 必須繼續可讀。
