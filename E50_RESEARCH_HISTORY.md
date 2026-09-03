# E50_RESEARCH_HISTORY.md

# V4.11 -> E50 Research History

## 文件目的
保存整條研究演進，避免 Cursor：
- 重做已經做過的研究
- 重新引入已淘汰方案
- 忘記為什麼某些模組被 Frozen
- 把 E50 誤解成重新設計整套 Portfolio

注意：
以下為研究交接紀錄。
實際程式、資料、結果、參數與 Artifact 必須由 Repository Audit 驗證。

---

## V4.11
研究主題：
台灣金融股價差 / Regime Router。

重點：
- 金融股不同 Regime 行為
- 公股與民營金融差異
- 低頻 Router
- Edge 導向配置

保留：
- Regime Router 概念
- 公股金融特殊季節性與低檔行為研究
- 民營金融不應直接套公股規則

狀態：
**RETAINED FOUNDATION**

---

## V4.12-C
研究主題：
月級 Router 升級為日級 Dynamic Router。

重點：
- 資金依 Edge 強度流動
- Router 內部日級選股
- 不再只做粗粒度月級切換

保留：
- Daily Dynamic Router
- Edge-strength allocation

狀態：
**RETAINED**

---

## V4.12-D
研究主題：
股票級金融研究。

初始資料任務：
- 2880 華南金
- 之後擴至 12 檔金融股
- 2010–2026，後續研究希望擴 2005–2026

重點：
- 股票級資料 QC
- OHLCV
- 事件資料
- 公股金融季節性

狀態：
**RETAINED DATA/RESEARCH FOUNDATION**

---

## E1
研究主題：
Crisis Budget + Turnover Buffer。

目的：
- 控制危機曝險
- 避免為追 Edge 過度換手
- 將交易摩擦納入 Router

狀態：
**RETAINED CONCEPT**

---

## E10
研究主題：
Telecom Harvest -> Financial Reentry Router。

目的：
- 金融沒有 Edge 時，使用電信防守 / 停泊資金
- 金融重新出現 Edge 後再回流

保留：
- 電信不是獨立終點，而是資金 Router 的 defensive component

狀態：
**RETAINED**

---

## E16
研究主題：
公股金融核心訊號 Frozen。

核心配置：
- 公股金融
- 電信三雄
- 0050

定位：
提供 Portfolio 核心底倉。

狀態：
**FROZEN CORE ALLOCATION**

---

## E18
研究主題：
Execution-aware Layer。

目的：
- 將理論訊號轉為可成交策略
- 強化 Exact T+1
- 納入執行限制與換手

狀態：
**FROZEN EXECUTION FOUNDATION**

---

## E22
研究主題：
交易執行 / 換手 / 股利與除權息處理的延伸層。

交接重點：
- 與 E18 一起構成執行層
- 實際細節需由 repo 驗證

狀態：
**FROZEN EXECUTION LAYER（需 repo 驗證細節）**

---

## E21
研究主題：
金融 + 電信 + 0050 補資料 / 回測。

重點：
- 組合性策略開始完整化
- 0050 作為 Beta / allocation alternative

狀態：
**RETAINED SUPPORTING RESEARCH**

---

## E27
研究主題：
短債 / 貨幣型 ETF 導入。

目的：
- 沒有股票 Edge 時，不一定完全持有現金
- 比較 Cash Alternative 的 expected return / risk / liquidity / cost

狀態：
**RETAINED ALTERNATIVE ASSET CONCEPT**

---

## E30
研究主題：
動態民營金融風險預算。

目的：
- 民營金融不直接複製公股金融風險邏輯
- 動態配置 risk budget

狀態：
**RETAINED SEPARATE PATH**

---

## E38
研究主題：
早期危機分類器。

方向：
- acceleration
- cumulative score
- breadth
- correlation
- multi-day deterioration

保留：
危機不能只靠單日大跌判斷。

狀態：
**RETAINED CRISIS CLASSIFICATION**

---

## E43
研究主題：
危機狀態交接。

目的：
把正常市場 / risk transmission / crisis 之間的策略切換做成明確 state transition。

狀態：
**RETAINED**

---

## E44
研究主題：
訊號與成交時鐘稽核。

核心：
- Signal(T)
- Order
- Execution(T+1 Open)

目的：
消除 same-bar execution 與時間洩漏。

狀態：
**FROZEN CAUSAL CLOCK**

---

