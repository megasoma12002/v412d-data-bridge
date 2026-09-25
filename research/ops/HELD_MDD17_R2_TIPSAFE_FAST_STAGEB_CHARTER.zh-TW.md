# Tip-safe FAST — 紙上憲章（R2 Stage B）

日期：2026-09-25  
狀態：**PAPER CHARTER OPEN**  
父：R2 CAGR→0 · 人接 MDD 下限 −14.5%  
Soft-Frozen tip：**KEEP** · live **KEEP**

標籤：`HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## 為什麼

`FAST_x08_ex06_f50_d21` held：**15.00% / −14.45%**（gb **+0.56pp**），但 **tip 窗 MDD 變差**。  
Stage B：有限 tip 安全 FAST 變體，目標保住 ~0.56pp gb 且 tip YTD/1y MDD 不差於 LIVE。

## 目標

- held MDD ∈ [−14.5%, −13%]  
- held gb ≤ 0.70pp（stretch ≤ 0.56pp）  
- tip YTD + 1y：`mdd_improve_pp >= 0`

## 裁決

`TIPSAFE_STRETCH` / `TIPSAFE_PRESERVE` / `TIPSAFE_OK` / `TIP_FAIL` / `NO_BAND`  
HIT → 只開 paper observe，不下 live。

## 產物

`scripts/held_mdd17_r2_tipsafe_fast_stageb_screen.py` · `HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN.md`
