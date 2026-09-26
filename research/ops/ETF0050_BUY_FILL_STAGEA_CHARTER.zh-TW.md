# 0050 BUY 成交 Stage A（修度量 + 分批）

日期：2026-09-26  
狀態：**Stage A OPEN** · Soft-Frozen **KEEP** · 不上 live  
人令：0050 BUY ±5d 看似最差 → 先修分割度量，再做加倉分批敏感度  

已知：2025-06-18 約 4:1 分割讓 raw ±5d 出現假 ~290%；穩健 mean ~3.2%，相對 FIN BUY 約 +0.8pp。

```bash
PYTHONPATH=scripts python3 scripts/etf0050_buy_fill_stagea.py
```
