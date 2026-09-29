# FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_CHARTER

Date: 2026-09-29
Status: **Stage A — COMP-entry signal analysis** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live
Parents: 0k9x `COMP_STAY_MISS` · 0k9y `COMP_CONFIRM_NO_EDGE`（規則層 exhausted）
Register: **0k9z**

## Question

SAT→COMP flip 當下，有沒有訊號能分開「好／壞 COMP 進場」，並擋 2022 類錯站？

## Method

1. Label each SAT→COMP entry by subsequent COMP-episode COMP−SAT return
2. Screen Spearman IC + median-split hit on trail/slope/rel/vol features
3. One threshold block probe on best |IC| feature vs raw P3 (2022 / held / tip)

## Non-goals

- 不關 Path3 observe · 不翻 fill/emit · 不改 Soft-Frozen

Label: `FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_CHARTER_2026-09-29__COMP_ENTRY_SIGNAL__NO_LIVE`
