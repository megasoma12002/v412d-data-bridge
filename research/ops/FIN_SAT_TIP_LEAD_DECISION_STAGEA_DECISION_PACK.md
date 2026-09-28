# FIN_SAT_TIP_LEAD_DECISION_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:29:12Z`
Status: **LEAD_SIGNAL** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_CHARTER.md`
Screen: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN.md`
Parents: 0k9n · register **0k9o**

## Verdict

**`LEAD_SIGNAL`**

## Reading

- enters=813 tip_enters=137 · lead_signal=`True`
- top IC: [{"feat": "trail_rel_63", "k": 1, "ic": -0.7273, "abs_ic": 0.7273, "enter_rate_selected": 0.4909, "base_enter_rate": 0.2416, "lift": 2.032}, {"feat": "trail_rel_63", "k": 2, "ic": -0.7147, "abs_ic": 0.7147, "enter_rate_selected": 0.4885, "base_enter_rate": 0.2416, "lift": 2.022}, {"feat": "trail_rel_63", "k": 3, "ic": -0.7004, "abs_ic": 0.7004, "enter_rate_selected": 0.4851, "base_enter_rate": 0.2416, "lift": 2.008}, {"feat": "trail_rel_63", "k": 5, "ic": -0.6805, "abs_ic": 0.6805, "enter_rate_selected": 0.4818, "base_enter_rate": 0.2416, "lift": 1.994}, {"feat": "comp_sells_21", "k": 5, "ic": 0.1784, "abs_ic": 0.1784, "enter_rate_selected": 0.3032, "base_enter_rate": 0.2416, "lift": 1.255}]
- pre-enter Δ: [{"feat": "comp_sells_21", "pre_enter_mean": 24.202214, "base_mean": 19.158098, "delta": 5.044116}, {"feat": "bearcrisis", "pre_enter_mean": 0.355474, "base_mean": 0.23893, "delta": 0.116543}, {"feat": "crisis", "pre_enter_mean": 0.219926, "base_mean": 0.125706, "delta": 0.09422}, {"feat": "zz08_bear", "pre_enter_mean": 0.214268, "base_mean": 0.180089, "delta": 0.034179}]

UB shaped:
- `UB_STATE_SD` held↑ 3.4758 tipY↑ 2.7325
- `UB_ENTER_M1` held↑ 3.4426 tipY↑ 1.7875

No causal LEAD_HIT.

## Books

- `REF_SAT_RELAX` (ref) · %SAT=100.0 · held↑ 0.3343 tipY↑ 0.6801 · tipClean=True shaped=False
- `REF_COMP_H150_A20` (ref) · %SAT=0.0 · held↑ 0.5415 tipY↑ -13.3591 · tipClean=False shaped=False
- `UB_ENTER_M1` (ub) · %SAT=26.45 · held↑ 3.4426 tipY↑ 1.7875 · tipClean=True shaped=True
- `UB_STATE_SD` (ub) · %SAT=24.16 · held↑ 3.4758 tipY↑ 2.7325 · tipClean=True shaped=True
- `R_SAT_LEAD_L1` (switch) · %SAT=24.13 · held↑ 1.2962 tipY↑ -8.4925 · tipClean=False shaped=False
- `R_HALF_THETA_L1` (switch) · %SAT=34.86 · held↑ 1.4528 tipY↑ -5.9029 · tipClean=False shaped=False
- `R_SLOPE_EARLY_L1` (switch) · %SAT=17.89 · held↑ 0.8112 tipY↑ -6.1698 · tipClean=False shaped=False
- `R_CONF_EARLY_L1` (switch) · %SAT=35.57 · held↑ 2.0233 tipY↑ -3.636 · tipClean=False shaped=False
- `R_LEAD_OR_STATE_L1` (switch) · %SAT=24.78 · held↑ 1.3752 tipY↑ -8.4925 · tipClean=False shaped=False

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not expand feature table after peek
4. UB diagnosis only · no observe · no live

Label: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_DECISION_PACK_2026-09-28__LEAD_SIGNAL__NO_LIVE`
