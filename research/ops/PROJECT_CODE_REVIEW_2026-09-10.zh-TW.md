# 專案 Code Review — 2026-09-10（全 repo）

範圍：Soft-assist observe（#185）後的 live／共用模擬路徑 landmine。  
Soft-Frozen **[0.60, 0.90] KEEP** · live **KD_OPT KEEP** · E45 **OFF** · Soft-assist **僅 paper observe**

## 總評

Live 路徑健康。本輪修了三件實害：

1. **CI live writer** 還硬編 `--capital 3000000`（wipe 會種回 3M）→ 改吃 DEFAULT **500M**
2. **Soft-assist 月結** 依賴被 gitignore 的 `*_daily_nav.csv` → 可回退到已追蹤的 `dual_paper_nav_compare.csv`
3. **MIX/DUAL** 路徑靜默丟掉 `sell_scores` → 已轉發／生效

未動 Soft-Frozen／不上 Soft-assist live。詳見英文：`PROJECT_CODE_REVIEW_2026-09-10.md` · `PROJECT_LANDMINE_CODEREVIEW_2026-09-10.md`
