# 乾粉回撤 Sleeve — 研究憲章（paper）

日期：2026-09-10  
狀態：**OPEN／僅 paper**  
人類：**「乾粉 10% + 組合／大盤回撤門檻進場 + 固定出場」vs 現況 live，看 tip／heldout／sealed，不是等 MDD**  
Soft-Frozen **KEEP** · live **KD_OPT／TEL_EQUAL KEEP** · E45 **OFF**

## 在問什麼

預留約 **10% 乾粉**，用**可觀測**的組合或大盤回撤門檻進場，再用**固定規則**出場，能否 tip-clean 勝過或共存於現況 live？

**不做：** 等「最大回撤」才進（事前不可知）。

## Live 對照（不動）

FINBAND `[0.60,0.90]` + `KD_OPT` + `TEL_EQUAL` + E45 OFF · 500M · lot 1000 · `E22_v2s_tw`

## 機制（摘要）

| 元件 | Stage A |
|---|---|
| 乾粉 | 10% 現金（或近現金） |
| 進場 | 組合 NAV 回撤 或／且 TAIEX 回撤 ≤ −D% · D∈{8,10,12,15} |
| 出場 | 持有 N 日／收回一半跌幅／創新高／時間或一半 取早 |
| 部署 | 預設打進金融 EQUAL（可加敏感性） |

門檻：tip YTD+1y · heldout · sealed（Stage A sealed 只報告）· 對標 live。

## 非動作

不上 Soft-Frozen／live KD／TEL／E45／Soft-assist live。

英文全文：`DRY_POWDER_DRAWDOWN_CHARTER.md`
