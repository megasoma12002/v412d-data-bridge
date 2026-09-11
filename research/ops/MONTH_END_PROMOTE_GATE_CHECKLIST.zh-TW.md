# 月結 Promote Gate Checklist — Soft-assist ∥ Sleeve-tilt（只服務 observe）

日期：2026-09-11  
狀態：**已起草 · 未授權 · 不上 live**  
範圍：只服務兩條 operating observe；**不**開 live cutover。  
每月預設：**KEEP OBSERVE**。某軌 A–I 全 YES → 最多標 `READY_FOR_DEDICATED_ACCEPT_BALLOT`（仍要人類專用 ACCEPT 字串）。

| 軌 | Challenger | Base |
|---|---|---|
| Soft-assist | `SOFT_CHAMP_PLUS_K9_LT30_a10` | `LIVE_KD_OPT` |
| Sleeve-tilt | `SLEEVE_BELOW_MA60_a01` | `LIVE_STACK` |

## 閘門（每軌分開填）

A 雙紙 OPERATING／Exact T+1 · B tip YTD+1y 無 PAUSE · C tip 無 ALERT（或書面豁免）· D heldout score>0 · E month-end alerts=none · F challenger ID 未換 · G Soft-Frozen／KD／TEL／E45 未因本 pack 改動 · H **未**提 Soft-assist×sleeve combo · I live cutover checklist 仍 BLOCKED

## 禁止

上 live、自動 combo、單月綠燈當 promote、把 paper 數字當 live claim。

## 操作

`python3 scripts/ops_month_end_paper_pack.py` → 填英文頁月結表。

英文全文：`MONTH_END_PROMOTE_GATE_CHECKLIST.md`
