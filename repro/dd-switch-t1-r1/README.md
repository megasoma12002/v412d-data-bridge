# DD_SWITCH 資料修復與逐筆成交重建（2026-10-08）

目前已完成修復候選與紙上帳本重建。以下全部是模型或 forward paper 帳本，沒有券商實際成交損益。正式 forward/e21 歷史未改写；修復留在獨立分支，未合併部署。

## 最關鍵的結果

| 帳本／方法 | 期末淨值（元） | 累計收益（元） | 累計報酬 | 觀測最大回撤 |
|---|---:|---:|---:|---:|
| 原 forward paper：2026-08-24～10-08 | 543,972,686.77 | 43,972,686.77 | +8.7945% | −3.6611% |
| 修復候選版：保留 9/29 以前帳本，9/30～10/8 以正式流程接續重跑 | 534,722,253.07 | 34,722,253.07 | +6.9445% | −4.2034% |

兩者均以原始資本 500,000,000 元計算。修復候選版比原帳本低 9,250,433.70 元。這是反事實重建差額，不是已實現損失，也不能全部歸因於 T+0／T+1。候選版同時修復控制資料過期、00631L 報價更新，以及改用明示的 R1 逐筆控制帳本來源；它不是只替換一張價格表的單因素比較。

原帳本 9/30 後 Path3 因 ledger_stale 沒有產生訂單，10/2 後 DD_SWITCH 控制資料顯示 nav_stale，普通 FIN/TEL 訂單仍被抑制。原 +8.79% 因此無法證明完整、正常運作的 DD_SWITCH 有該績效。修復版自 10/1 收盤決定 FIN/TEL→cash，10/2 開盤執行；截至 10/8 公股金融與電信持倉為零，仍有民營金融及 0050 持倉。

注意原帳本 9/17、9/18、10/5 缺少 NAV；接續重建补入 10/5，但 9/29 以前沒有重造，因此兩組最大回撤都是所列觀測序列的回撤，不能聲稱已恢復整段完整每日回撤。

## 逐筆成交與帳務驗證

9/30～10/8 正式流程新增 48 筆成交，費稅合計 2,569,039.32 元；保留先前帳本後，共 144 筆成交。每日獨立由逐筆股數、gross、fees_tax 回推現金及收盤 NAV：最大殘差 0.0000000596 元。現金非負、股數非負、每筆整股 1,000 單位、訂單／成交 ID 唯一、成交關聯訂單、NAV／state 一致、audit chain 等 20 項 QC 全通過。所有重建成交的 signal_date 均早於 fill_date；同日成交 0 筆。

費率沿用正式紙上模型：買賣佣金 0.0855%（最低 20 元）、股票賣出稅 0.3%、ETF 賣出稅 0.1%、買賣各 5 bp 滑價。整筆買單資金不足會保留待成交；賣單股份不足不成交。這是開盤價加成本模型，沒有撮合排隊、容量、漲跌停可成交量或券商回報驗證；長期掛單也沒有新增取消期限。

## 已修復的資料與成交時鐘

- 新增每日 DD_SWITCH 重建／更新步驟，先於正式 forward 流程執行。COMP、SAT、Path3 signal、L4、TRAIL、BASE 與 00631L 報價發布成同一版本，保存 SHA256 與 as-of。
- 執行前檢查資料日期與校驗碼；資料失效或損壞時整個流程停止，避免留下「成功、但策略部分未執行」的帳本。
- 00631L 使用官方月資料更新至 10/8；正式價格合併只接受指定日期資料，取消沿用舊開盤價的 fallback。
- DD_SWITCH 新訂單標示 AFTER_CLOSE / NEXT_SESSION_OPEN；Path3 的 -P3T0 ID 與 carve-out 標籤僅保留相容性，不能讓這些訂單在訊號當天成交。
- 修正 QC：即使允許特殊 T+0，也不能豁免訊號日期之前的成交。舊研究基線及原始 forward 帳本均保留。

### 停牌與分割

00631L 的 2026-03-25、26、27、30 沒有價格不是缺漏：官方公告為分割停牌，3/31 每單位變 22 單位。重建在停牌日沒有開盤成交，收盤估值暫用最後可得交易價，3/31 在開盤前增加持有與未成交訂單單位數，不產生現金股利。0050 的 2025-06-18 也在重建處理 1→4 單位分割。舊 simulate_core 呼叫不傳入 share_events / closed_sessions 時維持原有結果。

