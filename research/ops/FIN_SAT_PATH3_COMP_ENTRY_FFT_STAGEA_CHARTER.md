# FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_CHARTER

Date: 2026-09-29
Status: **Stage A — COMP-entry FFT signal** · Soft-Frozen **KEEP** · Path3 observe **KEEP** · fill/emit **OFF** · cutover **BLOCKED** · no live
Parents: 0k9z `SIGNAL_WEAK` · 0k9j `FFT_SIGNAL` · 0k9p `FFT_LAG_NO_EDGE`
Register: **0ka0**

## Question

SAT→COMP 進場當下，0k9j 帶通（85/128/256td）因果 STFT 特徵能否比時域 `rel_5` 更穩地分開好／壞 COMP 進場？

## Method

1. Label SAT→COMP by subsequent episode COMP−SAT
2. Causal STFT phase/amp/recon/dphase @ win 64/128/256 on trail_rel_63
3. Spearman IC + median hit · compare vs `rel_5` · one FFT block probe

## Non-goals

- 不關 Path3 observe · 不翻 fill/emit · 不改 Soft-Frozen · 不做非因果全樣本 bandpass

Label: `FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_CHARTER_2026-09-29__COMP_ENTRY_FFT__NO_LIVE`
