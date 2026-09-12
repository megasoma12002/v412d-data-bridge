# Soft-Assist DL Tip-MDD／Giveback 賣邊 Stage A — 研究憲章（僅 paper）

日期：2026-09-12  
狀態：**PAPER STAGE A DONE** · 判決 **`BEATS_LIVE_NO_OBSERVE_LIFT`**  
母鎖定：`RESEARCH_POSTURE_LOCK_RULEPATH_FIRST_DL_NEW_MECH`

腳本：`scripts/e16_soft_dl_tip_mdd_sell_stagea_screen.py`

## 問題

在 Soft observe **買** soft 固定下，用 **前瞻 path-MDD／giveback** 標籤訓練極小 MLP Soft **賣** 分數，能否 tip-MDD 衛生並 **promote-shaped** 勝過 Soft observe `…__SELL_a05`？

## 設計摘要

- 角色：賣邊（非 Soft-buy 加深、非 T2 重開）  
- 標籤：H=10 path-MDD 分類／−path-MDD 回歸  
- 對照：T3 `fwd&lt;0` 控制 + Soft observe／prior Soft／live base  
- 不接 live · 不換 Soft／Sleeve observe · 不融合  

## Label

`SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER_2026-09-12__BEATS_LIVE_NO_OBSERVE_LIFT`
