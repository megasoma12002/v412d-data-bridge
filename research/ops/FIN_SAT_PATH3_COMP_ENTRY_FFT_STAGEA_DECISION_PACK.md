# FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_DECISION_PACK

Date: 2026-09-29 · Verdict: **`FFT_ENTRY_WEAK`**
Status: Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live
Parents: 0k9z `SIGNAL_WEAK` · 0k9j `FFT_SIGNAL` · 0k9p `FFT_LAG_NO_EDGE`

## Answer

COMP 進場 **76** 筆。FFT 最佳 `w256_dphase`：IC **0.1908** · hit **0.5** · OOF 0.2981 · held 0.0968。
時域基線 `rel_5`：IC **0.1713** · hit **0.5921** · fft_beats_td=**True**。

Threshold block `BLOCK_w256_dphase`：
- 2022: P3 **-0.75** → probe **-1.08** (ok=False)
- held↑ 3.4758 → 2.7535 (ok=False) · tipY↑ 2.7325 → -0.7996 (ok=False)

## Implication

- FFT `|IC|` 可略高於 `rel_5`，但 hit≈0.50、held-IC 弱、block probe 傷 2022／held／tip → **不可用**。
- 與 0k9p 一致：因果譜是 trail 濾波，不解 COMP 進場品質；停此譜線。
- 接受 Path3 yearly **1/15** 殘差，或另開**外生**（非 COMP−SAT／trail 自迴圈）特徵票。
- Path3 observe **KEEP** · Soft-Frozen／Exact T+1 **KEEP** · fill/emit **OFF** · cutover **BLOCKED**。

Screen: `FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_SCREEN.md` · Charter: `FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_CHARTER.md` · Register **0ka0**

Label: `FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_DECISION_PACK_2026-09-29__FFT_ENTRY_WEAK__NO_LIVE`
