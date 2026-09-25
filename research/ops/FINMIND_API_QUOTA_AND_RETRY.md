# FinMind API 額度上限與 E22 Dividend Bridge Retry

Status: **OPS / RESEARCH**  
Audience: E22 日批 `v412e22-dividend-events` · Soft-Frozen KEEP（不寫 `forward/e21`）  
Related: `scripts/v412e22_fetch_dividend_events.py` · [API 使用次數](https://finmind.github.io/api_usage_count/) · [llms-full](https://finmind.github.io/llms-full.txt)

---

## 1. 官方額度（每小時）

| 方案 | 每小時上限 | 備註 |
|---|---:|---|
| 未帶 token | **300** | 匿名／未登入 |
| Free + token | **600** | 登入後 `Authorization: Bearer {token}` |
| Backer | **1,600** | 贊助方案 |
| Sponsor | **6,000** | 含即時／分點等高階資料 |
| Sponsor Pro | **20,000** | 最高階 |

查用量（需 token）：

```http
GET https://api.web.finmindtrade.com/v2/user_info
Authorization: Bearer {token}
```

回傳重點：`user_count`（已用）、`api_request_limit`（上限）。

---

## 2. 超額時的行為

超出小時額度時 FinMind 回 **HTTP 402**：

```json
{"msg": "Requests reach the upper limit. https://finmindtrade.com/", "status": 402}
```

這不是憑證錯，也不是 Soft-Frozen tip 問題——是**共用小時配額**用完。  
E22 Dividend Bridge（2026-09-22）失敗即為此：`urllib.error.HTTPError: HTTP Error 402: Payment Required`。

---

## 3. 本專案用量特徵

| Job | 約略 req／次 | Token |
|---|---:|---|
| `V4.12-E22 Dividend Events Bridge` | **≈16**（`UNIVERSE` 一碼一請求） | 應設 `FINMIND_TOKEN`（workflow 已接 secret） |
| E50-A0／A1 等大回填 | 可達數百～上千／小時 | 同 secret，**與 E22 共用額度** |

單獨跑 E22（16 次）遠低於 Free 600；**402 幾乎都是同小時內 E50／其他 FinMind job 先把配額打滿**。

---

## 4. Retry 機制（已落地）

`scripts/v412e22_fetch_dividend_events.py`：

| 情況 | 行為 |
|---|---|
| 5xx／429／網路／timeout | 指數退避 `2**attempt`，預設最多 **5** 次 |
| **402 額度** | 間隔 sleep **30s → 60s → 90s** 再試；仍 402 → `FinMindQuotaError` fail-closed（GHA 15m 內不空等一小時） |
| 碼與碼之間 | pacing **0.35s**，降低突發 |
| Token | 讀 `FINMIND_TOKEN`；有則帶 Bearer（Free 上限 600／hr） |
| 可選 probe | 有 token 時打 `user_info` 寫進 `e22_dividend_fetch_status.json` |

**不做的事：** 不在 402 時 sleep 滿 1 小時（workflow timeout）；不 invent tip；不改 Soft-Frozen books。

人工處置 402：等小時窗重置，或錯開 E50 大回填與 E22 cron（E22 = `0 7 * * 1-5` UTC），必要時升 Backer／Sponsor。

---

## 5. 與 payment_date 保留的關係

FinMind 早期列常缺 `CashDividendPaymentDate`／`StockDividendPaymentDate`。  
Refresh 時腳本會用既有 `e22_dividend_events.csv` 的非空白 payment_date，依 `(code, cash_ex_date)`／`(code, stock_ex_date)` **exact key 保留**；FinMind 有值則以 FinMind 為準。  
避免再出現「refresh → Soft-Frozen 空白 → paper-hygiene 紅」循環（#276／#277）。

---

## 6. 驗證

```bash
python3 -m unittest tests.test_e22_dividend_fetch_preserve -v
# 有 token 時可手動：
# FINMIND_TOKEN=... python3 scripts/v412e22_fetch_dividend_events.py
```

---

Label: `FINMIND_API_QUOTA_AND_RETRY__E22`
