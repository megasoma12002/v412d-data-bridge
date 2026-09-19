# 元大 SPARK 條件單對照 — 營業員建議「二擇一」

Status: **OPS / RESEARCH** — 對照 App 條件種類 ↔ SPARK API；**尚未送真單**  
Related: `YUANTA_SPARK_PROD_READONLY_HOWTO.md` · [新增條件單](https://www.yuanta.com.tw/file-repository/content/sparkapi_docs/%E6%A2%9D%E4%BB%B6%E5%96%AE/%E6%96%B0%E5%A2%9E%E6%A2%9D%E4%BB%B6%E5%96%AE/index.html) · Soft-Frozen KEEP

---

## 0. 結論（先讀）

營業員建議：**停利／停損或當沖優先用「二擇一」(OCO)**。  
SPARK API **有對應**：`OCOStrategy` + `SendAlgoCOOdrStrategy`（`StrategyType=3`）。

| 現況 | 說明 |
|---|---|
| 已驗證 | PROD Login＋庫存／餘額／交割**只讀** |
| **未做** | 任何 `SendStockOrder`／`SendAlgoCOOdrStrategy` 真送單 |
| 要「成交一筆」 | 需另開 **ACCEPT**（真錢／真庫存風險）；本文件只備研究與骨架參數 |

---

## 1. App「條件種類」↔ API

| App（截圖） | 意思 | SPARK 物件 | StrategyType |
|---|---|---|---|
| 長效單 | 區間內送出設定委託（GTC 語意） | （多為一般／條件時效設定，非獨立 StrategyType） | — |
| **停損利** | 價破條件線 → 送出委託；一日最多觸發一次 | `STOStrategy` | **1** |
| **移動鎖利** | 超基準價後洗價；自高點回檔觸發 | `MLPStrategy` | **2** |
| **二擇一** ★ | 兩條件擇一觸發；另一自動取消 | `OCOStrategy` | **3** |
| **母子單** | 母成交後才監控子；當沖版當日反向 | `MS_SpiderStrategy`／`MS_DayTradeSpiderStrategy` | **4**（＋當沖變體） |
| **多條件** | 1–8 條件；全部符合或擇一符合 | `SpiderStrategy` | **5** |

API 入口：

| 動作 | 函式 |
|---|---|
| 新增 | `SendAlgoCOOdrStrategy(Account, lstStrategy, lng)` — **單次清單只能同一策略類型** |
| 刪除 | `DeleteAlgoCOOdrStrategy` |
| 查有效 | `GetConditionStrategy(Account, StrategyType, StkCode)` |
| 查歷史 | `GetHisConditionStrategy` |

---

## 2. 為何營業員推「二擇一」

停利＋停損常見需求：上面一個賣（停利）、下面一個賣（停損），**只會成交一邊**。  
OCO 正是：條件1／條件2 商品必須相同；一邊觸發送單，另一邊自動取消。  
對照 App 文案：「設定兩個條件，其中一個符合觸發時…另一個條件即自動取消。」

適合：

- 已有庫存，掛 **停利價** + **停損價** 二選一賣出  
- 當沖情境（仍要注意當沖權限／母子當沖單是另一物件）

較不優先當「第一筆煙測」：

- **移動鎖利**：參數多（基準價、回檔％／元）  
- **母子單**：链路長，當沖版當日結束  
- **多條件**：組合複雜  

---

## 3. OCO 參數骨架（研究用，勿直接對 PROD 裸奔）

官方概念（賣出庫存例）：

```text
OCOStrategy
  Account, EffTime, ExpTime
  Order = 成交就停 / 觸發就停
  StrategySettings1  # 條件1：同商品、Direction 1=≥ 或 2=≤、Value=觸發價
  StrategySettings2  # 條件2：同商品、反向方向
  OrderSettings1     # 條件1 觸發後委託（現股賣、限價/市價、張數）
  OrderSettings2     # 條件2 觸發後委託
→ SendAlgoCOOdrStrategy(Account, [oco])
```

約束（文件）：

- 僅證券帳號；上市／上櫃  
- 有效日：盤中當日～90 天；盤後下一交易日～90 天  
- 條件價相對開盤參考價約 **0.7～1.7 倍**  
- `OrderQty` 單位與一般條件單設定一致（文件以張／設定股數欄位為準，送單前用官方 sample 再核一次）

Python 形狀（示意，帳密勿寫死）：見官方「新增條件單」頁 `OCOStrategy` 範例；本 repo **不**附可貼上即對 PROD 成交的腳本。

---

## 4. 建議驗證階梯（仍守 Soft-Frozen）

| 階 | 內容 | ACCEPT？ |
|---|---|---|
| A（已過） | PROD Login＋只讀查詢 | 不需要 |
| B | `GetConditionStrategy` 只讀列出既有條件單 | 可不需（仍只讀） |
| C | App 手動下一筆極小「二擇一」熟悉 UI | 人為操作 |
| D | API `SendAlgoCOOdrStrategy` 極小 OCO（例如既有庫存 **1 張**、寬鬆停利／停損） | **要 ACCEPT** |
| E | Soft-Frozen／策略日批自動掛條件單 | **另開 ACCEPT** |

**「幫設定成交一筆」= 階 D**，不是現在這份研究能直接執行的。

若你 **Accept 階 D**，請書面指定：

1. 標的代號（建議用已有庫存、流動性高者）  
2. 張數（建議 **1 張**）  
3. 停利價／停損價（或「距現價 ±X%」）  
4. 有效迄日  
5. 失敗時是否允許立刻 `DeleteAlgoCOOdrStrategy`  

未 Accept 前：agent **不會**呼叫送單 API。

---

## 5. 可跟營業員反應的問題（操作卡點）

- PROD 條件單／雲端策略權限是否已開（與一般下單權限可能分開）  
- API `OrderQty` 對條件單是 **張** 還是 **股**（請他對官方 sample 確認）  
- 二擇一「觸發就停」vs「成交就停」實務建議  
- 盤中／盤後掛單有效日規則  
- 是否建議先 App 手動 OCO 成功一筆，再改 API  

---

## 6. Repo 邊界

- `yuanta_spark_adapter.py`：目前離線映射一般 `StockOrder`；**尚未**映射 `OCOStrategy`  
- `broker_live_write_accepted` 維持 `False`  
- 條件單成功後的回報／與 Soft-Frozen fills 對帳 = 更後面的工作  

Label: `YUANTA_SPARK__CONDITIONAL_OCO_NOTES`
