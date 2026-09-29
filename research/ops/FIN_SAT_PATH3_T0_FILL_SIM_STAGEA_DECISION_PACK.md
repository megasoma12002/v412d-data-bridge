# FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`FILL_CARVE_CLOSE_ONLY`**
Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill flag **OFF** · cutover **BLOCKED** · no live · no broker

## Answer

模擬「ACCEPT fill carve → Path3 切換單同 bar 以 close／`reference_close` 成交」的回測效果：

- **`FILL_CARVE_CLOSE`**: held↑ **3.4758** · tipY↑ **2.7325** · tip1y↑ 1.7356 · tipClean=True · shaped=True
- **`STATUS_QUO_T1`（無 carve）**: held↑ 1.2962 · tipY↑ **-8.4925** · tipClean=False
- Tip YTD gap（carve − T1）: **11.225** pp

### Sealed 2023+

| Book | CAGR | MDD |
|---|---:|---:|
| `CTRL_LIVE_A10` | 0.195101 | -0.062022 |
| `FILL_CARVE_CLOSE` | 0.242923 | -0.063673 |
| `STATUS_QUO_T1` | 0.219369 | -0.067806 |

## Implication

- 建議路徑若走到 live fill carve（同 bar close），paper 預期 **≈ observe `P3_T0_STATE`**：held + tip 形狀 HIT。
- 若不開 carve、只做 T+1 成交，tip YTD **為負**（與 hybrid／0k9s 同結論）。
- 本 Stage A **不**翻 flag、**不**接下單；僅給 ACCEPT fill 前的效果上限。
- Soft-Frozen／全局 Exact T+1／CONF α **KEEP**；cutover 仍 **BLOCKED**。

## Yearly `FILL_CARVE_CLOSE` vs live

| Year | base% | carve% | Δpp | winner |
|---:|---:|---:|---:|---|
| 2012 | 0.55 | 1.2 | 0.65 | FILL_CARVE |
| 2013 | 7.26 | 11.46 | 4.2 | FILL_CARVE |
| 2014 | 7.27 | 11.31 | 4.04 | FILL_CARVE |
| 2015 | -1.64 | 0.81 | 2.44 | FILL_CARVE |
| 2016 | 14.56 | 15.76 | 1.19 | FILL_CARVE |
| 2017 | 17.58 | 21.36 | 3.78 | FILL_CARVE |
| 2018 | 7.65 | 10.1 | 2.46 | FILL_CARVE |
| 2019 | 20.49 | 22.73 | 2.24 | FILL_CARVE |
| 2020 | 5.85 | 9.17 | 3.32 | FILL_CARVE |
| 2021 | 20.63 | 25.29 | 4.66 | FILL_CARVE |
| 2022 | 6.5 | 5.75 | -0.75 | BASE |
| 2023 | 12.7 | 22.78 | 10.09 | FILL_CARVE |
| 2024 | 10.63 | 10.66 | 0.04 | FILL_CARVE |
| 2025 | 11.21 | 16.07 | 4.86 | FILL_CARVE |
| 2026 | 34.7 | 36.36 | 1.66 | FILL_CARVE |

W–L: **14–1**

Screen: `FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_CHARTER.md` · Register **0k9v**

Label: `FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_DECISION_PACK_2026-09-29__FILL_CARVE_CLOSE_ONLY__NO_LIVE`
