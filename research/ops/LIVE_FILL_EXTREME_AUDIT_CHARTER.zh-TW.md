# Live fill 高低點／機制審計（紙上）

日期：2026-09-26  
狀態：**tip `FILL_EXTREME_AUDIT_DONE` + 回測 `FILL_EXTREME_BACKTEST_DONE`** · Soft-Frozen **KEEP** · 不上 live  
人令：事後審計 + 機制對照；同題從回測檢視  

**Tip**：96 筆 tip fill：±5d 離高低點 mean ~3.8% · T+1 drag ~1.2% · 全數 T+1 · FIN 半數 CLIP_FIN_HI／KD 淡季；此窗無 DH／COOL 防守縮曝。

**回測**：FUSE+SELL_a75+COOL_c8 live twin 全歷史 `simulate_core` fills；COOL 為 on-book 防守標籤。

A：每筆 fill 相對 ±5／±21 日高低距離（%），分 FIN／TEL／0050／防守窗  
B：同日標記 T+1／clip／DH／COOL／KD 是否綁定  

```bash
PYTHONPATH=scripts python3 scripts/live_fill_extreme_audit.py
PYTHONPATH=scripts python3 scripts/live_fill_extreme_backtest_audit.py
```
