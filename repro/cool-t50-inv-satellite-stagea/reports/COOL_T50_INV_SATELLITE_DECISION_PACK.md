# COOL × 台50反1 — Decision Pack (Stage A)

Date: 2026-09-25 · Generated `2026-09-25T14:35:39Z`  
Status: **COOL_INV_SOFT** · Soft-Frozen **KEEP** · live wire **false**

## Human rule

**Cool 機制成立時買台50反1（`00632R`）；Cool 結束時賣出。**  
α = 防守殘差進反1 的比例 ∈ {0.25, 0.50, 1.00}。

## Verdict

**0 HIT / coexist.** 相對 `BASE_LIVE_FUSE_COOL`：

| book | α | held CAGR↑ | sealed MDD↑ | tip |
|---|---:|---:|---:|---|
| `COOL_INV_A25` | 0.25 | **−0.80** | **+0.04** | Y |
| `COOL_INV_A50` | 0.50 | −1.82 | −1.40 | N |
| `COOL_INV_A100` | 1.00 | −4.46 | −8.38 | N |

Reading: 小額反1（α=0.25）在 COOL 防守窗 **略改善 sealed MDD**、held MDD↑ 很大，但 **CAGR 明確變差**（與「想抬 CAGR」相反）。α 愈大，CAGR 與 sealed MDD 都更差。  
`ALWAYS_A50`（非防守也持有）CAGR↑ 但 sealed MDD 崩 — 不作 promote。

Cool defend 日佔比 ≈ **16%**。

## Binding

1. Soft-Frozen live + `COOL_c8` 參數 **KEEP**。  
2. Do **not** live-wire `00632R` from this Stage A.  
3. 本機制 **不像 CAGR 進攻槓桿**；若目標改成「寧願 CAGR 換 MDD」需 human 改 objective 再開。

## Refs

- Charter: `COOL_T50_INV_SATELLITE_CHARTER.md`  
- Screen: `COOL_T50_INV_SATELLITE_STAGEA_SCREEN.md`  

Label: `COOL_T50_INV_SATELLITE_DECISION_2026-09-25__COOL_INV_SOFT`
