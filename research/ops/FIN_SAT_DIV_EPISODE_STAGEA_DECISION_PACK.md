# FIN_SAT_DIV_EPISODE_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T14:02:05Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_DIV_EPISODE_STAGEA_CHARTER.md`
Screen: `FIN_SAT_DIV_EPISODE_STAGEA_SCREEN.md`
Parents: 0k9i tip-gap · register **0k9l**

## Verdict

**`TIP_MDD_ONLY`**

## Reading

- Primary θ=0.01: SAT_LEAD 21.69% · COMP_LEAD 24.01% · SIMILAR 54.29%
- SAT_LEAD − SIMILAR: `{"crisis": 0.16529, "bearcrisis": 0.209503, "r0050_63": -0.014226, "mdd0050_63": -0.015563, "vol0050_21": 0.001252, "comp_sells_21": 6.754526, "zz08_bear": -0.001151}`
- SAT_LEAD − COMP_LEAD: `{"crisis": 0.112516, "bearcrisis": 0.117208, "r0050_63": 0.009671, "mdd0050_63": -0.001356, "vol0050_21": 0.001747, "comp_sells_21": 9.096223, "zz08_bear": 0.079818}`
- Top IC: `[{"feat": "crisis_l1", "ic": 0.1853, "abs_ic": 0.1853, "sign_hit": 0.7625, "sat_when_high": true, "ic_gate": true, "n": 3364, "base_sat_rate": 0.217}, {"feat": "bearcrisis_l1", "ic": 0.1734, "abs_ic": 0.1734, "sign_hit": 0.7087, "sat_when_high": true, "ic_gate": true, "n": 3364, "base_sat_rate": 0.217}, {"feat": "comp_sells_21_l1", "ic": 0.1382, "abs_ic": 0.1382, "sign_hit": 0.566, "sat_when_high": true, "ic_gate": true, "n": 3364, "base_sat_rate": 0.217}]`

相似段佔多數時，全日平均／傅立葉被稀釋；互斥特徵應在 **SAT_LEAD episode** 內讀。

**精煉：**
1. **SIMILAR ~54%** → 證實「多數時候特徵相近」；全日 FFT 被這段稀釋。
2. **SAT_LEAD 內不同處**：Crisis／BearCrisis 明顯升高（+0.17／+0.21 vs SIMILAR）；COMP SELL21 **+6.8**；與 COMP_LEAD 比 SELL 差更大（+9.1）。
3. **預測 SAT_LEAD**：`crisis_l1` IC **0.19** · hit **76%**（遠強於 0k9i 對連續 fwd_rel 的 IC）——任務改成「預測分歧狀態」比「預測連續相對報酬」更乾淨。
4. Probe `PRB_STATE_SAT_LEAD` held↑+1.70 仍 tipCAGR− → 標籤／特徵對了，**進場規則仍不夠修 tip**。

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not expand feature table · no year-switch
4. Next cycle rules should trigger on divergence-entry features, not full-sample averages

Label: `FIN_SAT_DIV_EPISODE_STAGEA_DECISION_PACK_2026-09-28__TIP_MDD_ONLY__NO_LIVE`
