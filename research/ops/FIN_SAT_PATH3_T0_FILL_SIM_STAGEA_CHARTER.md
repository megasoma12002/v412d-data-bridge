# FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_CHARTER

Date: 2026-09-29
Status: **Stage A — fill-carve simulate** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill flag **OFF** · cutover **BLOCKED** · no live · no broker
Parents: 0k9r Path3 observe OPEN · carve `T0_CARVE_FIN_SAT_SWITCH` · fill PREP ballot (DRAFT)
Register: **0k9v**

## Question

若最終 ACCEPT live fill carve-out（Path3 tagged switch 同 bar 以 `reference_close` 成交），相對維持 Exact T+1（無 carve），paper NAV 模擬效果如何？

## Method

- `FILL_CARVE_CLOSE`: SAT_LEAD(day t) 權重當日全額進收益 ≡ observe `P3_T0_STATE` / live MOC close
- `STATUS_QUO_T1`: SAT_LEAD.shift(1) ≡ 決策當日、成交／收益 T+1 open
- Gates: held CAGR / MDD band · tip YTD+1y clean · vs SAT held extra
- 非整本帳 T+0；僅 Path3 COMP↔SAT 切換 carve

## Non-goals

- 不翻 `LIVE.live_t0_carve_fin_sat_switch_fill`
- 不接 Path3 order emitter / broker
- 不改 Soft-Frozen clips / CONF α / 全局 Exact T+1

Label: `FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_CHARTER_2026-09-29__FILL_SIM__NO_LIVE`
