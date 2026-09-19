# 民股 MDD 新機制 V3 — 摘要（不改 sealed）

日期：2026-09-19  
狀態：**DRAFT**（Stage A 待 ACCEPT）  
前提：N1–N3 + V2 S1–S2 **STOP** · Soft-Frozen **KEEP**

## 差在哪

| | N1–N3 / V2 | V3 |
|---|---|---|
| 感測 | FinPriv 自 DD，或單特徵二元觸發 | **E45 M1 合成強度** `s_t`（已凍結） |
| 作動 | 開關／整段搬到 0050 | FinPriv **連續縮放** `×(1−c·s)` |
| 殘量 | — | →0050 或 cash |

`c ∈ {0.25, 0.50, 0.75, 1.00}` × 兩種殘量 = 8 本。

詳見：`PRIV_MDD_M1_SCALE_V3_CHARTER.md`
