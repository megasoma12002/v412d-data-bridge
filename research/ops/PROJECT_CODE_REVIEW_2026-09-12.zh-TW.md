# Project Code Review — 2026-09-12（繁中摘要）

全庫 landmine + live 路徑複審。Soft-Frozen **[0.60, 0.90] KEEP** · live **KD_OPT** · E45 **OFF** · Soft-assist / Sleeve-tilt **僅 paper observe**。

## 本輪已修

1. Soft-Frozen cutover checklist 仍標 DRAFTED（實際已 FINBAND ACCEPT）→ 改 **ACCEPTED · LIVE WIRED**；L4/FIN50/BLEND 改引用 live `[0.60,0.90]`  
2. `e21 --asof` 可倒退改寫 `portfolio_state` → **拒絕 rewind**  
3. 現金不足 BUY 部分成交燒死 `order_id` → **整筆掛單等待**  
4. `ops_alert_scan` 看不到 Soft/Sleeve PAUSE → **納入掃描**  
5. Pack 仍寫 Soft-assist `SOFT_BOTH` → **K9+ + Sleeve-tilt**  
6. 月結 CI 漏 commit observe repro → **補 soft-assist / sleeve-tilt / fin-within**  
7. Live 股利金額 parse 失敗變 0 → **`require_exists` 時 fail-closed**

## 仍開著（不影響 Soft-Frozen / Soft-assist live）

- Paper `simulate_core` 仍無 SELL-before-BUY（避免 NAV churn）  
- fills vs state 非原子寫入  
- tip `e22_version` QC 可選強化  

## 不做

不上 Soft-assist / Sleeve-tilt live、不 auto-combo、不改 Soft-Frozen、不改寫 forward 歷史。

英文全文：`PROJECT_CODE_REVIEW_2026-09-12.md` · landmine：`PROJECT_LANDMINE_CODEREVIEW_2026-09-12.md`
