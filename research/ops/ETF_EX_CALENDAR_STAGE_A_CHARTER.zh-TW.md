# ETF 除息日曆 — Stage A 研究憲章（只測 paper）

日期：2026-09-11  
狀態：**OPEN／PAPER PENDING**（尚未跑 Stage A screen · **不上 live**）  
人類：**開一張很窄的 ETF ex-calendar Stage A charter（只測 paper、不上 live）**  
Soft-Frozen **KEEP** · live **KD_OPT／TEL_EQUAL KEEP** · E45 **OFF** · Soft-assist／Sleeve-tilt observe **不變**

## 在問什麼

用**已知的 0050 現金除息日曆**（月曆代理／精確 ex 前窗口）做規則型進出，成本後能否 tip-clean 勝過 **`BUY_HOLD_0050`**，以及／或與 **`LIVE_STACK`** 共存？

**不做：** 虛構 `announcement_date`、改 live、自動拼 Soft-assist／sleeve。

## 為什麼很窄

| 項 | 說明 |
|---|---|
| 標的 | Stage A **只做 0050**（E22 code `50`） |
| 資料 | ex／pay／金額 OK；announce 全空屬結構缺口，**不靠本憲章填** |
| 執行器 | 日曆擇時，不是 Soft-assist 個股加分、不是 sleeve-tilt、不是乾粉回撤 |

## Live 對照（不動）

FINBAND `[0.60,0.90]` + `KD_OPT` + `TEL_EQUAL` + E45 OFF · 500M · lot 1000 · `E22_v2s_tw`

## 機制（摘要）

| 來源 | 規則 |
|---|---|
| `MONTH_PROXY`（主） | ≥2016：僅 **1／7** 月前 W 個交易日；更早：僅 **10** 月。W∈{10,15} |
| `EXACT_EX`（敏感度） | 用已實現 `cash_ex_date`，持有 **[T−N, T−1]**。N∈{10,20,40} |

書：`BUY_HOLD_0050` · `LIVE_STACK` · 窗口內滿倉 0050（其餘現金）· 窗口外改為 BH 的 overlay。總書 ≤ **~14**。

## 閘門

tip／heldout／sealed；標籤 `NO_LIFT` · `COEXIST_NO_LIFT` · `BEATS_BH_ONLY` · `BEATS_LIVE`。  
beat-live 才可在人類要求下開 observe；**永不自動上 live**。

## 非動作

不上 Soft-Frozen／KD／TEL／E45；不改 Soft-assist／sleeve observe；不填 announce；不做多 ETF／sleeve 加權 overlay。

## 下一步

寫 `scripts/e16_etf_ex_calendar_screen.py` → `ETF_EX_CALENDAR_SCREEN.md` → 更新 register。

英文全文：`ETF_EX_CALENDAR_STAGE_A_CHARTER.md`
