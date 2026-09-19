# 民股 MDD 新機制 V2 — 摘要（不改 sealed 門檻）

日期：2026-09-19  
狀態：**DRAFT**（Stage A 待你 ACCEPT）  
前提：N1–N3 **STOP** · sealed 門檻 **不改** · Soft-Frozen **KEEP**

## 與 N1–N3 差在哪

| | N1–N3 | V2 |
|---|---|---|
| 感測 | FinPriv 自己的 DD／相對公股 | **市場廣度**、**FinPub vs TAIEX**（S2 再加 USD/TWD、央行利率） |
| 作動 | 開關／reloc／三態（已耗盡） | 沿用 N2 最佳方向：觸發時 FinPriv→**0050** |
| 門檻 | sealed≥0 | **相同**（不放寬） |

## S1（ACCEPT 後才跑）

- `S1_BREADTH_SMA120`：FIN∪TEL 跌破 SMA120 比例  
- `S1_FINPUB_TAIEX_Z`：公股相對加權 vs 大盤 60d z  
- `S1_OR_MID`：兩者中檔 OR  

詳見：`PRIV_MDD_SENSOR_MECH_V2_CHARTER.md`
