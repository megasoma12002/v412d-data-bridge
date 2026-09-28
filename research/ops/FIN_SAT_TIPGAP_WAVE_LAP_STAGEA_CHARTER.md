# FIN×SAT tip-gap 小波／拉普拉斯 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `WAVE_LAP_SIGNAL`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9j FFT **`FFT_SIGNAL`** — 日頻白噪音；平滑後 85/128/256td 帶通可輔助
- 0k9i tip-gap 時域 **`TIP_MDD_ONLY`** — lead `r0050_63`
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: 小波／拉普拉斯分析 tip-gap 能否找出可用時頻／極點訊號 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_CHARTER_2026-09-28__DONE_WAVE_LAP_SIGNAL__NO_LIVE_WIRE`

## Why

FFT 給全域頻率；小波給 **時變尺度**，拉普拉斯給 **衰減極點／因果模式**。  
Belief: tip-drag 是間歇事件，小波比 FFT 更對；拉普拉斯可抓指數衰減／增長模。  
Risk: 平滑偽影；數值 Laplace 不穩；偽尺度。

## Methods (numpy-only)

1. **Morlet CWT** on `rel` · `trail_rel_63` · tip-window — scale→period 圖；全局／tip 平均功率；ridge 主尺度  
2. **Numerical unilateral Laplace** \(X(σ+jω)=\sum x[n]e^{-(σ+jω)n}\) 網格 — 找 |X| 峰與主極點候選  
3. Wavelet ridge / Laplace 峰對應 period → **lag-1 重建訊號** vs `fwd_rel_21` IC  
4. 對照 0k9j 帶通結果

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 年切 oracle · 單靠變換當 live | **FORBIDDEN** |
| Live wire | **forbidden** |

## Verdicts

| Verdict | Meaning |
|---|---|
| `WAVE_LAP_SIGNAL` | 小波或 Laplace 有清晰主尺度／極點 且 lag-1 \|IC\|≥0.04 |
| `WAVE_LAP_WEAK` | 有結構但 IC 不過／僅平滑偽影 |
| `WAVE_LAP_NOISE` | 無可用時頻／極點 |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_tipgap_wave_lap_stagea.py
```

Register: **0k9k**
