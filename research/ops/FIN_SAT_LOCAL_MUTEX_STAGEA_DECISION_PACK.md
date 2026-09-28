# FIN_SAT_LOCAL_MUTEX_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:18:26Z`
Status: **TIP_LAG_BLOCK** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_LOCAL_MUTEX_STAGEA_CHARTER.md`
Screen: `FIN_SAT_LOCAL_MUTEX_STAGEA_SCREEN.md`
Parents: 0k9m/0k9l · register **0k9n**

## Verdict

**`TIP_LAG_BLOCK`**

## Reading

- local_mutex_diag=`True` score=`0.6162`
- tip SAT_LEAD 56.61% vs pre 18.73% · tip COMP_LEAD only 8.26%
- tip sum_rel ALL=-0.071071 · from SAT_LEAD=-0.076438 (frac 1.0755)
- held sum_rel COMP_LEAD=0.203611 · SAT_LEAD=-0.183915

UB shaped (non-causal):
- `UB_STATE_SD` held↑ 3.4758 tipY↑ 2.7325 %SAT 24.16
- `UB_TIPWIN_SAT` held↑ 1.632 tipY↑ 0.6801 %SAT 7.19

No causal switch HIT.

**精煉：**
1. **是局部互斥，不是全局同日對撞** — tip 窗幾乎全是 SAT_LEAD 損害（frac≈1.08）；held 優勢在 tip 外 COMP_LEAD（+0.20）；tip 內 COMP_LEAD 僅 8.3%；`P(COMP_LEAD∧drag)=0`。
2. **結構上可同時 tip-clean+held** — `UB_TIPWIN_SAT`（僅 tip 日曆 ~7% 切 SAT）held↑+1.63 tipY↑+0.68；`UB_STATE_SD`（同日狀態）held↑+3.48 tipY↑+2.73。
3. **Binding = Exact T+1 lag** — 同日 oracle 形狀 HIT；lag-1（`R_SAT_LEAD_L1`／`R_DRAG_L1`／tiplike）全 tipCAGR−。0k9e–0k9m 的「全局互斥」表象，主因是因果延遲錯過 tip 局部，而非日日要兩本書。
4. **下一步若再開**：需領先於 trail 狀態的 tip-local 預警（非再擴 day-switch 格）；或接受 Soft-Frozen Exact T+1 下 tip-clean 近純 SAT。UB／日曆不可上 observe／live。

## Books

- `REF_SAT_RELAX` (ref) · %SAT=100.0 · held↑ 0.3343 tipY↑ 0.6801 · tipClean=True shaped=False
- `REF_COMP_H150_A20` (ref) · %SAT=0.0 · held↑ 0.5415 tipY↑ -13.3591 · tipClean=False shaped=False
- `UB_TIPWIN_SAT` (ub) · %SAT=7.19 · held↑ 1.632 tipY↑ 0.6801 · tipClean=True shaped=True
- `UB_STATE_SD` (ub) · %SAT=24.16 · held↑ 3.4758 tipY↑ 2.7325 · tipClean=True shaped=True
- `R_SAT_LEAD_L1` (switch) · %SAT=24.13 · held↑ 1.2962 tipY↑ -8.4925 · tipClean=False shaped=False
- `R_DRAG_L1` (switch) · %SAT=47.22 · held↑ 1.1905 tipY↑ -5.1372 · tipClean=False shaped=False
- `R_TIPLIKE_L1` (switch) · %SAT=18.54 · held↑ 0.3413 tipY↑ -10.2087 · tipClean=False shaped=False
- `R_PRE_COMP_TIP_SAT_L1` (switch) · %SAT=44.96 · held↑ -0.0905 tipY↑ -2.7973 · tipClean=False shaped=False

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not expand feature table or rule grid after peek
4. UB is diagnosis only · not observe · not live

Label: `FIN_SAT_LOCAL_MUTEX_STAGEA_DECISION_PACK_2026-09-28__TIP_LAG_BLOCK__NO_LIVE`
