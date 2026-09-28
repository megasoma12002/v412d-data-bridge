# FIN×SAT tip-gap FFT 光譜 Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `FFT_SIGNAL`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9i tip-gap **`TIP_MDD_ONLY`** — binding gap = tip-drag timing · lead `r0050_63`
- COMPOSITE **`COMP_H150_x_A20`** · SAT_RELAX **`SAT_A20_RELAX`**

Human intent (normalized):

```
OPEN Stage A: FFT／Welch 能否從 tip-gap 序列找出可用週期訊號 · Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_TIPGAP_FFT_STAGEA_CHARTER_2026-09-28__DONE_FFT_SIGNAL__NO_LIVE_WIRE`

## Why

0k9i 指出要預測 tip-drag 時點。問：FFT 能否挖出穩定週期做切換？  
Belief: 若存在優勢週期（月／季尺度），bandpass 相位可當 lag-1 訊號。  
Risk: 日頻相對報酬近白噪音；偽峰；非平穩。

## Methods

1. Periodogram / Welch PSD：`rel` · `trail_rel_21/63` · `r0050` · `trail_drag` · **月聚合 rel**  
2. 報告 top periods（交易日）與功率占比  
3. 對最強帶通重建序列算 vs `fwd_rel_21` 的 IC（lag-1）  
4. Tip 窗口 vs 全樣本光譜對照  
5. **不**把 calendar year 當候選

## KEEP / forbidden

| Item | Status |
|---|---|
| Soft-Frozen · Exact T+1 · FUSE · COOL · SELL_a75 · live CONF α=0.10 | **KEEP** |
| COMPOSITE + SAT_RELAX observes | **KEEP OPEN** |
| 年切 oracle · 擴特徵表重挖 IC | **FORBIDDEN** |
| Live wire | **forbidden** |

## Verdicts

| Verdict | Meaning |
|---|---|
| `FFT_SIGNAL` | ≥1 序列有功率占比≥**3%** 的清晰峰 且 bandpass lag-1 IC \|IC\|≥0.04 |
| `FFT_WEAK` | 有峰但功率＜3% 或 IC 不過 |
| `FFT_NOISE` | 近白噪音／無可用峰 |

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_tipgap_fft_stagea.py
```

Register: **0k9j**
