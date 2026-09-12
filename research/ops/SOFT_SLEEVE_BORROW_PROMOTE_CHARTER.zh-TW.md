# Soft ∥ Sleeve 外借促升 — 研究章程（paper Stage A）

日期：2026-09-12  
狀態：**PAPER SCREEN DONE** · 判決 **`HAS_PROMOTE_SHAPED_CANDIDATE`** · **不接 live** · **禁止 Soft×Sleeve 融合**  
人類：把這幾輪查到的資料進行研究看能不能測試出新的更優解

Screen：`SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.md` · Script：`scripts/e16_soft_sleeve_borrow_promote_screen.py`

Soft-Frozen **clips KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · E45 **OFF**  
Soft-assist observe **KEEP** `SOFT_CHAMP_PLUS_K9_LT30_a10` · Sleeve-tilt observe **KEEP** `SLEEVE_BELOW_MA60_a01`

## Stage A 結果（asof 2026-09-11）

| 軌 | 判決 | Promote-shaped 重點 |
|---|---|---|
| Soft | **`PROMOTE_SHAPED_BEATS_OBSERVE`** | `…K9_LT30_a10__SELL_a05`（held 0.101 vs observe 0.085）· 亦有 `…_a15` |
| Sleeve | **`MDD_CLEAR_BEATS_LIVE`** | `SLEEVE_RSI14_LT30_a02` tip-MDD clean + held>0（升幅很小） |
| 總 | **`HAS_PROMOTE_SHAPED_CANDIDATE`** | 僅 paper — 換 observe 需專用 ballot · **不自動上線** |

Seed `SLEEVE_BELOW_MA60_a01` 仍 tip-clean 但 **tip_mdd_clean=False**。降 α 的 MA60 鄰近點未能在 held>0 下清掉 tip MDD。

## 問題

外借資訊 Stage A：是否存在 **promote-shaped** 紙上挑戰者

1. **Soft 軌** — tip-clean + tip MDD clean + held-out 勝過現有 Soft-assist observe，或  
2. **Sleeve 軌** — tip-clean + tip MDD clean（清掉月末 MDD ALERT 型態）+ held-out > 0 vs `LIVE_STACK`？

**Promote-shaped** = tip YTD+1y PASS **且** tip YTD+1y MDD 不劣於基準 **且** held-out score > 0。

## 外借對照

| 筆記 | 本地對應 |
|---|---|
| Note 2 — soft 告知、不取代 | Soft 在 K9+ observe 附近做加分振幅網格 |
| Note 3 — tilt 需過分散／風險衛生 | Sleeve 降 α／鄰近訊號 + **tip MDD 衛生** |
| Notes 4/5 — 互補 ≠ 自動融合 | Soft ∥ Sleeve 分開；**禁止融合** |

## 非動作

- 不單憑本 screen 換 Soft-assist／Sleeve-tilt observe  
- 不自動 Soft×Sleeve 融合  
- 不改 live Soft-assist／Sleeve-tilt／Soft-Frozen／KD／TEL／E45  
- 不重開硬 AND  

## Label

`SOFT_SLEEVE_BORROW_PROMOTE_CHARTER_2026-09-12__HAS_PROMOTE_SHAPED_CANDIDATE`
