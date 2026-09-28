# ETF 0050 軟縮放 × 高低點／DD Stage A — 紙上章程

日期：2026-09-28  
狀態：**Stage A DONE — `TIP_BLOCK`** · Soft-Frozen **KEEP** · β clip **KEEP** · `SELL_a75` **KEEP** · 不下 live  
父層：`1d` 硬閘 **`TIP_BLOCK`**（WR／偶發 CAGR↑，tip MDD 掛）  
種子：`SELL_COOL_DEFEND` · `BUY_RET5_POS`

人話：

```
OPEN Stage A: 0050 Δw 軟縮放（seed SELL_COOL_DEFEND / BUY_RET5_POS）或 0050 自身高低點／DD 閘 · tip-safe + CAGR↑ · paper only
```

Label: `ETF0050_SOFT_EXTREME_STAGEA_CHARTER_2026-09-28__DONE_TIP_BLOCK__NO_LIVE_WIRE`

## 雙軌

1. **SOFT** — 品質不合格時只吃 intended Δw 的 25%／50%（不是全凍）  
2. **EXT** — 靠近自身 N 日低／深 DD 才加碼；靠近 N 日高才減碼  

不重開 densify／slew／`1d` 同款硬閘。

## 重現

```bash
PYTHONPATH=scripts python3 scripts/etf0050_soft_extreme_stagea.py
```

詳見英文章程。
