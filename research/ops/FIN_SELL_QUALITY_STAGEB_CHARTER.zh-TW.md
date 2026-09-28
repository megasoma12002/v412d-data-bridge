# FIN 賣側品質 Stage B — 章程（繁中摘要）

日期：2026-09-28  
狀態：**Stage B DONE — `NO_EDGE`** · Soft-Frozen / Exact T+1 / COOL / **SELL_a75 KEEP** · 無 live wire  
父層 Stage A：`MDD_BLOCK`（硬閘抬 CAGR 但傷 MDD）

```
OPEN Stage B: FIN sell-quality · soft-dampen · optional MDD soft −1.0pp · KEEP SELL_a75 · paper only
```

## 做法

1. 不用硬 `fin_sell_ok`，改 **soft-dampen / boost-only**  
2. 嚴格 MDD −0.25pp 才算 HIT；另報 **放寬 −1.0pp** 作 observe 候選  
3. CAGR↑ = chal − base；禁止等回本  

```bash
PYTHONPATH=scripts python3 scripts/fin_sell_quality_stageb.py
```

詳見 `FIN_SELL_QUALITY_STAGEB_CHARTER.md`。
