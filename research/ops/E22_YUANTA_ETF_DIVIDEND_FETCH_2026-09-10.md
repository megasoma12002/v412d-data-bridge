# Yuanta ETF dividend fetch research (2026-09-10)

Human: **「可以研究怎麼抓嗎」**（元大 ETF 配息頁 / `0050`）  
Soft-Frozen / live wire: **unchanged**.

## Verdict

**可以機器抓**官方除息日、發放日、每股配息；**不能**從此 API 補 `announcement_date`。

| 目標欄位 | 結果 |
|---|---|
| `cash_ex_date` | OK — `SHARE_DATE` |
| `cash_payment_date` | OK — `PAY_DATE` |
| `cash_dividend` | OK — `DIVIDEN_PER_UNIT` |
| `announcement_date` | **無欄位** — 無法填 ledger 殘缺 ×27 |

對 `0050` ledger：27/27 ex 對齊、pay/amount **0 diffs**；API 另有 2005–2009 共 5 筆較舊紀錄（ledger 未收）。

## 怎麼抓（可重現）

1. **內部基金代號**：`STK_CD=0050` → `FUND_ID=1066`（`FuncId=FundList`）。  
   人類頁面 `?fundid=0050` 會打錯；正確為  
   `https://www.yuantafunds.com/myfund/dividend/history?fundid=1066`。  
   `yuantaetfs.com/product/detail/0050/dividend` 是 Nuxt SPA，配息表連到上述 funds 站。

2. **API**（來自 Nuxt `$getAPI`，預設 `/api/trans`）:

```text
GET https://api.yuantafunds.com/ectranslation/api/trans
  APIType=EC2API
  CompanyName=YUANTAFUNDS
  AppName=FundWeb
  Device=4
  Platform=YUANTAFUND
  PageName=/myfund/dividend/history
  DeviceId=<any>
  FuncId=FundDividend/History
  FundId=1066
```

缺 `AppName/Device/Platform` → `必要參數不可為空白`；錯 FuncId → `不允許的API存取`。

3. **Prototype**：`scripts/e22_fetch_yuanta_etf_dividend.py`

```bash
python3 scripts/e22_fetch_yuanta_etf_dividend.py --stk 0050 --compare-ledger
```

輸出：`research/ops/yuanta_etf_div_0050.json`

## 欄位對照

| API | Ledger | 備註 |
|---|---|---|
| `SHARE_DATE` | `cash_ex_date` | 除息日 |
| `PAY_DATE` | `cash_payment_date` | 發放日 |
| `DIVIDEN_PER_UNIT` | `cash_dividend` | |
| `BASE_DATE_GEN` / `P_ESTIMATEDATE` | — | 多為除息前一交易日，**不是**公告日 |
| `ESTIMATEDATE` | — | 收益計算基準日（多為季/半年底） |
| （無） | `announcement_date` | API schema 無公告日 |

## 為何先前抓不到

| 路徑 | 結果 |
|---|---|
| 直接 scrape `yuantaetfs.com` SPA HTML | 無 SSR 配息表；chunk 動態載入 |
| `www.yuantaetfs.com/api/trans` | SPA catch-all → HTML |
| `etfapi.yuantaetfs.com` + 錯參數 | JSON 但 `必要參數格式不正確` |
| `fundid=0050` 當 FundId | 錯對象（應為 `1066`） |

穩定路徑是 **`api.yuantafunds.com` + `FundDividend/History`**，不是爬 ETF 行銷站 DOM。

## Resilience 定位

- **適合**：手動／研究用官方 ex/pay 核對、補早期 pay、擴 ETF universe。  
- **不適合**：當 runtime failover 自動備援（需固定 common params；非 FinMind/Yahoo 契約）；**不能**解 `0050` announce 空白。  
- 不改 `DATA_SOURCE_RESILIENCE.md` 自動備援表；本筆記僅記錄研究結果。

## Residual

- Ledger **`0050` `announcement_date` × 27** 仍空。  
- Next（人工／其他來源）：元大新聞稿／公開資訊觀測站 ETF 相關公告，**不可**用 `BASE_DATE_GEN` 冒充公告日。

## Non-actions

- 不寫入 `e22_dividend_events.csv`（無 announce 可填；ex/pay 已齊）  
- No Soft-Frozen flip / no Goodinfo·Wantgoo 備援重開  

## Artifacts

- Script: `scripts/e22_fetch_yuanta_etf_dividend.py`  
- Sample: `research/ops/yuanta_etf_div_0050.json`  
- Related: `E22_STOCK_WEB_SOURCE_SWEEP_2026-09-10.md`
