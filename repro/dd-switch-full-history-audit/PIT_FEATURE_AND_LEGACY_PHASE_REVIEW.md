## 2026-10-10 公告閘門與舊權利證書核對

本輪並未解除一般股票／現增普通股交付缺口。6筆股票、9筆現增、4筆股份階段及9項全歷史阻塞仍保留，類別重疊。股份階段由2增為4：重新讀取已保存、原始／壓縮SHA256核對的一手兆豐金公告，明確辨識2011權利證書9/16發行、9/21普通股上市與權利證書終止；2012為9/6及9/13。兩筆配股數量與ledger精確匹配，但上市日不自動等於一般交付入帳日。權利證書價格、單位、交易資格及換發交付仍待補，canonical未修改。

研究用公告版本閘門已實作：只使用cutoff以前reported_at的版本，未知clock排除、無時區clock拒絕；同event同clock不同日期拒絕；修訂與撤回只在公開後生效。市場輸入限截止日以前；未來只有日曆標籤、沒有未來行情。既有KD函式需要在index內找到已知未來除息日，故提供NaN行情的日曆佔位列，避免截短市場時把已知日程一併丟掉。只輸出指定截止日的當年特徵，不把當下快照回填為過去每日決策。

10項閘門測試及4項權利證書測試通過；包含既有核對流程的115項相關測試全部通過。2025/2026各5/15、6/5、7/1（休日取前一觀測日）共6截止日、24個標的截點：實體行情prefix與完整输入结果一致，未來價格乘100及加入20份未來修訂均不改變此前結果。與舊完整ledger計算比較，KD差異12/24、買進遮罩差異0/24；比較同時改變事件可得限制與日曆前綴處理，不能歸因為NAV損失或宣稱提升報酬。

本輪範圍：feature-only，沒有產生訂單、成交、NAV或收益。僅研究候選，未接入production；公告版本全集、歷史publication vintage與日曆vintage仍未認證，`backtest_ready=false`。未執行DD_SWITCH T+1，沒有合併、部署、runtime發布或背景抓取。

重現（先恢復既有證據與研究输入）：

- `PYTHONPATH=scripts python scripts/dd_switch_legacy_rights_phase.py`
- `PYTHONPATH=scripts python scripts/dd_switch_pit_feature_review.py`
- `PYTHONPATH=scripts python -m unittest tests/test_dd_switch_pit_features.py tests/test_dd_switch_legacy_rights_phase.py`
- `python scripts/dd_switch_remaining_gap_inventory.py`
