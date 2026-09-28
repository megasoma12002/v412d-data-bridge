# FIN_SAT_TIP_LEAD_DECISION_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:30:48Z`
Status: **TIP_LAG_BLOCK** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_CHARTER.md`
Screen: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN.md`
Parents: 0k9n · register **0k9o**

## Verdict

**`TIP_LAG_BLOCK`**

## Reading

- enters=**77** tip_enters=**8** · lead_signal=`True`（弱）
- top IC: `trail_rel_63` k=1..5 |IC|≈**0.10**（接近 θ 的定義性接近，非強外部 lead）· 次佳 `zz08_bear` k=2 IC **0.037**
- pre-enter Δ: zz08_bear **+0.09** · crisis/SELL **無上升**（進入前危機／賣壓不提前抬升）

UB shaped:
- `UB_STATE_SD` held↑ 3.4758 tipY↑ 2.7325
- `UB_ENTER_M1` held↑ 3.4426 tipY↑ 1.7875

No causal LEAD_HIT.

**精煉／決策點地圖：**
1. **結構決策點** — 只要比同日狀態 **早 1 日** 進 SAT（`UB_ENTER_M1`），即可 tip-clean+held。問題不是「切不切」，是「能不能早一天知道」。
2. **外部 lead 不足** — 既有特徵對 **enter 事件** IC 偏弱；Crisis/SELL 是 SAT_LEAD **狀態內** 差異（0k9l），不是 **進入前** 預警。
3. **最佳因果近似** — `R_CONF_EARLY_L1` tipY **−3.6**（優於 L1 −8.5）仍未 tip-clean；半閾／斜率提早無效。
4. **可繼續的窄路徑** — (a) 只校準 CONF 進場時序（不擴表）；(b) 接受 Exact T+1 下 tip-clean≈近純 SAT 並另修 held MDD；(c) 停在 paper map。**不開新特徵掃描。**

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

Label: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_DECISION_PACK_2026-09-28__TIP_LAG_BLOCK__NO_LIVE`
