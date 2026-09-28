# FIN 賣側品質 Stage A — 章程（繁中摘要）

日期：2026-09-28  
狀態：**Stage A OPEN** · Soft-Frozen / Exact T+1 / COOL / **SELL_a75 KEEP** · 無 live wire

```
OPEN Stage A: FIN 賣側品質過濾 · 保留已測賣側優化(SELL_a75) · MDD持平/改善 + CAGR↑ · 勝率兼顧更好 · paper only
```

## 目標

1. held CAGR↑ ≥ +0.15pp（**chal − base**）  
2. held MDD 近持平／改善  
3. tip MDD 不惡化  
4. FIN SELL 勝率（賣後 H=21 下跌）能兼更好  

## 保留／禁止

- **KEEP**：live `SELL_a75` soft-sell  
- **禁止重開**：賣側等回本 / loss-defer  

詳見 `FIN_SELL_QUALITY_STAGEA_CHARTER.md`。

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_quality_stagea.py
```