00631L 官方公告：
https://www.twse.com.tw/zh/ETFortune/announcement?company=A00005&date=20260330&fund=00631L&seq=1&type=all

0050 官方分割公告：
https://www.twse.com.tw/zh/ETFortune/announcement?company=A00005&date=20250617&fund=0050&seq=1&type=other

官方行情：
https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=20261001&stockNo=00631L&response=json

## 長期模型揭露：現金回補缺口

長期 R1 使用公股金融、電信、0050、00631L 的逐筆持股及股利帳務，固定從第一個 2013 年交易日 BASE 母帳本初始化，下一日開始觀測。以下為機械診斷模型，不是完整現行策略的歷史績效認證：沒有逐年重演 FinPriv 與 TEL_T3 全部正式流程，COOL 控制仍沿用現行原始 offense 的 cash-on-ex 模型；調整價格是目前快照，沒有歷史版本 PIT 証明。

| R1 帳本 | 2013-01-03 起期初 | 2026-10-08 期末 | 年化（252 筆） | 最大回撤 | 公股 FIN/TEL 為零日數 |
|---|---:|---:|---:|---:|---:|
| L4，Path3 持續 ON | 507,852,267.74 | 1,563,834,365.45 | 8.8259% | −21.5518% | 0 |
| TRAIL42 | 507,852,267.74 | 662,994,010.74 | 2.0249% | −1.9811% | 3,332 / 3,352 |
| DD_SWITCH | 507,852,267.74 | 662,994,010.74 | 2.0249% | −1.9811% | 3,332 / 3,352 |

現行 plan_delta_ledger_scaled 依「既有 FIN/TEL 持倉金額」配置母帳本比例。轉現金使該金額變成零後，即使 Path3 恢復 ON，算出的回補買單依然為零；普通 FIN/TEL 又被抑制。因此本模型自 2013-01-31 起長期缺少公股 FIN/TEL 曝險，低回撤不能當成 DD_SWITCH 選擇能力的證明。修復沒有擅自發明新的現金回補預算；需要另外定義 NAV／sleeve 預算與未成交訂單處理，再評估該修正版本。

## Path3 T+0 優勢判定

目前結論仍是 INCONCLUSIVE / RETAIN_BASELINE。原始 blend_oracle 用當日完整報酬挑選同一天的 COMP／SAT 報酬，屬非因果；原 T1_OPEN 名稱也只是 lagged return blend，沒有逐筆開盤重建。正式流程在盤後取得完整收盤資料，不能用它回填同日收盤成交。這次採用收盤訊號→下一交易日開盤，沒有產生可驗證的 T+0 優勢證據。真實 T+0 必須有決策截止前的資料與時間戳、可下單價格及券商／撮合證據，不能從 daily OHLC 推導。

## 重現與檔案

來源基準：megasoma12002/v412d-data-bridge @ 7aeb896de232dad475c179d90ee7136090807489。
分支：fix/dd-switch-refresh-t1-rebuild。

```bash
pip install -e .
python scripts/dd_switch_rebuild.py --asof 2026-10-08 --refresh-prices --publish
python scripts/dd_switch_live_replay.py
python -m unittest discover -s tests -p 'test_dd_switch_runtime_r1.py'
```

重跑 live replay 時需指定新的 --out 空目錄，避免混入上次資料。全部輸出在 repro/dd-switch-t1-r1 與 repro/dd-switch-live-t1-r1；後者直接呼叫正式 production pipeline，逐日截斷 runtime 資料，未使用未来觀測。

主要結果：summary.json、fills.csv、nav.csv、orders.csv、portfolio_state.json、qc_status.json、independent_reconciliation.csv。長期資料額外提供三本 NAV、股數、成交、股利明細、每日控制狀態與官方回應快照。

相關 69 項單元測試通過；短期完整 QC 通過。長期控制帳本重新計算的 want_trail 與 trail42_on 和已發布來源逐日一致（0 個差異）。未重新做參數最佳化、未宣稱未知樣本驗證、未合併部署。
