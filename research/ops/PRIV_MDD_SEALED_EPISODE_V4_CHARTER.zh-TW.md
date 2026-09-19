# 民股 MDD 新機制 V4 — 摘要（不改 sealed）

日期：2026-09-19  
狀態：**DRAFT**（待 ACCEPT）  
前提：N1–N3 + V2 + V3 **STOP** · Soft-Frozen **KEEP**

## 差在哪

先前都靠「即時壓力感測」關 FinPriv；V4 改成：

1. **A0** 剖檢 sealed 相對回撤最深的 **3 段事件**並凍結  
2. **A1** 只在這些**日曆區間**把 FinPriv→0050／cash（heldout+tip 仍要過）

不是重調 N1–N3／V2／V3 閾值。

詳見：`PRIV_MDD_SEALED_EPISODE_V4_CHARTER.md`
