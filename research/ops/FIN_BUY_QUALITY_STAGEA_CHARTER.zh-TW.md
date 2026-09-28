# FIN 買側品質 Stage A — 紙上章程

日期：2026-09-28  
狀態：**Stage A DONE — `WIN_SOFT`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · 不下 live  
父層 live：Soft-Frozen F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] + FUSE + `SELL_a75` + `COOL_c8_f50_d21` + L1=0.05  
人話（正規化）：

```
OPEN Stage A charter: FIN 買側品質過濾 · 勝率診斷 + MDD 維持/改善 + CAGR↑ · paper only
```

動機：想同時改善買賣勝率、護／改善 MDD、抬 CAGR。賣側「等回本」已否決；本軌改測 **買側進場過濾**（少做差的 FIN BUY）。

Label: `FIN_BUY_QUALITY_STAGEA_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## 問題

在 live twin + COOL 上，有限的 FIN `buy_ok` AND 過濾能否同時：

1. held CAGR↑ ≥ +0.15pp  
2. held MDD 近持平且 tip MDD 不惡化  
3. FIN BUY 前瞻勝率（H=21）↑ ≥ +2.0pp  

## 非目標

- 不改 Soft-Frozen／Exact T+1／tip  
- 不做賣側延後認賠／FIFO 記帳改寫  
- 不下 live；HIT 最多紙上 observe ballot  

## 重現

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_stagea.py
```

詳見英文章程 `FIN_BUY_QUALITY_STAGEA_CHARTER.md`。
