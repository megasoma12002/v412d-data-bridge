# Held-MDD 幅度 ≤ 17% — 紙上研究憲章（R1）

日期：2026-09-25  
狀態：**PAPER CHARTER OPEN** · R1 **DONE** (`MDD17_HIT_CAGR_OK`)  
Soft-Frozen tip：**KEEP** · live clip / FUSE / DH：**KEEP**（本憲章不下 live）  
Books：現行 Stage-E DEFAULT + 現行股利 ledger + 現行 `live_market.csv`

標籤：`HELD_MDD17_TARGET_PAPER_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## 為什麼

2026-09-13 paper `MENU3` held MDD **−17.2%** 在現行 Stage-E 資料下已過期（約 −24%）。  
微調現行 `DH_dd06` 無法回到 |MDD|≤17%。  
問題：在**現行資料**上，有沒有**有限、新機制**能讓 held-out |MDD| ≤ **17%**（`max_drawdown >= -0.17`）？

註：口語「held MDD ≤ −17%」在本憲章定義為 **回撤幅度 ≤ 17%**。

## 禁止

- 改寫 tip 歷史、回退股利 ledger 去「算回」舊 −17%  
- 翻 Soft-Frozen clip / FUSE / DH / broker live  
- 無界搜參、重開 E45 stitch  

## R1 裁決

| 裁決 | 意義 |
|---|---|
| `MDD17_HIT_CAGR_OK` | |MDD|≤17% + tip 衛生 + held CAGR giveback≤3pp |
| `MDD17_HIT_CAGR_FAIL` | 達 |MDD| 但 giveback / tip 失敗 |
| `NO_HIT` | 無人達 |MDD|≤17% |

即使 HIT → 只開 paper observe；**不** live wire。

## 產物

- `scripts/held_mdd17_target_r1_screen.py`  
- `research/ops/HELD_MDD17_TARGET_R1_SCREEN.md`  
- `repro/held-mdd17-target-r1/`
