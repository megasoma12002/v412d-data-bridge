# HANDOFF.md — E50 Full Research Handoff v2

## 0. Read Order
Cursor 必須依序讀：
1. `research/STRATEGY_DEBT_BOARD.md` ← **現行 live / paper 狀態（先讀）**
2. `FROZEN_GOVERNANCE.md`（尤其 §4：SOFT_FROZEN class ≠ live cutover）
3. `FROZEN_STRATEGY_SPEC.md`（角色定義；非 live wiring 證明）
4. `E50_RESEARCH_OPERATING_RULES.md`
5. `E50_RESEARCH_HISTORY.md`
6. `CURSOR_RULES.md`
7. `E50-A3-R1_TODO.md`（歷史研究帳本）
8. 本文件

## 0.1 Live cutover default（強制）

**現行 live（SSOT；以 `research/ops/OPS_STATUS.md` 為準）：** `forward/e21` = **E16 + Exact T+1 E18 + E22_v3_recv_pay_effdelay**（Stage-E DEFAULT）+ **整股一張=1000** + **起始資本 500M**。  
**Live Soft-Frozen clips：** FIN **[0.60, 0.90]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.35]**。  
**Within-sleeve：** FIN **`KD_OPT`** · TEL **`TEL_EQUAL`**。  
**Live overlay：** **`FUSE_ADDITIVE`** + **`DH_dd06`**（ACCEPT `LIVE_DH_FUSE_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`）。  
**Legacy A05 blend stitch：** unused（`LIVE_E45_STITCH=False`）。  
**Tip books：** catch-up **CONFIRMED** 2026-09-21（`ACCEPT_TIP_BOOKS_ALIGN_V3.md`）— **no history rewrite**；歷史 `nav.csv` 列 immutable KEEP。  
術語：`TW_SHARE_LOT_DEFINITIONS.md` · 資本：`scripts/portfolio_capital.py` · 組合：`research/ops/RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md`。  
**禁止：** 未授權改寫歷史、獨立 Soft／Sleeve observe 靜默 ops auto-fuse、未 ballot 重開 ARCHIVE 線、merge R4 `settled_cash` → `portfolio_state.cash`。

| Module | Official class | Live? |
|---|---|---|
| E16 / E18 / E22_v3_recv_pay_effdelay | SOFT_FROZEN + Stage-E DEFAULT | **Yes (core)** |
| E22_v2s_tw / E22_v2s_tw_effex | preserved / FUSE offense history | **No** as tip DEFAULT |
| FIN within-sleeve `KD_OPT` | live ACCEPT 2026-09-09 | **Yes** |
| TEL within-sleeve `TEL_EQUAL` | live KEEP | **Yes** |
| `FUSE_ADDITIVE` + `DH_dd06` | live ACCEPT 2026-09-13 | **Yes** |
| Soft-assist / Sleeve-tilt **independent** observes | paper | **No**（獨立 cutover 仍 BLOCKED；FUSE 為專用配方） |
| E50-A | EXPERIMENTAL / RESEARCH_ONLY | **No** |
| E45 legacy A05 blend stitch | SOFT_FROZEN_CRITICAL class | **No**（`LIVE_E45_STITCH=False`） |
| FIN_CAP_50 / L4_DD_PATH / FINCAP BLEND_025 | paper dual-ledger | **No** |

細節：`research/ops/OPS_STATUS.md` · `research/STRATEGY_DEBT_BOARD.md`。

## 1. 專案定位
這不是新專案。
這是從 V4.11 / V4.12 一路演化到 E45，再進入 E50 Alpha Program 的延續研究。

禁止從零重新設計。

## 2. 現行 Portfolio 架構
Frozen Portfolio Baseline（**角色定義 — 不是 live wiring 證明**）：

E16 Core Allocation
+
E18/E22 Execution
+
E50-A Alpha Overlay   ← RESEARCH_ONLY；未 live
+
E45 Crisis Protection ← official class only；未 auto-live

**Live 實況：** 見 §0.1。四層合帳引擎尚未 wiring。債務看板：`research/STRATEGY_DEBT_BOARD.md`。

E50-A 不是整套 Portfolio。
它只負責正常市場的 Alpha 進攻（研究層）。

## 3. 核心運作邏輯（目標架構 / 研究願景 — 非現行 live）
Normal Market（目標）:
- E16 核心持續運作
- 部分資金配置 E50-A（**目前未 live**）

Alpha weak:
- 降低 Alpha Layer
- 不一定動核心底倉

Risk transmission:
- 優先關閉 Alpha
- 降低核心風險

Crisis（目標）:
- E45 接管整體風險控制（**目前未 live-wire**）

## 4. Current Research
權威狀態以 `research/STRATEGY_DEBT_BOARD.md` 為準。摘要：

- **Track A S9A1**：paper/monitor KEEP  
- **Track B S1**：`STOP_S1_HELDOUT_KEEP_TRACK_A`  
- **FIN_CAP_50**：dual-paper OPERATING；cutover **`NOT_READY_SEALED_CAGR`**  
- **L4_DD_PATH_08_50**：`PASS_HELDOUT_L4`；dual-paper OPERATING；cutover FROZEN（≠ Soft-Frozen flip）  
- **Stage-8**：saturated — 不要重跑 TECH2 grids  

歷史：E50-A3-R1 turnover/held-out 診斷已收尾（`MIXED_HELDOUT`），仍 `RESEARCH_ONLY`。  
執行帳本：`DEFAULT_BOOKS_VERSION = E22_v3_recv_pay_effdelay`（Stage-E；`E22_v2s_tw` / `E22_v2s_tw_effex` 僅保留為對照／FUSE offense 歷史帳）。

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

現階段優先（權威細節見 `research/STRATEGY_DEBT_BOARD.md`）：
1. ~~合併策略債收尾~~ — done (#35)
2. ~~Stage-8 failure-signature / stress-sleeve~~ — **SATURATED**; do not re-grid TECH2
3. ~~Track B S1~~ — `STOP_S1_HELDOUT_KEEP_TRACK_A`
4. **Operate:** Track A S9A1 paper/monitor; FIN_CAP_50 paper (cutover frozen); L4 dual-paper (cutover frozen)
5. **禁止：** live overlay、改寫歷史 NAV、發明 E45 the retired handoff MDD narrative、把 dual-paper／held-out PASS 當 Soft-Frozen flip、重跑已飽和 Stage-8 grids
