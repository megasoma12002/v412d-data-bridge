# FIN_SAT_FFT_PHASE_LAG_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T14:39:34Z`
Status: **FFT_LAG_NO_EDGE** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

## FFT-phase lead vs enter

- best_fft=`{'feat': 'w64_phase', 'k': 1, 'ic': -0.0898, 'abs_ic': 0.0898, 'win': 64}`
- trail_abs_ic_k1=`0.1005`

| feat | win | k | IC |
|---|---:|---:|---:|
| w64_phase | 64 | 1 | -0.0898 |
| w64_phase | 64 | 2 | -0.0753 |
| w64_phase | 64 | 3 | -0.0716 |
| w64_dphase | 64 | 3 | 0.0686 |
| w64_dphase | 64 | 2 | 0.0679 |
| w64_dphase | 64 | 1 | 0.065 |
| w64_dphase | 64 | 5 | 0.0578 |
| w64_phase | 64 | 5 | -0.0553 |
| w256_phase | 256 | 5 | -0.0513 |
| w256_phase | 256 | 1 | -0.0501 |

## Books

| ID | fam | %SAT | heldCAGR↑ | tipCAGR↑ | tipClean | mark |
|---|---|---:|---:|---:|---|---|
| CTRL_LIVE_A10 | ctrl | 0.0 | -0.0 | 0.0 | True | · |
| REF_SAT_RELAX | ref | 100.0 | 0.3343 | 0.6801 | True | · |
| REF_COMP_H150_A20 | ref | 0.0 | 0.5415 | -13.3591 | False | · |
| UB_ENTER_M1 | ub | 26.45 | 3.4426 | 1.7875 | True | UB |
| R_SAT_LEAD_L1 | switch | 24.13 | 1.2962 | -8.4925 | False | · |
| R_PHASE_QUAD_L1 | switch | 48.92 | 1.105 | -7.0231 | False | · |
| R_DPHASE_HI_L1 | switch | 23.48 | 2.0412 | -1.7041 | False | · |
| R_RECON_HALF_L1 | switch | 30.55 | 1.0299 | -7.1779 | False | · |
| R_AMP_TREND_L1 | switch | 24.64 | 0.7382 | -10.788 | False | · |

Verdict: **`FFT_LAG_NO_EDGE`**

Label: `FIN_SAT_FFT_PHASE_LAG_STAGEA_SCREEN_2026-09-28__FFT_LAG_NO_EDGE`
