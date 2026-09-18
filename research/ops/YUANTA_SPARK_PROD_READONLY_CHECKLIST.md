# 元大 SPARK PROD — 只讀驗證清單

Status: **OPS / HOWTO** — 正式環境 API 已開通後的**安全上限**  
**逐步教學（安裝＋腳本）：** `YUANTA_SPARK_PROD_READONLY_HOWTO.md`  
Audience: 營業員確認 PROD 開通；尚無 UAT、或 UAT 未就緒  
Related: `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md` · `broker_safety.py` · `broker_risk.py` · Soft-Frozen KEEP

---

## 0. 硬規則（先讀）

| 做 | 不做 |
|---|---|
| `Open(PROD)` → `Login` → **只讀查詢** | **不下單**（`SendStockOrder`／改量／改價／刪單） |
| 憑證只放本機或獨立 PROD 機器 | 不把 `.pfx`／密碼 commit 進 git／Docker／Public repo |
| 核對帳號、庫存、交割款數字合理 | 不寫 Soft-Frozen `forward/e21` |
| 測完可登出／關機 | 不設 `E21_BROKER_WRITE_LIVE=1` |
| | 不開 `live_config.broker_live_write_accepted`（仍要另開 ACCEPT） |
| | **不要**用 `yuanta-uat-vm`（UAT 白名單 IP）連 PROD 當常態 |

**一句話：** PROD 開通 = 可以驗證「帳號能登、能查」；≠ 可以自動交易。

---

## 1. 跟營業員再確認（書面為佳）

1. 開通的是 **PROD**（不是 UAT）— 已確認則打勾  
2. 帳號格式：`S` + 分公司(4) + 帳號(7)  
3. `.pfx` 路徑／密碼、登入密碼、SDK／DLL 下載位置  
4. PROD **是否需要**來源 IP 白名單（多數不必；若要，另記 IP，勿與 UAT IP 混用）  
5. 有無 **UAT** 可並行（有則開發優先改回 UAT）

---

## 2. 環境準備（與 UAT 分開）

- 本機或**另一台**機器（建議標名 `yuanta-prod-readonly`，勿與 `yuanta-uat-vm` 混用設定）  
- .NET 8 + `pythonnet` + 元大 SPARK 元件（見 UAT howto §5 安裝步驟，元件選 **正式**）  
- 環境變數／設定檔只含 PROD endpoint；**禁止**同一 config 裡 UAT／PROD 憑證混放  

最小連線順序：

```text
Open(PROD) → Login(pfx, pfx密碼, 帳號, 登入密碼)
  → 等 OnResponse Login 成功
  → 只讀：庫存／銀行餘額／交割款／損益（依 SDK 查詢 API）
  → Logout / 結束
```

---

## 3. 驗證步驟（由淺到深）

| # | 步驟 | 通過標準 | 失敗時 |
|---|---|---|---|
| 1 | 元件載入 | DLL／`.so` 無缺檔 | 重裝 SDK；對齊 OS／架構 |
| 2 | `Open(PROD)` | 連線成功、無 timeout | 問營業員 PROD endpoint／防火牆 |
| 3 | `Login` | `OnResponse` MsgCode 成功 | 核對 pfx／密碼／帳號格式 |
| 4 | 庫存查詢 | 張數／標的與 App／對帳單大致一致 | 截 MsgCode＋時間給營業員 |
| 5 | 交割款／餘額 | 數字合理（允許延遲） | 同上 |
| 6 | **停止** | 已 Logout；過程**零**下單／改單 | — |

可接受的紀錄（打碼後可贴 agent）：Login 成功時間、MsgCode、查詢種類、是否一致。  
**禁止**貼：完整帳號、密碼、pfx、未打碼委託明細。

---

## 4. 通過之後仍不做的事

- 不送測試單（即使 1 張／可刪）— 等 UAT 或另開 **ACCEPT** 書面範圍  
- 不接 `BrokerPreflightFillPort` live write  
- 不合併「能 Login」與「策略日批自動下單」為同一里程碑  

建議下一里程碑（擇一）：

1. 營業員補 **UAT** → 回 `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md` 完整測  
2. 無 UAT → 另開 ACCEPT：「PROD 只讀 adapter 接線」charter（仍無自動下單）

---

## 5. 與 repo 防呆的關係

已落地（離線）：`broker_safety`／`broker_risk`（鎖、dedupe、狀態機、panic、限流、熔斷 half-open、對帳）。  
PROD Login 成功**不**自動解除這些閘門；`LIVE.broker_live_write_accepted` 預設 `False`。

---

Label: `YUANTA_SPARK_PROD__READONLY_CHECKLIST`