## E45
研究主題：
Single Exact T+1 Full Model Rebuild。

重要基準：
- MDD 約 -13.16%（需由實體結果驗證）
- 危機保護效果優先保留
- 當時 CAGR 約 10% 左右，報酬仍不足

結論：
- 危機防守核心保留
- 後續不要破壞 E45
- 用新的 Alpha Layer 取回正常市場報酬

狀態：
**FROZEN CRISIS PROTECTION CORE**

---

# E50 系列

## E50-A
研究主題：
Crisis-Controlled Stock Alpha Engine。

核心思想：
正常市場追 Alpha；
危機時關閉進攻層；
E45 保護核心層。

E50-A 不是取代 E45。
也不是取代 Financial / Telecom / 0050 組合。

狀態：
**ACTIVE ALPHA PROGRAM**

---

## E50-A0
Point-in-Time Taiwan Equity Database。

交接紀錄：
- 2004-02-11 ~ 2026-08-28
- 5,551 trading days
- 2,259 ever-traded stocks
- 7,943,783 raw OHLCV rows
- 795,000 PIT eligible rows
- duplicate keys = 0
- OHLC anomalies = 0
- download failures = 0
- adjusted_rows 曾為 0

狀態：
**COMPLETED / VERIFY IN REPO**

---

## E50-A1
Corporate Actions + Causal Financial Layer。

重點：
- announcement / release date
- corporate action
- revenue
- financial data
- trading calendar
- point-in-time availability

狀態：
**COMPLETED / VERIFY IN REPO**

---

## E50-A2
Causal Alpha Factor Engineering。

交接紀錄：
- 約 795,000 rows
- 約 1,347 stocks
- 約 5,300 trading days
- 約 27 ranking/factor-related columns

重點：
- factor panel
- labels
- walk forward
- embargo
- feature dictionary
- manifest / schema / QC

狀態：
**COMPLETED / VERIFY IN REPO**

---

## E50-A3
研究主題：
Causal Alpha Model Training + Exact T+1 Open Simulation。

核心問題：
A2 因子在真正 OOS + Exact T+1 下是否仍有可交易 Alpha？

模型順序：
1. Single Factor
2. Equal Weight Multi-Factor
3. Linear / Regularized
4. Tree / Boosting
5. Ensemble
6. Regime-aware

狀態：
**CURRENT**

---

## E50-A3-R1
研究主題：
修復、驗證、Leakage Attack。

優先：
- ranking timing
- label timing
- universe timing
- survivorship bias
- delisting
- corporate actions
- T+1 execution
- cost
- turnover
- concentration
- regime dependence

狀態：
**CURRENT ACTIVE RESEARCH**

---

# Frozen / Retained / Rejected Summary

Governance classes are defined in `FROZEN_GOVERNANCE.md`.

```
HARD_FROZEN = 研究正確性底線
SOFT_FROZEN = E16 / E18 / E22 / E45 目前正式策略版本
EXPERIMENTAL = 新模型、新門檻、新權重、新 Router、新 rebalancing
```

## HARD_FROZEN
- Exact T+1 / no same-bar execution
- PIT / no look-ahead
- Walk Forward / Embargo
- No survivorship bias
- Never overwrite or delete a prior frozen baseline
- Do not claim PASS without reproducible evidence
- Do not rebuild E50-A0/A1/A2 without a reproducible upstream defect

## SOFT_FROZEN
- E16 目前正式核心配置版本
- E18 目前正式執行層版本
- E22 目前正式股利 / 經濟報酬版本
- E45 目前正式危機保護版本

## RETAINED (inside the current official E16 / E18 / E22 / E45 versions)
- Financial Router
- 公股 / 民營金融分流
- Telecom Harvest -> Financial Reentry
- 0050 as Beta / Risk-on / indicator / allocation option
- Cash / Short Bond alternative
- Crisis classifier
- Dynamic Router
- Dividend total-economic-return simulation

A *new* router or *new* rebalancing rule is EXPERIMENTAL. It does not edit the official versions in place.

## REJECTED / NOT CORE
- 0050 leveraged ETF (0050 正二) is not in the current official E16 version

## EXPERIMENTAL
- E50-A3 / E50-A3-R1 Alpha model, grids, costs, turnover ceiling, bootstrap cutoff
- 未來的 advanced model / regime-aware Alpha
- 新模型、新門檻、新權重、新 Router、新 rebalancing，直到 explicitly promoted
