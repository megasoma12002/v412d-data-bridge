# 民股 MDD 新機制 V6 — 摘要（不改 sealed）

日期：2026-09-19  
狀態：**DRAFT**（待 ACCEPT）  
前提：N1–N3 + V2 + V3 + V4 + V5 **STOP** · Soft-Frozen **KEEP** · `#257` **FROZEN**

## 差在哪

V4 剖出 offense 相對 `LIVE_PUB` 是「淺但長」的相對回撤；V5 稀疏 DH 窗仍補不到。

V6：用**未阻尼影子 NAV**算 `DD_rel`，連續  
`FinPriv' = FinPriv · (1 − c · u)`（δ=0.05 凍結）→ residual 到 0050／cash。

不是日曆閘、不是 DH 鎖存、不是 M1、不是 FinPriv 自路徑 DD。

詳見：`PRIV_MDD_SHADOW_RELNAV_V6_CHARTER.md`
