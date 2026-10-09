# 歷史缺列恢復：價格已取得，完整母帳尚未完成

7天真實 FIN/TEL＋TAIEX 原始開盤／收盤價格共56列已恢復；金融與大盤來自保存的 FinMind TaiwanStockPrice JSON，電信來自既存原始OHLCV檔。未補前值價格，未寫入forward或正式runtime。

日期：2025-02-06、2025-06-11/12/13/16/17、2026-05-28。原始release ZIP也缺2/6及5/28；0050停牌5天的缺quote不能解讀為全市場沒有交易。僅核心研究使用 recovered_core_prices.csv，沒有捏造0050可成交價或調整價。

TRAIL缺2026-08-03至08-07源於上層生成commit的market snapshot缺這5日，父帳與訊號其實有資料。用同日真實market列及鎖定上層建構規則重跑SC_WITHIN/SC_CASH與TRAIL，不做NAV前值填補。缺口以前TRAIL相對誤差1.33e-15，已存在日期的active gate改變0日；新增5日會改變隨後NAV水準，且增加可重播交易日。

corrected research runtime明確改名、取消prefix_certified，禁止發布；原母帳／認證generation原樣保留。完整全期間仍缺7天BASE/L4與父帳份額／選擇訊號。嚴格模式會拒絕，而非把下一觀察日成交當成T+1。恢復母帳需重新模擬：0050停牌時須分離估值與可成交價，再重建所有受影響的累積控制與持倉；不能插入母帳NAV前值或偽造父帳股數。

```bash
python scripts/dd_switch_history_gap_recovery.py --sources repro/dd-switch-history-gap-recovery/sources --out repro/my-gap-recovery
python scripts/dd_switch_crisis_profit_research.py --runtime repro/my-gap-recovery/runtime --core-prices repro/my-gap-recovery/recovered_core_prices.csv --out repro/my-fixed-diagnostic --allow-observation-gaps
```

sources/*.json保存原始API回應，query為dataset=TaiwanStockPrice、data_id=<檔名>、start_date=2025-02-06、end_date=2026-05-28。summary內有所有來源hash；其他未發布的大型生成檔可由上述腳本重建。嚴格模式不加allow-observation-gaps仍會阻擋七天缺少的控制來源。
