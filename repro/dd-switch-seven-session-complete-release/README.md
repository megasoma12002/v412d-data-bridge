# 7日父帳／母帳完整重建與停牌成交資格

本次是資料校正研究：原母帳與canonical forward全部保留，沒有合併、部署、券商委託或正式runtime發布。corrected generation沒有original prefix certification，不能直接冒充原研究母帳。

## 已完成

恢復2025-02-06、2025-06-11/12/13/16/17、2026-05-28七天的真實FIN/TEL/TAIEX市場列，並重新模擬COMP/SAT父帳、OFFENSE、BASE、L4及原規則TRAIL/DD母帳。父帳份額與選擇訊號從模型重算，沒有用前值NAV或偽造股數插列。原上層缺少的2026/8/3–8/7也已一起補齊。

2025官方243日＋2026截至10/8官方185日，共428交易日，市場、父帳、母帳、選擇訊號都無缺日。七日以外的既有原始價格不覆寫。金融缺日調整因子由兩側完全一致的凍結因子核對推導，兩側不同即阻擋；電信及0050使用既存調整價。早於首個缺日2025/2/6，COMP/SAT股數差0、BASE/L4 NAV差0、TRAIL相對誤差1.56e-15。

## 0050估值與成交

官方0050停止交易2025/6/11–6/17，6/18恢復並以1拆4換發。停牌五天保留核心股票交易日；0050估值採最後交易日收盤188.65元，標記LAST_EXCHANGE_CLOSE，成交open留空、tradable=False。這是陳舊市場估值，不是逐日基金NAV或停牌期間真實可成交價。

恢復前持股及暫停委託股數乘4、現金不变，按真實當日open成交。停牌期間新的close意圖取代同標的舊暫停意圖，防止每日累積重复買單；signal_date仍保留，不能同日成交。0050指標及上層shadow returns採分割中性計算，價格四分之一不會被誤當75%虧損。

父帳含既存00631L路徑，也套用已核對的2026/3/25–3/30停牌與3/31股數乘22；這不是新增配置。另恢復00631L 9/29實際quote，避免用舊價成交。停牌和上市前價均不可成交，未知上市後缺價會報錯。

官方來源：
- [0050單位數與恢復交易公告](https://www.twse.com.tw/zh/ETFortune/announcement?company=A00005&date=20250617&fund=0050&seq=1&type=other)
- [00631L分割公告](https://www.twse.com.tw/zh/ETFortune/announcement?company=A00005&date=20260330&fund=00631L&seq=1&type=all)

## 稽核

123個相關測試通過，含停牌無成交、空open阻擋、暫停意圖更新、恢復股數／委託換算、股數與價格分割後資產連續、分割中性shadow returns、因子不一致阻擋。

五個實際share/cash/E22帳由逐筆fills獨立重建，最大NAV殘差3.34e-6元，沒有負現金，停牌成交0筆、同日成交0筆。官方日曆驗證限2025/2026，早期股利有效日期仍保留原fallback假設。完成日曆不等於全歷史券商可執行／完整PIT認證。DD/TRAIL原本shadow與return-stitch假設保留；本次不改策略門檻。

## 更新後的固定方案

六方案與首輪固定門檻完全相同。以下是FIN/TEL核心研究錢包，排除0050／民營金現行overlay，不是完整live績效。2026已被前輪研究看過，不稱盲測。

|2026截至10/8|報酬|MDD|
|---|---:|---:|
|保持ON核心基準|24.9889%|-8.2250%|
|原DD＋可回補帳|23.3195%|-9.4324%|
|大盤半倉確認|20.1048%|-9.3880%|
|大盤全退確認|15.6566%|-10.5198%|

連續2025–2026基準44.8323%、原DD36.7698%、半倉確認42.4060%。日期補齊後全部逐筆成交落在下一官方交易日，缺資料延遲0筆；資金最大殘差5.26e-6元。没有跨年份穩定提升報酬且改善回撤的證據，不自動替換現行策略。

## 同一live種子下的隔離T+1重播

9/29既有實際帳種子，更新控制／父帳後重播至10/8，完整8/24–10/8共32交易日再建帳：NAV543,462,667.23元、報酬8.6925%、MDD -5.1394%。相較先前核對T+1重播NAV增加541,684.07元，與原forward仍差510,019.54元。這是來源及父帳狀態校正後的反事實研究，不是實際帳戶新增獲利，也不是靠調參追平；剩餘差額不得都叫滑價。

已存在控制日期中3日active gate改变，新增12個控制日期。校正資料會改變後續累積持倉、選擇及母帳，因此不沿用旧長期績效。正式live尚未切換此corrected generation。

## 重現

```bash
python scripts/dd_switch_seven_session_rebuild.py --out repro/dd-switch-seven-session-rebuild --stage all
python scripts/dd_switch_session_validation.py --build repro/dd-switch-seven-session-rebuild
python scripts/dd_switch_crisis_profit_research.py --out repro/my-complete-fixed-policies --runtime repro/dd-switch-seven-session-rebuild/runtime --core-prices repro/dd-switch-history-gap-recovery/verified/recovered_core_prices.csv
python scripts/dd_switch_live_replay.py --inputs-dir repro/dd-switch-seven-session-rebuild/runtime --out repro/my-complete-forward-replay
```

沒有allow-observation-gaps。固定原始provider JSON在此前history-gap-recovery/sources，新增inverse回應在原build sources。大型輸入market／中間持倉檔由腳本確定性生成；hash記錄於source_manifest.json，父／母帳NAV、fills、runtime、独立殘差、完整連續比較成交／持倉／資金journal保存於本目錄。
