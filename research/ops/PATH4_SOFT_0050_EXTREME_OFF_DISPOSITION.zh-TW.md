# Path4 extreme OFF 處置 — FULL_CASH vs Stage A renorm（中文摘要）

日期：2026-09-30  
狀態：**OPEN — 等人裁** · 建議 **`KEEP_STAGEA_RENORM`** · Soft KEEP · 無 live

詳見英文 SSOT：`PATH4_SOFT_0050_EXTREME_OFF_DISPOSITION.md`

| 臂 | 含義 | held | tipY |
|---|---|---:|---:|
| `SW_TRAIL_001` | Soft-0050 ON↔OFF renorm（Stage A） | +0.40 | +0.19 |
| `SW_CASH_ETF_00025` | 0050→現金（較近 extreme） | +0.49 | −0.32 |
| `SW_FULL_CASH_00025` | Soft-core 全現金風險關閉 | +6.51 | +6.12 |

**建議：** Path4 Soft-0050 主線留 Stage A renorm；FULL_CASH 是另一機制（Soft-core risk-off），若要走再開新 charter。

```
PATH4 DISPOSITION: KEEP_STAGEA_RENORM
(Path4 Soft-0050 primary = SW_TRAIL_001 · FULL_CASH = separate Soft-core risk-off track · no live)
```
