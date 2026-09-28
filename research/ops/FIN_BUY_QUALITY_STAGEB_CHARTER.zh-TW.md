# FIN 買側品質 Stage B — MA120 種子微調（紙上）

日期：2026-09-28  
狀態：**Stage B OPEN** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · 不下 live  
父層 Stage A：`WIN_SOFT` · 種子 `Q_BELOW_MA120`  
人話：

```
OPEN Stage B: FIN buy-quality · seed Q_BELOW_MA120 finite micro-tune · or accept WIN_SOFT → observe
```

## 目的

在 MA120 附近做**有限**微調；若仍無 HIT，則**明確接受** Stage A `WIN_SOFT` → 建議紙上 observe（種子或更好的經濟面 challenger）。

## 非目標

不改 Soft-Frozen／T+1／tip；不下 live；不重開賣側等回本。

## 重現

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_stageb.py
```

詳見 `FIN_BUY_QUALITY_STAGEB_CHARTER.md`。
