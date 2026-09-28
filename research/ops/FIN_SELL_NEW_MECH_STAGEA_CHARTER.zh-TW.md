# FIN 賣側新機制 Stage A — 紙本憲章

日期：2026-09-28  
狀態：**Stage A DONE — `MDD_BLOCK`** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · 無 live  
前軌：`FIN_SELL_QUALITY_*` → `MDD_BLOCK` / `NO_EDGE`（MA-dampen 家族耗盡）

人話：開 **新賣機制**（timing／確認），不是再掃 MA／dampen；仍要過 CAGR+MDD+tip；賣勝率當診斷。

排除：hard MA／RSI／K9 水位閘、soft-dampen、loss-defer。

跑：`PYTHONPATH=scripts python3 scripts/fin_sell_new_mech_stagea.py`
