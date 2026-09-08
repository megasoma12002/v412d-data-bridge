# E45 M3 BIL_FX v1 — 中文摘要

日期：2026-09-08  
判決：**FAIL_AUTOPSY**  
全文：`research/ops/E45_M3_BIL_FX_V1.md`

## 做了什麼

離開 C35×regime 軟閘門，把 M3 三態機的 actuator 從失敗的 TEL 換成 M2 過關的 **RELOC_BIL_FX**（滯後規則與 v0 相同，凍結後才跑分數）。

## 結果

| 書 | held-out | tip |
|---|---:|---|
| 連續 C35（現行 observe） | **+1.81** | 髒 |
| M3_BIL_FX_V1 | **−2.10** | 更髒（YTD giveback ~15pp） |

固定 u 的離散態（約 28% 非 NORMAL）相對連續 `c·s` **過度犧牲 CAGR**，換真 DEF 救不了 M3。

## 接下來（仍不碰 C35×regime 軟旋鈕）

1. 操作上：C35 看分數 + Soft_A 雙軌清 tip（四條路）  
2. 研究上：要衝分數需 **新感測器（M1 v1 / 新免費序列）**，或接受現有資料上機制梯已薄  
3. Soft-Frozen KEEP · stitch FORBIDDEN · observe lock 未改  
