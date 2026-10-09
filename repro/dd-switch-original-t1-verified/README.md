# 已核對原來源鏈：完整 T+1 生產流程重播

**追回 8,198,730.08 元，約原 R1 缺口的 88.63%。區間報酬回到 8.5842%，完整日期最大回撤 -5.1556%。**

範圍：2026-08-24 至 10-08，共32個官方交易日，初始5億元。保留9/29以前的原forward記錄與當日待成交訂單，從9/30起以已核對原母帳、當前固定production配置重新產生訂單與成交。這是7個交易日的新決策重播加上既有歷史，並非從2013起的整套現行策略回測。

## 同口徑結果

|帳本|最終 NAV（元）|獲利（元）|區間報酬|完整日期 MDD|總佣金／交易稅（元）|
|---|---:|---:|---:|---:|---:|
|原 forward|543,972,686.77|43,972,686.77|8.7945%|-5.0914%|953,578.58|
|R1|534,722,253.07|34,722,253.07|6.9445%|-5.3934%|3,322,089.68|
|原來源鏈 T+1|542,920,983.15|42,920,983.15|8.5842%|-5.1556%|1,517,877.20|
|先前 R1 強制 ON 消融|542,947,596.42|42,947,596.42|8.5895%|-5.1563%|1,508,267.35|

原來源鏈7日自然保持ON，不使用消融或強制開啟。相對R1增加1.6397個百分點、8,198,730.08元；相對原forward剩餘0.2103個百分點、1,051,703.62元。比先前消融少26,613.27元，來自更新後的實際再配置路徑與成本，沒有以績效選擇輸入。

## 逐筆成交、現金、持股與股利

- 7日pipeline與最終QC全部PASS。新增39筆成交全部在訊號之後的下一交易日開盤，0筆同日成交、0筆延後成交。31筆新Path3訂單均有NEXT_SESSION_OPEN資格。
- 每日runtime檔案截斷到當日，before-use驗證來源hash，daily preflight再檢查同日asof／hash。日線訊號於收盤後使用，DD的T0標籤無法越過T+1成交資格。
- 使用production原開盤滑價、佣金、證交稅、整張、現金約束及訂單生命週期；39筆含金融／電信／0050等實際配置，不只縮放NAV。
- 依當日股利版本與除息前持股重建應收／支付、股數與唯一鍵。本视窗沒有合格股利權利，實際股利認列0。
- 補齊種子以前漏掉的09-17、09-18估值，完整32日NAV最大對帳差1.192e-7元，現金最大差3.726e-8元、最終持股差0。

runner的部分日期NAV曾算出約-3.9626%的回撤；那不是完整32日回撤。此報告统一使用補齊日曆的-5.1556%，不可混用。

## 追回部分與剩餘缺口

會計拆解可精確對上，並非各因素彼此獨立的因果效果。

|原來源鏈 T+1 減 R1|金額（元）|
|---|---:|
|前日持倉價格變化|+3,647,150.00|
|交易當日開收盤價格變化|+2,507,900.00|
|成交價差改善|+239,467.60|
|費稅減少|+1,804,212.48|
|合計追回|+8,198,730.08|

|原來源鏈 T+1 較原forward少賺的部分|金額（元）|
|---|---:|
|持倉＋交易當日淨價格曝險差|368,200.00|
|額外成交價差成本|119,205.00|
|額外佣金／交易稅|564,298.62|
|合計剩餘|1,051,703.62|

約65%的剩餘缺口是額外費稅與成交價差，35%是持倉／交易價格路徑。原forward因來源過期而較少再配置，其較低成本和持倉結果不能當作正確更新後一定能達到的收益。再進場預算沿用production既有規則，沒有偷偷補滿或重設金融／電信資金。

## 證據範圍與下一步

本次證明：在現有短視窗、production紙上T+1開盤成本模型下，忠實原來源鏈能保留大部分差距。仍未驗證券商實際成交、委託簿深度、開盤競價容量、參與率或真正T+0。母控制shadow保留原研究報酬拼接、同日DD選擇及歷史日曆／企業行動假設；不據此推定長期年化、危機期防守或完整原研究收益可實現。

下一步應把剩餘再配置成本做固定、事前規則的測試，再做整段歷史的共同资金T+1重建與分版本企業行動修正。新規則需含持倉回饋與退場後再進場測試，不能只以此7日挑最優參數。

所有執行使用隔離runtime與state-dir，沒有發布正式runtime、改寫原forward、合併、部署或券商操作。

## 檔案與重跑

`summary.json`含收益、完整MDD、時鐘、精確損益橋接、來源／程式hash；四套`*_complete_nav.csv`與`*_positions.csv`是完整估值／持股，`*_book_residuals.csv`是對帳。`LINEAGE_minus_*`按日按標的歸因；`signal_comparison.csv`是當日控制。原來源鏈實際生成的fills／orders／signals／state／QC另存`repro/dd-switch-original-live-t1/`。runtime來源manifest另存`repro/dd-switch-original-runtime-t1/current.json`。

先依 `repro/dd-switch-original-lineage-verified/README.md` 重建原研究來源鏈與父持股帳，再執行以下命令。輸出目錄須不存在；可自訂新名稱。

```bash
python scripts/dd_switch_original_runtime.py --lineage repro/dd-switch-original-lineage-certified-1008 --parents repro/dd-switch-original-parents-extended --audit repro/dd-switch-original-lineage-verified --out repro/original-runtime-new
python scripts/dd_switch_live_replay.py --inputs-dir repro/original-runtime-new --out repro/original-live-new --end 2026-10-08
python scripts/dd_switch_original_live_audit.py --lineage-live repro/original-live-new --out repro/original-live-audit-new
PYTHONPATH=scripts python -m unittest discover -s tests -p 'test_dd_switch_*.py'
```

43個相關unittest通過；另runtime來源hash、接入控制與原來源鏈、32日完整帳務及精確損益橋接均驗證通過。原forward在種子後有1筆舊pending較晚成交，統計另列；本次新來源鏈39筆均為下一交易日。
