# COOL 雙段交割 — 防守反1 → 結束正2 — 紙上憲章（Stage A）

日期：2026-09-26  
狀態：**憲章開啟 · Stage A 執行中** · Soft-Frozen **KEEP** · 不上 live  
人令：`開 dual-handoff Stage A`

## 問題

在 live twin（含 SELL_a75 + COOL）上，**防守窗持有 `00632R`、結束後確認脈衝 `00631L`（互斥交割）**，能否相對 `BASE_LIVE_FUSE_COOL` 通過 held CAGR≥+0.20pp 與 MDD／tip 門？

單腿結果**不可**直接合成：反1 已 SOFT（傷 CAGR）；正2 HIT 底座是降曝／現金，不是反1。

## 機制摘要

- 防守中：`DEF=α_inv×(1−cool)` → `00632R`  
- 結束脈衝（可 CONFIRM）：`OFF=α_lev` × H 日 → `00631L`  
- **交割鎖**：`OFF>0` 時強制 `DEF=0`  
- 有限格子見英文憲章；HIT 仍只開 paper observe

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_dual_handoff_stagea.py
```
