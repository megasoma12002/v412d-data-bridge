# FIN 買側品質 Stage C — A∪B 混成（紙上）

日期：2026-09-28  
狀態：**Stage C OPEN** · Soft-Frozen **KEEP** · 不下 live  
父層：Stage A 種子 `SEED_MA120`（CAGR）· Stage B `B_MA120_OR_K9`（勝率／MDD）  
人話：

```
OPEN Stage C: FIN buy-quality · keep Stage A CAGR edge + Stage B WR/MDD · hybrid paper only
```

目的：有限混成能否**同時多留** A 的 CAGR 與 B 的勝率／MDD。  
非目標：不上 live；不改 Soft-Frozen／T+1。

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_stagec.py
```

詳見 `FIN_BUY_QUALITY_STAGEC_CHARTER.md`。
