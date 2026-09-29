# FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`SIGNAL_WEAK`**
Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live
Parents: 0k9x `COMP_STAY_MISS` · 0k9y `COMP_CONFIRM_NO_EDGE`

## Answer

COMP 進場事件 **76** 筆（good 72.37%；2022 7 進場／good 4）。最佳特徵 `rel_5`：IC **0.1713** · hit **0.5921** (high→good) · OOF-IC -0.0075 · held-IC 0.3508。

IC 不穩：`rel_5` full IC 達 edge 門檻，但 ≤2018 ≈0／≥2019 才抬；hit 0.59 < 0.60 → **`SIGNAL_WEAK`**。

Threshold block probe `BLOCK_rel_5`（修 2022 代價 tip）：
- 2022 gap: P3 **-0.75** → probe **0.79**（ok=True）
- held↑ 3.4758 → 3.6722（ok=True）· tipY↑ 2.7325 → 2.1769（ok=False）

## Implication

- 規則層（0k9x/0k9y）+ 內生 trail/rel/vol 訊號層皆難穩修 2022 而不傷 tip。
- 接受 Path3 yearly **1/15** 殘差（2022 −0.75），或另開**外生**特徵票（非 COMP−SAT trail 自迴圈）。
- **不** promote `BLOCK_rel_5` · Path3 observe **KEEP** · Soft-Frozen／Exact T+1 **KEEP** · fill/emit **OFF** · cutover **BLOCKED**。

Screen: `FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_CHARTER.md` · Register **0k9z**

Label: `FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_DECISION_PACK_2026-09-29__SIGNAL_WEAK__NO_LIVE`
