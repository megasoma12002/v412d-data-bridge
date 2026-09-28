# FIN×SAT FFT-phase × Exact T+1 lag Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `FFT_LAG_NO_EDGE`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · SAT_A20_RELAX observe **KEEP** · no live wire  
Parents:
- 0k9o tip-lead **`TIP_LAG_BLOCK`** — 早 1 日足夠；外部 lead 弱
- 0k9j tip-gap FFT **`FFT_SIGNAL`** — trail ~85/128/256td；assist≠replace
- 0k9n 局部互斥 **`TIP_LAG_BLOCK`**

Human intent (normalized):

```
OPEN Stage A: 傅立葉／因果相位能否解決 Exact T+1 lag（領先 SAT_LEAD enter ≥1 日）· Soft-Frozen KEEP · paper only
```

Label: `FIN_SAT_FFT_PHASE_LAG_STAGEA_CHARTER_2026-09-28__DONE_FFT_LAG_NO_EDGE__NO_LIVE_WIRE`

## Why

0k9j 證明 trail 有譜峰，但**功率譜／非因果 bandpass** 不解 lag。  
Belief: 對 85/128/256td 帶做 **因果 STFT 相位／瞬時頻／端點重建**，或可領先 enter。  
Risk: 窗長本身引入 lag，相位對 enter IC≈0；或 probe 仍 tipCAGR−。

## Diagnosis（預註冊）

- Carrier: `trail_rel_63`（0k9j 有色載體；daily rel≈白噪不試為主）
- Causal rolling FFT win ∈ {64,128,256} · bands 對齊 0k9j periods ±30%
- 對 `enter`（SAT_LEAD 起點）lead k=1..5：phase / dphase / recon / amp 的 IC
- 對照：`trail_rel_63` 本身 lag-1 IC（0k9o）

## Books

| ID | fam | 規則 |
|---|---|---|
| `CTRL_LIVE_A10` | ctrl | live |
| `REF_SAT` / `REF_COMP` | ref | always |
| `UB_ENTER_M1` | ub | 早 1 日 oracle（0k9o 對照） |
| `R_SAT_LEAD_L1` | switch | baseline lag-1 狀態 |
| `R_PHASE_QUAD_L1` | switch | 因果相位落在預註冊危險象限 ∧ recon_l1<0 |
| `R_DPHASE_HI_L1` | switch | \|dphase\|_l1 高分位 ∧ trail_l1<0 |
| `R_RECON_HALF_L1` | switch | 因果 band 重建 ≤ −0.005 |
| `R_AMP_TREND_L1` | switch | amp 上升 ∧ recon_l1<0 |

## Gates / Verdicts

HIT = tip-clean + held≥+0.10 + vsSAT+0.05（switch only）。  
`FFT_LAG_HIT` / `FFT_LAG_SIGNAL` / `FFT_LAG_NO_EDGE` / `TIP_LAG_BLOCK` / `TIP_MDD_ONLY`

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_fft_phase_lag_stagea.py
```

Register: **0k9p**
