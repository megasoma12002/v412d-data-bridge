# 民股 MDD 新機制 V5 — 摘要（不改 sealed）

日期：2026-09-19  
狀態：**DRAFT**（待 ACCEPT）  
前提：N1–N3 + V2 + V3 + V4 **STOP** · Soft-Frozen **KEEP** · `#257` **FROZEN**

## 差在哪

| 先前 | 形狀 |
|---|---|
| N1–N3 | FinPriv 自路徑 DD → 關／搬／三態（無鎖存） |
| V2 | 當日二元感測 → FinPriv→0050 |
| V3 | M1 連續縮放 FinPriv |
| V4 | sealed 日曆事件閘（跨度太長 STOP） |
| SF4_DH | **整本**曝光 SHRINK |

V5：**凍結的 DH 防衛窗 FSM**（`DH_dd06_vz1p0`）只在 DEFEND 期間把 **FinPriv→0050／cash**；進場≠出場、有最長停留與復原／賽跑出場。  
不是重調舊閾值，也不是再做整本 DH 縮倉。

詳見：`PRIV_MDD_DH_PRIV_WINDOW_V5_CHARTER.md`
