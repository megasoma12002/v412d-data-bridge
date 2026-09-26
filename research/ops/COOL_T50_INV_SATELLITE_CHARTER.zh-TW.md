# COOL → 台50反1 衛星 — 研究 Charter（中文）

日期：2026-09-25  
狀態：**CHARTER OPEN → Stage A** · Soft-Frozen live **不動**

## 機制（寫死）

**Cool 機制成立時買 t50 反一；Cool 結束時賣出。**

- 成立 = `COOL_c8` **defending**（`cool_exposure=0.50`）  
- 結束 = exposure 回到 1（含 exit 後 cool-down 日）→ **DEF=0**  
- 標的 = **`00632R`（元大台灣50反1）**  
- 防守殘差中 α∈{0.25,0.50,1.00} 進反1，其餘現金  

Live Soft-Frozen / COOL 參數 **不改**；上 live 要另 ACCEPT。

英文全文：`COOL_T50_INV_SATELLITE_CHARTER.md`
