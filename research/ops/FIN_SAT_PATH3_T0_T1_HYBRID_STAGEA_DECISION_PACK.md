# FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_DECISION_PACK

Date: 2026-09-28 · Verdict: **`T0_SAMEBAR_ONLY`**
Status: Soft-Frozen **KEEP** · Exact T+1 fills **KEEP** · Path3 observe **KEEP** · cutover **BLOCKED** · no live

## Answer

Realistic live Path3（决策用当日 close `SAT_LEAD`，下单／收益从下一交易日开始）在 NAV 模型上 **≡** `SAT_LEAD.shift(1)`，与 0k9q 的 `R_SAT_LEAD_L1` 相同。

- **`P3_T0_STATE`（same-bar）**: held↑ 3.4758 · tipY↑ 2.7325 · tip-clean HIT-shaped
- **`P3_HYBRID_T1_FILL`（T+1 fill）**: held↑ 1.2962 · tipY↑ -8.4925 · tipClean=False
- Gap tip YTD: **11.225** pp（same-bar 乐观幅度）

## Implication

- Observe `P3_T0_STATE` 数字 **不能**直接当 live 预期。
- 若 live 只做「切换决策 T+0 + 买卖仍 Exact T+1」，回测 **tip 不过**（YTD CAGR↑ 为负）。
- Path3 observe 可继续（paper same-bar 上界）；**不要**把 observe 数字当成 fill-realistic live edge。
- Soft-Frozen／全局 Exact T+1／CONF α **KEEP**；cutover 仍 **BLOCKED**。

## Hybrid yearly vs live

| Year | base% | hybrid% | Δpp | winner |
|---:|---:|---:|---:|---|
| 2012 | 0.55 | 1.2 | 0.65 | HYBRID |
| 2013 | 7.26 | 4.2 | -3.06 | BASE |
| 2014 | 7.27 | 5.99 | -1.27 | BASE |
| 2015 | -1.64 | -3.68 | -2.04 | BASE |
| 2016 | 14.56 | 13.75 | -0.81 | BASE |
| 2017 | 17.58 | 21.36 | 3.78 | HYBRID |
| 2018 | 7.65 | 4.08 | -3.56 | BASE |
| 2019 | 20.49 | 22.55 | 2.06 | HYBRID |
| 2020 | 5.85 | 9.17 | 3.32 | HYBRID |
| 2021 | 20.63 | 20.07 | -0.56 | BASE |
| 2022 | 6.5 | 3.19 | -3.31 | BASE |
| 2023 | 12.7 | 22.66 | 9.96 | HYBRID |
| 2024 | 10.63 | 10.02 | -0.61 | BASE |
| 2025 | 11.21 | 15.73 | 4.52 | HYBRID |
| 2026 | 34.7 | 29.48 | -5.22 | BASE |

W–L: **6–9**

Screen: `FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_CHARTER.md` · Register **0k9s**

Label: `FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_DECISION_PACK_2026-09-28__T0_SAMEBAR_ONLY__NO_LIVE`
