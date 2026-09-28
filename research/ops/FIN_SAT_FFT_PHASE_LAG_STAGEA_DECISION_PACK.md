# FIN_SAT_FFT_PHASE_LAG_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:39:34Z`
Status: **FFT_LAG_NO_EDGE** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_FFT_PHASE_LAG_STAGEA_CHARTER.md`
Screen: `FIN_SAT_FFT_PHASE_LAG_STAGEA_SCREEN.md`
Parents: 0k9o/0k9j/0k9n · register **0k9p**

## Verdict

**`FFT_LAG_NO_EDGE`**

## Reading

- best FFT lead IC: {"feat": "w64_phase", "k": 1, "ic": -0.0898, "abs_ic": 0.0898, "win": 64}
- trail_rel lag-1 |IC| vs enter: `0.1005`
- enters=77

UB shaped:
- `UB_ENTER_M1` held↑ 3.4426 tipY↑ 1.7875

No causal FFT_LAG_HIT.

## Books

- `REF_SAT_RELAX` (ref) · %SAT=100.0 · held↑ 0.3343 tipY↑ 0.6801 · tipClean=True
- `REF_COMP_H150_A20` (ref) · %SAT=0.0 · held↑ 0.5415 tipY↑ -13.3591 · tipClean=False
- `UB_ENTER_M1` (ub) · %SAT=26.45 · held↑ 3.4426 tipY↑ 1.7875 · tipClean=True
- `R_SAT_LEAD_L1` (switch) · %SAT=24.13 · held↑ 1.2962 tipY↑ -8.4925 · tipClean=False
- `R_PHASE_QUAD_L1` (switch) · %SAT=48.92 · held↑ 1.105 tipY↑ -7.0231 · tipClean=False
- `R_DPHASE_HI_L1` (switch) · %SAT=23.48 · held↑ 2.0412 tipY↑ -1.7041 · tipClean=False
- `R_RECON_HALF_L1` (switch) · %SAT=30.55 · held↑ 1.0299 tipY↑ -7.1779 · tipClean=False
- `R_AMP_TREND_L1` (switch) · %SAT=24.64 · held↑ 0.7382 tipY↑ -10.788 · tipClean=False

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Causal FFT window cannot invent lead beyond carrier; do not expand spectrum grid after peek
4. UB diagnosis only · no observe · no live

Label: `FIN_SAT_FFT_PHASE_LAG_STAGEA_DECISION_PACK_2026-09-28__FFT_LAG_NO_EDGE__NO_LIVE`
