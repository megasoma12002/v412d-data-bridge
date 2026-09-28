# FIN 賣側診斷角色 Stage A — 紙本憲章

日期：2026-09-28  
狀態：**Stage A OPEN** · Soft-Frozen **KEEP** · `SELL_a75` **KEEP** · **不閘 `fin_sell_ok`** · 無 live

人話：只在 live 賣出上**標註／診斷**條件勝率，不改成交、不加硬閘。DIAG_SIGNAL ≠ observe ≠ live。

跑：`PYTHONPATH=scripts python3 scripts/fin_sell_diag_role_stagea.py`
