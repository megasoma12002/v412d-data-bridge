# Fill 機制全面分析 A–D（紙上）

日期：2026-09-26  
狀態：**`FILL_MECH_DEEPDIVE_DONE`** · Soft-Frozen **KEEP** · 不上 live  
人令：全面分析後再討論後續  

在 tip／回測 fill 審計之上，切四塊：T+1 成本、KD 季、CLIP_FIN_HI、COOL 防守（含 NAV 對帳）。

```bash
PYTHONPATH=scripts python3 scripts/live_fill_mech_deepdive.py
```
