# FIN_SAT_TIPGAP_PRED_STAGEA_DECISION_PACK

Date: 2026-09-28 · Generated `2026-09-28T13:31:00Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**

Charter: `FIN_SAT_TIPGAP_PRED_STAGEA_CHARTER.md`
Screen: `FIN_SAT_TIPGAP_PRED_STAGEA_SCREEN.md`
Parents: 0k9h cycle TIP_MDD_ONLY · register **0k9i**

## Verdict

**`TIP_MDD_ONLY`**

## What gap to predict

Binding gap = **tip CAGR drag timing** (when COMP HARD lags SAT), not held lift / not calendar year.

- Best leading feat: `r0050_63_l1` IC=-0.1094
- IC-gated feats: ['r0050_63_l1', 'zz08_bear_l1']
- Tip1y−held: `{"trail_rel_63": -0.013667, "comp_sells_21": 1.861838, "vol0050_21": 0.004554, "crisis": 0.043267, "zz08_bear": 0.051094, "pct_trail_drag": 24.13}`
- Tip-drag cycle overlap: `{"tip_drag_base_rate": 69.42, "n_tip": 242, "crisis": {"n": 48, "drag_rate": 100.0, "lift_pp": 30.58}, "bearcrisis": {"n": 48, "drag_rate": 100.0, "lift_pp": 30.58}, "zz08_bear": {"n": 53, "drag_rate": 60.38, "lift_pp": -9.04}, "zz12_bear": {"n": 11, "drag_rate": 100.0, "lift_pp": 30.58}, "sells21_hi": {"n": 114, "drag_rate": 87.72, "lift_pp": 18.3}, "rel63_neg": {"n": 168, "drag_rate": 100.0, "lift_pp": 30.58}}`

IC-gated features exist but probes did not clear tip-clean HIT — next charter should build **cycle around these feats**, not re-scan.

**Reading — 要預測的缺口：**
1. Binding = **tip-drag 時點**（COMP HARD 落後 SAT），不是 held、不是年切。
2. **領先（因果）**：`r0050_63_l1` IC=−0.11（0050 近 63 日偏強 → 未來 21 日 COMP 相對落後）· `zz08_bear_l1` IC=−0.09。  
3. **同期（tip 窗口）**：Crisis／高 COMP SELL 與 trail-drag 重疊極高（drag_rate 100%／88% · lift +19～31pp）——偏 **確認／狀態**，領先 IC 未過 gate。  
4. **反例**：tip 內 `zz08_bear` 的 drag lift 為 **負**（−9pp）——峰谷 bear 半週期與 tip-drag **不同步**，解釋 0k9h ZigZag 傷 tip。  
5. Probe `PRB_R0050_63` held↑+1.09 仍 tipCAGR−；特徵找對方向但單門檻切換不夠修 tip。

下一輪應圍繞 **0050 動能衰竭／過熱後切 SAT** + **Crisis／SELL 密集確認** 組週期，禁止再掃特徵表。

## Binding

1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP
2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**
3. Do not calendar-year switch · do not expand feature table after this scan
4. Even GAP_PRED_HIT → observe ballot DRAFT only · no live

Label: `FIN_SAT_TIPGAP_PRED_STAGEA_DECISION_PACK_2026-09-28__TIP_MDD_ONLY__NO_LIVE`
