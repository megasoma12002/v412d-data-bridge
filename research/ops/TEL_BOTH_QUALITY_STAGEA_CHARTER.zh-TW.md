# TEL 買賣側聯優 Stage A — 章程（繁中摘要）

日期：2026-09-28  
狀態：**Stage A OPEN** · Soft-Frozen / Exact T+1 / COOL / FIN **KD_OPT** + **SELL_a75 KEEP** · TEL live **T3_COOL_INV_VOL20 KEEP** · 無 live wire

```
OPEN Stage A: TEL 買賣側聯優 · 有限 buy×sell grid on T3_COOL_INV_VOL20 · MDD持平/改善 + CAGR↑ · KEEP Soft-Frozen · paper only
```

CTRL = live twin（FIN 鎖死 · TEL cool-gated INV_VOL20）。只挑戰 `tel_buy_ok` / `tel_sell_ok` / `tel_sell_scores`。  
CAGR↑ = **chal − base**。HIT：`TEL_QUALITY_HIT`。Screen 於跑數時填入。

```bash
PYTHONPATH=scripts python3 scripts/tel_both_quality_stagea.py
```

詳見 `TEL_BOTH_QUALITY_STAGEA_CHARTER.md`。
