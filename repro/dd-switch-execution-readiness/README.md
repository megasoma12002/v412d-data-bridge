# DD_SWITCH 盤中實作與資料就緒稽核

日期：2026-10-08（台灣時間研究跨至 10-09）。狀態：**BLOCKED_INTRADAY_EVIDENCE**。

已實作可重跑的研究程式，尚未得到真正 T+0 成交績效。原策略、原日線歸因以及正式帳本均保留。

## 現有證據

|帳本|成交筆數|訊號日期後成交|同日成交|缺少 NAV 交易日|
|---|---:|---:|---:|---|
|原 forward/e21|107|107|0|09-17、09-18、10-05|
|R1 生產流程重播|144|144|0|09-17、09-18（位於 09-29 重播種子之前）|

兩者皆缺少 `signal_at`、`fill_at`、`quote_at`。日期符合隔日資格不等於成交時間已驗證；`execution_clock` 是訂單規則標籤。R1 補齊種子後的 10-05，並沒有補齊種子前歷史。掃描 data / forward / repro 未找到具備時間戳、可知時間、買賣報價和深度的 CSV。掃描不是宣稱其他外部服務沒有資料。

因此先前 24–29% 延後一期保留的增益仍屬固定母帳的報酬序列敏感度，不能當成真實 T+0 / T+1 獲利比例。R1 使用重建控制帳，也不是原完整 DD_SWITCH 的長期成交證明。

## 新實作

`scripts/dd_switch_intraday_replay.py` 固定比較 10:00、12:00、13:20 三個觀察時點的 L4、TRAIL42 與 DD_SWITCH；另外以 14:00 可取得的當日收盤母帳訊號，在下一交易日報價到達後重播 DD_SWITCH。

- DD 規則維持 `TRAIL DD >= L4 DD` 選 TRAIL；以各母帳前一日以前的收盤峰值，加上當時可知的 NAV 計算。這是原 DD 規則的盤中版本，盤中母帳 NAV 必須由真實價格與完整持倉建立，不從最終日報酬推算。
- 每個比較組各用一個相同起始現金的股票／現金帳。目標必須是完整母帳配置，含私有袖套；不將兩個母帳當日報酬直接拼接。
- 訊號及配置必須在觀察時點可知。模擬成交必須使用訊號及延遲之後的新報價；訊號前報價即使延遲送達，也不能成交。
- 一次訊號固定一次股數目標；先賣後買，整張取整，使用 `live_ledger` 的成本與滑價。價格變動不會自動產生持續再平衡。
- 新目標取消舊目標，日終取消剩餘目標。現金再進場使用該帳現金與 NAV，不隱含注資。這只是新研究帳的明確政策，沒有修改正式帳的資金補回規則。
- 預設延遲 1 秒、每筆最多取顯示深度 10%。這些是模型假設，並非經驗成交品質。缺少當日持倉價格會中止，拒绝默默沿用昨日價格。
- 支援明列拆股事件。含現金／股票股利事件的區間目前中止，待加入按除權息日持倉建立的權益及支付帳；不得把相關月份當作已完成完整總報酬驗證。

## 資料介面

輸入為同一資料夾中的 `manifest.json` 與六份 CSV。所有時間須帶時區，例如 `2026-10-01T10:00:01+08:00`；報價數量單位為股，價格為未還原原始報價。

|檔案|欄位|
|---|---|
|sessions.csv|date（排序、唯一；包含母帳收盤峰值所需的暖機歷史）|
|daily_nav.csv|date,available_at,l4_nav,trail_nav|
|snapshots.csv|snapshot_id,observed_at,available_at,l4_nav,trail_nav|
|targets.csv|snapshot_id,parent,code,weight,available_at（parent 為 L4 / TRAIL42）|
|quotes.csv|timestamp,available_at,code,bid,ask,bid_size,ask_size|
|events.csv|effective_at,kind,code,factor（拆股 kind=split；無事件也需有表頭）|

`manifest.json` 必須有 `evidence_kind: "timestamped_market_observations"`、`parent_scope: "full_account"` 及 `sha256`，後者以六份 CSV 檔名為鍵、檔案 SHA256 為值。應記錄資料提供者、取得方式、修訂版本、公司行動核對範圍；旗標與雜湊是可重現性檢查，本身不驗證提供者資料真實性。

每個有盤中觀察的有效交易日須有三個時點的新鮮母帳觀察和可用配置，以及 13:30 收盤觀察（14:00 前取得），否則中止。暖機日可以只有 daily_nav。現金配置可用一筆 weight=0 明示；未配置權重留在現金。收盤母帳歷史須涵蓋原策略峰值起點，不得縮短歷史來改善 DD。

實際 quote 模型仍不保證掛單排隊、可成交深度維持、同批跨標的成交或成交回報；重複深度觀察也不證明新增流動性。要宣稱真實成交，另須券商成交回報重建。最大回撤目前是報價資料每日最後可用標記的觀察值，並非連續盤中最大回撤。

```bash
python scripts/dd_switch_execution_readiness.py
PYTHONPATH=scripts python -m unittest discover -s tests -p test_dd_switch_intraday_replay.py -v
python scripts/dd_switch_intraday_replay.py --bundle /path/to/verified_bundle --out /path/to/new_run --initial-cash 500000000
```

输出每組逐筆決策、成交、每日 NAV、目標更換與拆股紀錄，以及報酬、觀察最大回撤及實際模型費稅。首次跑出結果應核對固定時點的優勢是否跨時期存在，再評估是否要更改正式策略。此階段不做参數搜尋，也不寫入實盤。
