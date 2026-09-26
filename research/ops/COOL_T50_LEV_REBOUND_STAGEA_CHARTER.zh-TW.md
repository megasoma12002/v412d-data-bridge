# COOL 結束買台50正2（00631L）搶反彈 — 紙上憲章（Stage A）

日期：2026-09-26  
狀態：**CHARTER OPEN · Stage A DONE → `MDD_BLOCK`** · Soft-Frozen live **KEEP** · live wire **false**

Stage A 摘要：α×H 網 **0 HIT**。小額短窗有 CAGR↑（如 `REB_A10_H10` +0.74pp）但 sealed／held MDD 門不過 → **`MDD_BLOCK`**。長抱／防守進場對照更差。不開 live。

## 人話機制

**Cool 結束（防守→全倉）當日起，短窗持有 `00631L`（台50正2）搶反彈；防守中不加槓桿。**

| 狀態 | 動作 |
|---|---|
| COOL 防守中 | 正2 權重 = 0 |
| COOL 結束日（exit） | 開始脈衝：持有 `00631L` 共 **H** 個交易日 |
| 脈衝結束 | 賣出正2 |

## 問題

相對 live twin `BASE_LIVE_FUSE_COOL`（含 **SELL_a75**），exit 後 `00631L` 脈衝能否在 held CAGR≥**+0.20pp** 且不炸 MDD／tip？

## 有限網格

- `α ∈ {0.10, 0.25, 0.50}`（正2 權重；由 Soft 袖縮放出資）  
- `H ∈ {3, 5, 10, 21}`  
- 對照：`ALWAYS_A25`（長抱衰減）· `DEFEND_A25_H5`（錯時機：防守進場）

## 裁決

`COOL_LEV_REBOUND_HIT` ／ `SOFT` ／ `MDD_BLOCK` ／ `NO_LIFT`  
即使 HIT → 只開 paper observe；live 要 Class D ACCEPT。

## 不做

- 改 COOL 參數 · Soft-Frozen 翻邊 · tip 改寫 · broker · 重開 00632R 網

## 重跑

```bash
PYTHONPATH=scripts python3 scripts/cool_t50_lev_rebound_stagea.py
```

標籤：`COOL_T50_LEV_REBOUND_STAGEA_CHARTER_2026-09-26__OPEN`
