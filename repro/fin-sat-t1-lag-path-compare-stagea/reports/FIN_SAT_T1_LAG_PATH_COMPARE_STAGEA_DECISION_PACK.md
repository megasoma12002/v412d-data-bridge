# FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:49:23Z`
Status: **T0_ONLY_EDGE** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_CHARTER.md`
Screen: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_SCREEN.md`
Parents: 0k9n/0k9o/0k9p · register **0k9q**

## Verdict

**`T0_ONLY_EDGE`**

## Reading

- Soft-Frozen best score: `P2_SAT_PURE` score=2.2002 · held↑ 0.3343 tipY↑ 0.6801 · tipClean=True
- Soft-Frozen best tip-clean: `P2_SAT_PURE` tipY↑ 0.6801 · held↑ 0.3343 heldMDD -0.3084
- Soft-Frozen best held CAGR: `R_SAT_LEAD_L1` held↑ 1.2962 · tipY↑ -8.4925
T+0 counterfactual shaped:
- `P3_T0_STATE` held↑ 3.4758 tipY↑ 2.7325
- `P3_T0_ENTER_M1` held↑ 3.4426 tipY↑ 1.7875

No Soft-Frozen PATH_HIT.

**路徑比較結論：**

| 路徑 | Soft-Frozen 回測 | 評語 |
|---|---|---|
| **1 停切換** | LIVE tip 平、無 held↑；COMP held↑+0.54 但 tipY **−13** | 可當「不動作」下限，不是優勝 |
| **2 tip≈SAT** | **SF 分數第 1** · tip-clean · held MDD **−0.31 不過** | Soft-Frozen 下 **相對最優**（先保 tip） |
| **3 放寬 T+0** | **唯一 HIT 形狀** held↑+3.5 tipY↑+2.7 | 回測最好，但 **需改 Exact T+1**（反事實） |
| **4 換機制（配資／半倉）** | held↑~+0.9–1.3 仍 tipY **−6～−11** | 未優於二元 lag-1；**不解 tip** |

**建議（Soft-Frozen KEEP）：** 選 **路徑 2** 作為 tip 線（SAT observe／near-pure SAT），路徑 1 的 COMP 作 held 線分開看；**不要**指望路徑 4 修 tip；路徑 3 僅在人裁改 T+0 時才優。

## All books

- `P1_STOP_LIVE` path=1_stop sf=True score=1.0 · held↑ -0.0 tipY↑ 0.0 · tipClean=True shaped=False
- `P1_STOP_COMP` path=1_stop sf=True score=-6.0129 · held↑ 0.5415 tipY↑ -13.3591 · tipClean=False shaped=False
- `P2_SAT_PURE` path=2_sat sf=True score=2.2002 · held↑ 0.3343 tipY↑ 0.6801 · tipClean=True shaped=False
- `P3_T0_STATE` path=3_t0 sf=False score=8.6243 · held↑ 3.4758 tipY↑ 2.7325 · tipClean=True shaped=True
- `P3_T0_ENTER_M1` path=3_t0 sf=False score=7.1736 · held↑ 3.4426 tipY↑ 1.7875 · tipClean=True shaped=True
- `P4_BLEND_TRAIL` path=4_mech sf=True score=-5.173 · held↑ 1.2948 tipY↑ -6.1442 · tipClean=False shaped=False
- `P4_SCALE50_L1` path=4_mech sf=True score=-5.5252 · held↑ 0.925 tipY↑ -10.9176 · tipClean=False shaped=False
- `R_SAT_LEAD_L1` path=ref_switch sf=True score=-5.154 · held↑ 1.2962 tipY↑ -8.4925 · tipClean=False shaped=False

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. T+0 paths are counterfactual only · not observe · not live without policy change
4. Do not expand path grid after peek

Label: `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK_2026-09-28__T0_ONLY_EDGE__NO_LIVE`
