# Live fill 高低點／機制審計（紙上）

日期：2026-09-26  
狀態：**tip `FILL_EXTREME_AUDIT_DONE` + 回測 `FILL_EXTREME_BACKTEST_DONE`** · Soft-Frozen **KEEP** · 不上 live  
人令：事後審計 + 機制對照；同題從回測檢視  
OHLC：**`adj_close` 還原**（0050 Stage A `METRIC_ARTIFACT_ONLY` 後改為權威口徑）

**Tip**：tip fill 相對 ±5／±21 日高低距離（%）+ 機制標籤。  
**回測**：FUSE+SELL_a75+COOL_c8 live twin 全歷史 fills。

```bash
PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py
PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py
```
