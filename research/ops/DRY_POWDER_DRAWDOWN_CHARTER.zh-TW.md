# 乾粉回撤 Sleeve — 研究憲章（paper）

日期：2026-09-10  
狀態：**PAPER DONE／STOP**（Stage A `NO_LIFT` · live KEEP）  
人類：**「乾粉 10% + 組合／大盤回撤門檻進場 + 固定出場」vs 現況 live，看 tip／heldout／sealed，不是等 MDD**  
Soft-Frozen **KEEP** · live **KD_OPT／TEL_EQUAL KEEP** · E45 **OFF**  
結果：`DRY_POWDER_DRAWDOWN_SCREEN.md`

## 在問什麼

預留約 **10% 乾粉**，用**可觀測**的組合或大盤回撤門檻進場，再用**固定規則**出場，能否 tip-clean 勝過或共存於現況 live？

**不做：** 等「最大回撤」才進（事前不可知）。

## Live 對照（不動）

FINBAND `[0.60,0.90]` + `KD_OPT` + `TEL_EQUAL` + E45 OFF · 500M · lot 1000 · `E22_v2s_tw`

## 機制（摘要）

| 元件 | Stage A |
|---|---|
| 乾粉 | 10% 現金（或近現金） |
| 進場 | 組合 NAV 回撤 或／且 TAIEX 回撤 ≤ −D% · D∈{10,12,15}% |
| 出場 | HOLD_40／收回一半／創新高／時間或一半取早 |
| 部署 | idle 0.9× Soft-Frozen；觸發後 +10% 打進 Financial 再 clip |

## Stage A 結果

- **37** books（36 challenger + LIVE）· 總評 **`NO_LIFT`**
- tip-clean challenger **0** · coexist **0** · beat-live **0**
- 現金拖累為主；heldout score 全 &lt; 0
- **STOP／歸檔**；live 不變。擴網格需人類另開。

## 非動作

不上 Soft-Frozen／live KD／TEL／E45／Soft-assist live。

英文全文：`DRY_POWDER_DRAWDOWN_CHARTER.md`
