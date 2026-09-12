# 月結 Promote Gate Checklist — Soft-assist ∥ Sleeve-tilt（只服務 observe）

日期：2026-09-12（pack asof **2026-09-11**）  
狀態：**操作中 checklist · 不上 live** · 本月列 **KEEP_OBSERVE** / **KEEP_OBSERVE**  
範圍：只服務兩條 operating observe；**不**開 live cutover。  
每月預設：**KEEP OBSERVE**。某軌 A–I 全 YES → 最多標 `READY_FOR_DEDICATED_ACCEPT_BALLOT`（仍要人類專用 ACCEPT 字串）。

| 軌 | Challenger | Base |
|---|---|---|
| Soft-assist | `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` | `LIVE_KD_OPT` |
| Sleeve-tilt | `SLEEVE_RSI14_LT30_a0225` | `LIVE_STACK` |

本月（asof 2026-09-11）：兩軌 alerts=none · Soft held≈+0.101 · Sleeve held≈+0.099 · overlap heldout corr≈+0.112 · **high_joint_dd=True** → Gate H 維持不 combo。詳見英文月結表。

## 閘門（每軌分開填）

A 雙紙 OPERATING／Exact T+1 · B tip YTD+1y 無 PAUSE · C tip 無 ALERT（或書面豁免）· D heldout score>0 · E month-end alerts=none · F challenger ID 未換 · G Soft-Frozen／KD／TEL／E45 未因本 pack 改動 · H **未**提 Soft-assist×sleeve combo · I live cutover checklist 仍 BLOCKED

## Soft ↔ Sleeve overlap（報告欄 · 不開 combo）

來源：`SOFT_SLEEVE_OBSERVE_OVERLAP.md`  
看 heldout：**corr／same-sign／both−／joint DD**。高 overlap＝更不該自動拼；低 overlap 也**不**等於可以拼。

Seed 2026-09-10：corr **−0.025** · same-sign **55%** · both− **26.5%** · joint DD **33%**。

## 禁止

上 live、自動 combo、單月綠燈當 promote、把 paper 數字當 live claim、用 overlap 開 joint ACCEPT。

## 操作

`python3 scripts/ops_month_end_paper_pack.py` → 看兩條 monitor + overlap → 填英文頁月結表。

英文全文：`MONTH_END_PROMOTE_GATE_CHECKLIST.md`
