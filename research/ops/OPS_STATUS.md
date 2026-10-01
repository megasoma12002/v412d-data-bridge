# Ops Status — One-Page Map

Date: 2026-09-29 (tip catch-up CONFIRMED · Path3 dual-paper/signal/ledger refreshed)  
Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
Live Soft-Frozen clips: **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]** (β densify ACCEPT 2026-09-25; was FINBAND F[0.60,0.90] E[0.00,0.35])  
Soft-Frozen `REBALANCE_L1_MIN`: **0.05** (ACCEPT 2026-09-27)  
**Tip calendar:** live + COMPOSITE/SAT/P3 signal/ledger tip **`2026-09-29`** · holiday gap 9/25–28 · evidence `TIP_CATCHUP_2026-09-29.md` · checklist `TIP_CATCHUP_2026-09-29_CHECKLIST.md`  
**Cutover `#257`: CLOSED** (not merged) · `ACCEPT_CLOSE_CUTOVER_BUNDLE_257.md` · live KEEP 公股+FUSE · DH later **replaced by COOL_c8** 2026-09-25 · reopen only new mechanism or sealed-gate  
**Deferred ops ACCEPT:** `ACCEPT_DEFERRED_OPS_HARDEN_2026-09-25.md` · broker PREP `ACCEPT_PREP_BROKER_LIVE_WRITE_2026-09-25.md` · Stage-E sandbox `ACCEPT_RESEARCH_STAGE_E_FULL_HISTORY_SANDBOX_2026-09-25.md`  
**Eng tip-path P0–P2:** merged `#314` · Soft-Frozen KEEP  
**Broker/R5/OCO PREP not open:** merged `#315` · `BROKER_R5_OCO_PREP_NOT_OPEN.md` · UAT readonly checklist `YUANTA_SPARK_UAT_READONLY_CHECKLIST.md`  
**SAT_A20_H5:** Stage A MECH_HIT · Stage B PARENT_KEEP · **OBSERVE CLOSED** (2026-09-28 · superseded by COMPOSITE) · `COMPOSITE_OBSERVE_OPEN_PARENTS_CLOSE_2026-09-28.md`  
FIN 賣側新機制（timing/confirm · 非 MA-dampen）：Stage A **`MDD_BLOCK`** · WR↑仍傷 MDD/tip · SELL_a75 KEEP · no observe · no live · `FIN_SELL_NEW_MECH_STAGEA_DECISION_PACK.md`
FIN 浮虧延後賣（等回本）：**Stage A `COOL_GATE_REQUIRED`** · gated defer no lift · NOCOOLGATE proves gate needed · `FIN_LOSS_DEFER_SELL_STAGEA_DECISION_PACK.md` · no live  
FIN 買側品質：**OBSERVE CLOSED** (superseded by both-quality HARD150) · batch `OBSERVE_UP_DOWN_BATCH_2026-09-28.md` · Soft-Frozen KEEP · no live  
FIN 賣側品質：Stage A `MDD_BLOCK` → Stage B **`NO_EDGE`** · soft-dampen 護 MDD 失 CAGR · SELL_a75 KEEP · no observe · no live · `FIN_SELL_QUALITY_STAGEB_DECISION_PACK.md`  
FIN 買賣側聯優：Stage B `BOTH_QUALITY_HIT` · **OBSERVE CLOSED** (2026-09-28 · superseded by COMPOSITE) · `COMPOSITE_OBSERVE_OPEN_PARENTS_CLOSE_2026-09-28.md`  
**Observe UP/DOWN batch 2026-09-28:** `OBSERVE_UP_DOWN_BATCH_2026-09-28.md` — OPEN both-quality+SAT_A20; CLOSE soft/sleeve/fuse/priv/within-sleeve/BLEND025/FIN50/E45 paper observes (live stack KEEP)
**ABC Stage A next (2026-09-28):** A `LOCK_KEEP_NO_TIP_LIFT` · B `NO_EDGE` · C `MONITOR_READY` · `ABC_STAGEA_NEXT_BATCH_2026-09-28.md` · Soft-Frozen KEEP · no live  
ETF **0050 買賣品質** Stage A：**`TIP_BLOCK`** · best sell `SELL_COOL_DEFEND` CAGR↑+0.16 但 tip MDD↓ · clip/`SELL_a75` KEEP · no live · `ETF0050_BOTH_QUALITY_STAGEA_DECISION_PACK.md`  
ETF **0050 軟縮放 × 高低點／DD** Stage A：**`TIP_BLOCK`** · best `EXT_SELL_HIGH20` CAGR↑+0.16 tip↓ · Soft-Frozen KEEP · no live · `ETF0050_SOFT_EXTREME_STAGEA_DECISION_PACK.md`  
ETF **0050 regime × 多空偵測器** Stage A：**`NO_EDGE`** · best `DET_BUY_MA60_UP` CAGR↑+0.13 tip↓ · Soft-Frozen KEEP · no live · `ETF0050_REGIME_DETECTOR_STAGEA_DECISION_PACK.md`  
**FIN×SAT COMPOSITE (2026-09-28):** Stage A **`COMPOSITE_HIT`** · **OBSERVE OPEN** `COMP_H150_x_A20` · parents CLOSED · Soft-Frozen KEEP · live CONF α=0.10 KEEP · cutover **BLOCKED** · no live · `FIN_SAT_COMPOSITE_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
**FIN×SAT tip-CAGR repair (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · HARD150 tip CAGR− · SAT tip-clean/held short · COMPOSITE observe KEEP · no live · `FIN_SAT_TIP_CAGR_STAGEA_DECISION_PACK.md`  
**FIN×SAT tip new-mech (2026-09-28):** Stage A **`SAT_RELAX_HIT`** · **OBSERVE OPEN** `SAT_A20_RELAX` · COMPOSITE observe KEEP · Soft-Frozen KEEP · live CONF α=0.10 KEEP · cutover **BLOCKED** · no live · `SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
**FIN×SAT 配資混合 (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · COMP×SAT daily blend C25…C75 · tip CAGR− whenever w_COMP≥0.25 · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_BLEND_STAGEA_DECISION_PACK.md`  
**FIN×SAT 切換機制 (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · lag-1 COMP↔SAT · short REL tip CAGR− · REL126 tip-clean/held MDD fail · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_SWITCH_STAGEA_DECISION_PACK.md`  
**FIN×SAT 互斥特徵→切換 (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · year mutex Bull↔Crisis real · oracle year upper-bound tip-clean · pre-reg switches tip CAGR− · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_MUTEX_FEAT_STAGEA_DECISION_PACK.md`  
**FIN×SAT 週期互斥切換 (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · not year-switch · ZigZag/K5/month-qtr · episode Bull≠COMP-stable · ZZ08 held↑ tipCAGR− · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_CYCLE_SWITCH_STAGEA_DECISION_PACK.md`  
**FIN×SAT tip-gap 預測／特徵 (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · gap=tip-drag timing · lead `r0050_63` IC−0.11 · tip Crisis/SELL overlap · zz08 tip-desync · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_TIPGAP_PRED_STAGEA_DECISION_PACK.md`  
**FIN×SAT tip-gap FFT (2026-09-28):** Stage A **`FFT_SIGNAL`** · daily rel≈white · trail ~85/128/256td + bandpass IC · assist≠replace 0k9i · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_TIPGAP_FFT_STAGEA_DECISION_PACK.md`  
**FIN×SAT tip-gap 小波／拉普拉斯 (2026-09-28):** Stage A **`WAVE_LAP_SIGNAL`** · CWT trail ~200–234td · tip ~107–115td · Laplace σ≈0 @115/231td · assist≠replace 0k9i · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_DECISION_PACK.md`  
**FIN×SAT 分歧 Episode (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · SAT_LEAD vs SIMILAR: Crisis/SELL↑ · crisis→SAT_LEAD IC 0.19 hit76% · SIMILAR~54% dilutes spectra · probes tip CAGR− · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_DIV_EPISODE_STAGEA_DECISION_PACK.md`  
**FIN×SAT 分歧切換規則 (2026-09-28):** Stage A **`TIP_MDD_ONLY`** · enter/confirm/exit 6 switch 全 tipCAGR− · best `R_DIV_ONLY` held+1.30 tipY−8.5 · rule-layer day-switch exhausted · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_DIV_RULE_STAGEA_DECISION_PACK.md`  
**FIN×SAT 局部互斥 (2026-09-28):** Stage A **`TIP_LAG_BLOCK`** · tip/held 時段分離（score0.62）· UB tip-clean+held · Exact T+1 lag-1 擋 HIT · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_LOCAL_MUTEX_STAGEA_DECISION_PACK.md`  
**FIN×SAT tip-lead 決策點 (2026-09-28):** Stage A **`TIP_LAG_BLOCK`** · enter lead 外部弱 · UB_ENTER_M1 tip-clean+held · CONF_EARLY tipY−3.6 未 clean · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_TIP_LEAD_DECISION_STAGEA_DECISION_PACK.md`  
**FIN×SAT FFT-phase × T+1 lag (2026-09-28):** Stage A **`FFT_LAG_NO_EDGE`** · causal phase IC0.09 < trail0.10 · FFT 無法補 Exact T+1 · parents KEEP · Soft-Frozen KEEP · no observe · no live · `FIN_SAT_FFT_PHASE_LAG_STAGEA_DECISION_PACK.md`  
**FIN×SAT T+1 lag 路徑比較 (2026-09-28):** Stage A **`T0_ONLY_EDGE`** · SF 最優 `P2_SAT_PURE` · 唯一 HIT 形狀是 T+0 反事實 · path4 不解 tip · parents KEEP · Soft-Frozen KEEP · no live · `FIN_SAT_T1_LAG_PATH_COMPARE_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 T+0 carve-out (2026-09-28):** **EXECUTED ACCEPT** `T0_CARVE_FIN_SAT_SWITCH` · **OBSERVE OPEN** `P3_T0_STATE` · dual-paper OPERATING · sealed MDD −0.17pp human **ACCEPTABLE** (abs sealed≪full/held) · COMPOSITE+SAT_RELAX KEEP · Soft-Frozen clips KEEP · cutover **BLOCKED** · no live · `FIN_SAT_PATH3_T0_SEALED_MDD_DISPOSITION.md`  
**FIN×SAT Path3 T0×T1 hybrid (2026-09-28):** Stage A **`T0_SAMEBAR_ONLY`** · hybrid T1-fill tipY↑ **−8.49** · ≡ `R_SAT_LEAD_L1` · same-bar observe tip gap +11.2pp · Path3 observe KEEP · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_T0_T1_HYBRID_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 live T+0 机制 (2026-09-29):** Stage A **`ORACLE_ONLY`** · MOC F25/50/75 tipY仍−（best F50 −4.71）· live Exact T+1 guards binding · Path3 observe KEEP · Soft-Frozen／全局 T+1 KEEP · no fill-core edit · no live · `FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 live T+0 fill PREP (2026-09-29):** **SUPERSEDED by 0ka7** · fill flag **ON** · Soft-Frozen Exact T+1 KEEP elsewhere · broker false · `FIN_SAT_PATH3_OBSERVE_THETA005_T0_LIVE_BALLOT_EXECUTED_ACCEPT.md`  
**FIN×SAT Path3 T0 fill-carve simulate (2026-09-29):** Stage A **`FILL_CARVE_CLOSE_ONLY`** · evidence parent for 0ka7 · Soft-Frozen KEEP · `FIN_SAT_PATH3_T0_FILL_SIM_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 T0 switch emitter PREP (2026-09-29):** **SUPERSEDED by 0ka7** · emit flag **ON** · weight **0kab ledger** · mute **0kaa** · Soft KEEP · broker false · `LIVE_PATH3_T0_SWITCH_EMITTER_PREP.md`  
**FIN×SAT Path3 2022 flip 落點 (2026-09-29):** Stage A **`COMP_STAY_MISS`** · 2022 P3−BASE −0.75 · 主因錯站 COMP（3月／夏秋）· May–Jun whipsaw 非主因（窗內 +1.04）· Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_2022_FLIP_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 COMP confirm／min-stay (2026-09-29):** Stage A **`COMP_CONFIRM_NO_EDGE`** · confirm/minstay 修不了 2022（最佳 −0.74≈原 −0.75）且 D≥2 傷 tip · Path3 observe KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 COMP-entry signal (2026-09-29):** Stage A **`SIGNAL_WEAK`** · best `rel_5` IC0.17 hit0.59 · OOF IC≈0 不穩 · `BLOCK_rel_5` 修2022(+0.79)但 tipY↓ · Path3 observe KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_DECISION_PACK.md`  

**FIN×SAT Path3 COMP-entry FFT (2026-09-29):** Stage A **`FFT_ENTRY_WEAK`** · best `w256_dphase` IC0.19 hit0.50 · block 傷2022/held/tip · 譜不解進場 · Path3 observe KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_DECISION_PACK.md`  
**FIN×SAT FFT exog×TD AND (2026-09-29):** Stage A **`EXOG_FFT_WEAK`** · `exog_dphase` IC−0.12 hit0.52 · AND 輸 P3 tip/held/2022 · Soft-Frozen KEEP · no live · `FIN_SAT_FFT_EXOG_AND_STAGEA_DECISION_PACK.md`  
**FIN×SAT FFT non-switch tilt (2026-09-29):** Stage A **`FFT_OBSERVE_ONLY`** · soft-tilt 全被 P3 hard 支配 · observe `exog_amp` IC~0.11 · 不當曝險旋鈕 · Soft-Frozen KEEP · no live · `FIN_SAT_FFT_NONSWITCH_TILT_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 θ sweep (2026-09-29):** Stage A **`THETA_HIT`** · challenger θ=**0.005** tipY↑+0.14 held↑+0.30 · θ↑≥0.02 tip垮 · 2022 不敏感 · observe θ=0.01 KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_THETA_SWEEP_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 θ dense down-grid (2026-09-29):** Stage A **`THETA_DOWN_CONFIRM`** · 19-pt ≤1% · 冠軍仍 θ=**0.005**（平台 0.005–0.006）· θ≤0.004 tip塌 · observe θ=0.01 KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_THETA_DOWN_GRID_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 wrong-stay census (2026-09-29):** Stage A **`WRONG_STAY_RECURRENT__THETA_INSENSITIVE`** · θ=0.01 wrong**74** SEVERE_COMP**6** years[2016,2018,2022,2024,2026] · only **2022** year-loss · θ=0.005 SEVERE不減 · observe θ=0.01 KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_WRONG_STAY_CENSUS_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 window pack (2026-09-29):** Stage A **`WINDOW_UNIFORM__THETA005_HELD_EDGE`** · θ=0.01 vs BASE full↑**+3.23** held↑**+3.48** sealed↑**+4.78**/MDD**−0.17** · θ=0.005 full/held再+0.3 · yearly ret W–L **14–1**／MDD W–L **8–7** · observe θ=0.01 KEEP · fill/emit OFF · Soft-Frozen KEEP · no live · `FIN_SAT_PATH3_WINDOW_PACK_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 weight-engine (2026-09-29):** Stage A **`PROXY_WIRED_DEMO_OK`** · `P3_SOFT_SLEEVE_EQ_RECON_PROXY` · demo 6×`-P3T0` + same-bar fill · e21 hook wired · Soft KEEP · broker false · cutover BLOCKED · `FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 weight-engine Stage B (2026-09-29):** **`FULL_ENGINE_BOTH_OK`** · `P3_COMP_SAT_ASOF_RECON_B` · COMP→SAT RELAX KD **6** / SAT→COMP OR_K9×HARD150 **6** `-P3T0` · same-bar fill · Soft KEEP · broker false · cutover BLOCKED · `FIN_SAT_PATH3_WEIGHT_ENGINE_STAGEB_DECISION_PACK.md`  
**Soft↔Path3 flip-day coexistence mute (2026-09-29):** **EXECUTED ACCEPT / LIVE WIRED** · `MUTE_SOFT_FIN_TEL` · `live_soft_path3_coexist_mute=True` · Soft clips/Exact T+1 KEEP elsewhere · broker false · cutover BLOCKED · `LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT_EXECUTED_ACCEPT.md`  
**Path3 COMP/SAT daily share SSOT (2026-09-29):** **EXECUTED ACCEPT / LIVE WIRED** · `live_path3_weight_engine_mode=ledger` · `P3_COMP_SAT_DAILY_POS_LEDGER_A` · Soft KEEP · broker false · cutover BLOCKED · `LIVE_PATH3_WEIGHT_ENGINE_LEDGER_BALLOT_EXECUTED_ACCEPT.md`  
**Path3 strategy cutover (2026-09-29):** Stage A **`CUTOVER_SCOPE_DEFINED`** · `PATH3_STRATEGY_CUTOVER` · default `WITHIN_SLEEVE_PATH3` · Soft clips+0050 KEEP · Soft FIN/TEL Exact T+1 retire candidate · broker false · live flag OFF · next paper `PAPER_WITHIN_HIT` · `FIN_SAT_PATH3_STRATEGY_CUTOVER_STAGEA_DECISION_PACK.md` · checklist `CUTOVER_CHECKLIST_PATH3_STRATEGY.md`  
**Project code review (2026-09-29):** Path3 LIVE WIRED healthy · P1 ledger stale vs tip · ops PREP supersession drift · broker fail-closed KEEP · `PROJECT_CODE_REVIEW_2026-09-29.md`  
**Repo hygiene Batch D (2026-10-01):** untrack ignore-shaped fills/NAV (~30MB) · ARCHIVE 6 closed Stage A trees (~77MB) · KEEP/live/tipsoft untouched · no history rewrite · `REPO_HYGIENE_REPRO_BATCH_D_2026-10-01.md`  
**Path3 0050 ETF recon policy (2026-09-30):** Stage A **`ETF_POLICY_LEDGER_RATIO_HIT`** · champion `LEDGER_SOFT_RATIO` · SCHEDULE_W ruled out · Soft KEEP · broker false · no live · `FIN_SAT_PATH3_ETF_RECON_POLICY_STAGEA_DECISION_PACK.md`  
**Path3 satellite overlay re-home (2026-09-30):** Stage A **`OVERLAY_REHOME_REQUIRED__KEEP_PATH3_OUT`** · recommend `KEEP_OVERLAY` · no Path3 `00631L` recon · Soft/COOL KEEP · `FIN_SAT_PATH3_SATELLITE_REHOME_STAGEA_DECISION_PACK.md`  
**Path3 0050 / satellite scope (2026-09-30):** Stage A **`ETF_DIVERGES__SATELLITE_OVERLAY_BLOCK`** · 0050 COMP≠SAT material but needs new ETF recon policy · 00631L overlay re-home first · Soft KEEP · broker false · cutover BLOCKED · no live · `FIN_SAT_PATH3_ETF_SAT_SCOPE_STAGEA_DECISION_PACK.md`  
**Path3 0050 ETF recon NAV dual (2026-09-30):** Stage B **`ETF_NAV_DUAL_HIT`** · **T+0** fill · LEDGER_SOFT_RATIO−KEEP full CAGR **+0.95**pp · held **+1.68**pp · sealed MDD **+7.13**pp · tipY **+3.78** / tip1y **+1.44** · yearly ret W–L **7–8** · Soft-core carve-only · Soft KEEP · no live · `FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_DECISION_PACK.md`  
**Path3 0050 ETF recon harden (2026-09-30):** Stage A **`ETF_HARDEN_HIT`** · T+0 · champion **`DEAD_05`** · held **+1.66**pp · tipY **+3.94** · yearly ret W–L **9–6**（vs full RATIO 7–8）· Soft KEEP · no live · `FIN_SAT_PATH3_ETF_RECON_HARDEN_STAGEA_DECISION_PACK.md`  
**Path3 0050 ETF recon year-mitigation (2026-09-30):** Stage A **`ETF_YEARMIT_HIT`** · T+0 · champion **`ADD_FULL_CUT_D05`** · held **+1.79** · 2024 **−4.0**pp（parent −5.1）· loserΣ **−5.8**（parent −7.2）· Soft KEEP · no live · `FIN_SAT_PATH3_ETF_RECON_YEARMIT_STAGEA_DECISION_PACK.md`  
**Path3 0050 ETF feature cut-gate (2026-09-30):** Stage A **`ETF_CUTGATE_HIT`** · T+0 · champion **`CG_ZZ08_ALLOW`**（大砍僅 `zz08_bear_l1`）· held **+1.90** · 2024 **−3.55** · loserΣ **−5.32**（parent −5.79）· Soft KEEP · no live · `FIN_SAT_PATH3_ETF_RECON_CUTGATE_STAGEA_DECISION_PACK.md`  
**Path4 Soft-0050 mutex (2026-09-30):** Stage A **`PATH4_MUTEX_HIT`** · Soft-own ON↔OFF · champion **`SW_TRAIL_001`** (θ=0.01) · held **+0.40** · tipY **+0.19** · corr vs P3 trail **−0.14** · not Path3 hitchhike · Soft KEEP · no live · `FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEA_DECISION_PACK.md`  
**Path4 Soft-0050 mutex Stage B (2026-09-30):** **`PATH4_MUTEX_STAGEB_HIT`** · HI↔DEF clips · champion **`SW_HI_DEF_0005`** · held **+0.11** · tipY **+0.62** · held < Stage A carve parent(+0.40) · Soft KEEP · no live · `FIN_SAT_PATH4_SOFT_0050_MUTEX_STAGEB_DECISION_PACK.md`  
**Path3 strategy cutover (2026-09-29/30):** Stage A **`CUTOVER_SCOPE_DEFINED`** · Stage B **`PAPER_WITHIN_HIT`** (0kam) · **ACCEPT ballot OPEN** · scope `WITHIN_SLEEVE_PATH3` · paper WITHIN−FLIP held **+3.04** tipY **+0.27** sealed MDD **+7.24** · pre-ACCEPT disposition filed · Soft KEEP · live flag **OFF** · broker false · `PATH3_STRATEGY_CUTOVER_ACCEPT_BALLOT_OPEN.md` · checklist `CUTOVER_CHECKLIST_PATH3_STRATEGY.md`  
**Path4 Soft-0050 extreme OFF (2026-09-30):** **`PATH4_EXTREME_HIT`** · champion **`SW_FULL_CASH_00025`** Soft-core full-cash risk-off · held **+6.51** tipY **+6.12** sealed MDD **+3.97** · beats Stage A parent · 0050 cash-park runner held+0.49 · Soft KEEP · no live · `FIN_SAT_PATH4_SOFT_0050_MUTEX_EXTREME_OFF_DECISION_PACK.md`  
**Path4 Soft-0050 extreme OFF disposition (2026-09-30):** **EXECUTED `KEEP_STAGEA_RENORM`** · Path4 Soft-0050 primary = Stage A **`SW_TRAIL_001`** · FULL_CASH = separate Soft-core risk-off track · Soft KEEP · no live · `PATH4_SOFT_0050_EXTREME_OFF_DISPOSITION_EXECUTED.md`  
**Path3 strategy cutover (2026-09-30):** **EXECUTED ACCEPT / LIVE WIRED** · scope **`WITHIN_SLEEVE_PATH3`** · Soft FIN/TEL Exact T+1 **OFF** · Soft clips+0050 KEEP · Path3 ledger **daily** · T0 carve KEEP · flip mute superseded-when-ON · broker **false** · paper 0kam WITHIN−FLIP held **+3.04** tipY **+0.27** sealed MDD **+7.24** · `LIVE_PATH3_STRATEGY_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` · checklist `CUTOVER_CHECKLIST_PATH3_STRATEGY.md`  
**Path3×Path4 Soft-0050 coexist (2026-09-30):** Stage A **`P3_P4_COEXIST_HIT`** · champion `P3_P4_CASH_00025` · held **+2.99** tipY **−0.28** sealed MDD **+1.36** · OFF book **CASH_ETF** (RENORM forbidden live) · Soft sticky≠P4 gate · Soft KEEP · Path4 live **OFF** · broker false · `FIN_SAT_PATH3_PATH4_COEXIST_STAGEA_DECISION_PACK.md`  
**Path3×Path4 tip Soft twin / live optimize (2026-09-30):** Stage B **`LIVESTACK_TWIN_MDD_BLOCK`** · base `BASE_LIVE_FUSE_COOL` · best `LIVE_P3_WITHIN` held+0.85 tipY+2.85 sealed MDD**−0.50** · P3+P4 θ 皆 MDD_BLOCK 且 held≤P3 · P4-only NO_EDGE · **keep Soft+COOL+FUSE** · Path4 live OFF · `FIN_SAT_PATH3_PATH4_LIVESTACK_TWIN_STAGEB_DECISION_PACK.md`  
**Path3×Path4 live-stack T+0 overlay twin (2026-09-30):** Stage B **`LIVESTACK_T0_MDD_BLOCK`** · Soft-core T+0×frozen COOL vs Exact T+1 live · best `T0COOL_P3_P4_CASH_00025` held+0.99 tipY−1.67 sealed MDD**−3.16** · **keep Soft+COOL+FUSE** · Path4 live OFF · `FIN_SAT_PATH3_PATH4_LIVESTACK_T0_TWIN_STAGEB_DECISION_PACK.md`  
**Research↔live align gap (2026-09-30):** Stage A **`ALIGN_GAP_LARGE`** · Soft-core→live held **+2.51**pp · tip Soft ladder largest step **+FUSE −3.24** held / tipY **−20** · COOL repairs · protocol **P1–P6** · Soft KEEP · no live · `RESEARCH_LIVE_ALIGN_GAP_STAGEA_DECISION_PACK.md`  
**tip Soft hybrid runner (2026-09-30):** Stage A **`HYBRID_MDD_BLOCK`** · default twin `TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE` · Soft Exact T+1 overlays + P3/P4 Exact T+0 carve · champion `HYBRID_P3_P4_CASH_00025_T0` held **−3.22** tipY **−5.70** sealed MDD **−8.72** · **keep Soft+COOL+FUSE** · Path4 live OFF · Soft KEEP · no live · `TIP_SOFT_HYBRID_RUNNER_STAGEA_DECISION_PACK.md`  
**Meta-detect stack-select (2026-09-30):** Stage A **`META_DETECT_MDD_BLOCK`** · Soft always-on · FUSE/COOL/P3 detector-gated · champion `DETECT_P3_THETA` held **+1.25** tipY **+2.87** sealed MDD **−0.50** · Soft KEEP · Path4 OFF · no live · `META_DETECT_STACK_SELECT_STAGEA_DECISION_PACK.md`  
**Meta-detect sealed-MDD harden (2026-09-30):** Stage A **`SEALED_MDD_HARDEN_HIT`** · champion `P3_THETA_NEARPEAK3` held **+1.45** tipY **+5.68** sealed MDD **−0.04** · vs 0kat sealed **+0.46**pp · Soft KEEP · Path4 OFF · no live · next Stage B hybrid twin · `META_DETECT_SEALED_MDD_HARDEN_STAGEA_DECISION_PACK.md`  
**Hybrid twin × NEARPEAK3 Stage B (2026-09-30):** Stage B **`HYBRID_NEARPEAK3_MDD_BLOCK`** · `HYBRID_P3_NEARPEAK3` held **−2.25** tipY **−5.78** sealed MDD **−3.06** · sealed vs ungated **+8.38**pp still blocks · tip Soft Exact T+1 NEARPEAK3 dual-track **HIT KEEP** · Soft-core T+0 carve no promote · Soft KEEP · Path4 OFF · no live · `META_DETECT_HYBRID_NEARPEAK3_STAGEB_DECISION_PACK.md`  
**tip Soft Exact T+1 NEARPEAK3 paper/observe (2026-09-30):** **OBSERVE OPEN / OPERATING** · human `OPEN paper observe: TIPSOFT_P3_THETA_NEARPEAK3 (tip Soft Exact T+1 · meta-detect Path3 near-peak3 · NOT hybrid T+0 carve)` · Exact T+1 only · hybrid T+0 carve **FORBIDDEN** · held **+1.45** tipY **+5.68** sealed MDD **−0.04** · Soft KEEP · Path4 OFF · cutover **BLOCKED** · `TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
**tip Soft Exact T+1 LIVE_OVERRIDE (2026-09-30):** **OBSERVE KEEP** + **LIVE WIRED (gate stamps / telemetry)** · ACCEPT Exact T+1 OVERRIDE · held **+1.61** tipY **+6.04** paper · Path3 WITHIN KEEP · Soft FIN/TEL stay OFF · Path4 OFF · broker false · `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`  
**tip Soft LIVE_OVERRIDE ACCEPT (2026-09-30):** **EXECUTED ACCEPT / LIVE WIRED (gate stamps / telemetry)** · Exact T+1 OVERRIDE · **not** return-blend on tip orders · Path3 WITHIN KEEP · Soft FIN/TEL stay OFF · Path4 OFF · broker **false** · `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`  
**Project code review (2026-10-01):** tip Soft LIVE_OVERRIDE **stamps/telemetry FIXED** · nav_stale fail-loud · flatten signal cols · observe SSOT aligned · broker false · Path3 WITHIN KEEP · `PROJECT_CODE_REVIEW_2026-10-01.md`  
**tip Soft T+0 gap attribution (2026-09-30):** Stage A **`T0_NOT_DRIVER`** · OVERRIDE Exact T+1 vs L3 held **+1.61** tipY **+6.04** · Soft-core T+0 held **−2.51** · hybrid T+0 tipY **−5.78** · same-clock OVERRIDE−L4 held **+0.77** · live lag ≠ T+0 · Soft KEEP · Path4 OFF · `TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_DECISION_PACK.md`  
**tip Soft LIVE_OVERRIDE apply path (2026-10-01):** Stage A **`APPLY_TIPY_OWNERSHIP_BLOCK`** · gap vs L4 held **+0.77** tipY **+3.19** · tipY ≈ MUTE_S3_SAT vs always-WITHIN · force-LIVE/soft-α tipY≈0 · Soft FIN/TEL hole on Path3 OFF · **KEEP stamps** · Soft KEEP · Path4 OFF · no apply wire · `TIPSOFT_IP3_APPLY_PATH_STAGEA_DECISION_PACK.md`  
**Path3 OFF-day fill lock (2026-10-01):** Stage A **`FILL_LOCK_BLOCK`** · Soft-refill tipY **+3.19** FORBIDDEN · MUTE Path3-ON **~10%** · Soft-core FREEZE/0050/CASH held≪0 · **no ACCEPT apply** · KEEP stamps · `TIPSOFT_IP3_FILL_LOCK_STAGEA_DECISION_PACK.md`  
**tip Soft perfection ladder (2026-10-01):** Stage A **`LADDER_STEP1_KEEP__STEP2_BLOCKED`** · step1 KEEP CURRENT · step2 BLOCKED · step3 GATED · step4 DEFAULT_NO · Soft KEEP · Path4 OFF · no wire · `TIPSOFT_IP3_PERFECT_LADDER_STAGEA_DECISION_PACK.md`  
**tip Soft unlock paths (2026-10-01):** Stage A **`UNLOCK_HIGHON_FILL_HIT`** · Soft-core champ `TRAIL42≥−0.01×FT→CASH` held **+1.20** tipY **+8.53** · Soft-refill tipY **+3.19** needs WITHIN-loosen ACCEPT · next tip Soft twin Stage B · Soft KEEP · Path4 OFF · no live · `TIPSOFT_IP3_UNLOCK_PATH_STAGEA_DECISION_PACK.md`  
**tip Soft high-ON×CASH twin (2026-10-01):** Stage B **`TWIN_HIT`** · champ `ON_UNLESS_MUTE×CASH` held **+0.87** tipY **+2.44** sealedMDD **+0.02** · DRAFT observe · Soft FIN/TEL OFF · Path4 OFF · no live · `TIPSOFT_IP3_HIGHON_CASH_TWIN_STAGEB_DECISION_PACK.md`  
**tip Soft high-ON×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING** · human OPEN `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` · held **+0.8735** tipY **+2.4396** · Soft FIN/TEL OFF · Path4 OFF · apply BLOCKED · `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
**tip Soft TRAIL42×CASH observe (2026-10-01):** **OBSERVE OPEN / OPERATING** · human `Trail42 cash的mdd可接受` → sealed MDD **-0.3632 ACCEPTABLE** · OPEN `TIPSOFT_P3_TRAIL42_FT_CASH` held **+1.4549** tipY **+11.3364** · Soft FIN/TEL OFF · Path4 OFF · apply BLOCKED · 0kba KEEP · `TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md`  
**tip Soft NEARPEAK3 × Path4 stack (2026-09-30):** Stage A **`PATH4_STACK_HIT`** · champion `P3NEAR_P4_DEFEND` held **+1.46** tipY **+5.59** · vs NEARPEAK3-only **NO_EDGE** · Path4 live **OFF KEEP** · Soft KEEP · no wire · `TIPSOFT_NEARPEAK3_PATH4_STACK_STAGEA_DECISION_PACK.md`  
**I_p3 signal refine (2026-09-30):** Stage A **`IP3_REFINE_NO_EDGE`** · pure I_p3 held+ **0** · note `NEAR&PEAK2` year_gap↑+0.10 held−0.02 · KEEP NEARPEAK3 · Path4 DRAFT 0kay · Soft KEEP · `TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_DECISION_PACK.md`  
**Path4 held-pos gate (2026-09-30):** Stage A **`PATH4_HELD_POS_HIT`** · champion `P4_C001_NEAR&SAT` held vs NEARPEAK3 **+0.027** · DRAFT observe `TIPSOFT_PATH4_NEAR_SAT_OBSERVE_BALLOT_DRAFT.md` · Path4 live OFF · Soft KEEP · `TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_DECISION_PACK.md`  
**I_p3 asymmetric gate (2026-09-30):** Stage A **`IP3_ASYMM_YEAR_SOFT`** · screened 456 · held_pos **0** · champ `ASYMM_NEAR__X_R5NEG__MS8_CD3__P4_SAT` held vs NEAR **−0.076** year_gap↑ **+0.35** · soft-α/mutex/hyst no held+ · KEEP NEARPEAK3 · Path4 DRAFT · Soft KEEP · no live · `TIPSOFT_IP3_ASYMM_GATE_STAGEA_DECISION_PACK.md`  
**I_p3 trailing prem mute (2026-09-30):** Stage A **`IP3_TRAIL_MUTE_HIT`** · champ `MUTE_P3_W63_Tm001__S3_MUTESAT` held vs NEAR **+0.070** year regret↑ **+0.136** tipY **+6.04** · strong **9** · DRAFT observe `TIPSOFT_IP3_TRAIL_PREM_MUTE_OBSERVE_BALLOT_DRAFT.md` · Soft KEEP · Path4 live OFF · no live · `TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_DECISION_PACK.md`  
**Live↔stack trail-race (2026-09-30):** Stage A **`IP3_LIVE_STACK_RACE_HIT`** → **LIVE WIRED** · ACCEPT Exact T+1 LIVE_OVERRIDE · held **+1.61** tipY **+6.04** · Path3 WITHIN KEEP · broker false · `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md`  
**Live-year residual 2013/19/20 (2026-09-30):** Stage A **`IP3_LIVE_YEAR_RESIDUAL_HIT`** · champ `SHORT_SAT_W21_M0005_K1_ST0` held vs 0kb2 **+0.011** · targetΔlive↑ **+0.156** · beats_live **8** KEEP · 2020 unfixed · DRAFT refine `TIPSOFT_IP3_LIVE_YEAR_RESIDUAL_OBSERVE_BALLOT_DRAFT.md` · Soft KEEP · Path4 OFF · no live · `TIPSOFT_IP3_LIVE_YEAR_RESIDUAL_STAGEA_DECISION_PACK.md`  
**2020 defend/off-peak knife (2026-09-30):** Stage A **`IP3_Y2020_DEFEND_NO_EDGE`** · **stop_freeze_0kb2=true** · held+∧y20 **0**/147 · FUSE/PROXY can flip·cut 2020 but held≪0 · KEEP/OPEN **0kb2** `OVERRIDE_LIVE_W42_M0005_K3` observe mainline · Soft KEEP · Path4 OFF · no residual paper stacks · `TIPSOFT_IP3_Y2020_DEFEND_STAGEA_DECISION_PACK.md`  
**FIN×SAT Path3 observe θ=0.005 + T+0 live (2026-09-29):** **EXECUTED ACCEPT** · dual-paper θ=**0.005** · `live_t0_carve_fin_sat_switch_fill/emit` **ON** · weight engine **ledger** (0kab) · mute **ON** (0kaa) · broker **false** · cutover **BLOCKED** · `FIN_SAT_PATH3_OBSERVE_THETA005_T0_LIVE_BALLOT_EXECUTED_ACCEPT.md`

新機制 N1–N3：**STOP / ladder exhausted** · `PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md`  
新機制 V2 S1–S2：**STOP / ladder exhausted** · `PRIV_MDD_SENSOR_S2_DECISION_PACK.md`  
新機制 V3：**STOP** · `PRIV_MDD_M1_SCALE_V3_DECISION_PACK.md`（N1–N3+V2+V3 STOP）  
新機制 V4：**STOP**（A0 span>120 · A1 未開）· `PRIV_MDD_SEALED_EPISODE_V4_DECISION_PACK.md`（N1–N3+V2+V3+V4 STOP）  
新機制 V5：**STOP** · `PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION_PACK.md`（N1–N3+V2+V3+V4+V5 STOP）  
新機制 V6：**STOP** · `PRIV_MDD_SHADOW_RELNAV_V6_DECISION_PACK.md`（N1–N3+V2+V3+V4+V5+V6 STOP）  
民股金控 Gate V7：Stage A SOFT → OBSERVE → NEAR_FLAT → **Class D LIVE WIRED** (`ACCEPT Class D: FinPriv V7 F05`) · Soft-Frozen 3-sleeve KEEP · `CLASSD_FINPRIV_V7_F05_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`  
民股金控 Gate V8（AND-confirm）：**Stage A `PRIV_FINHC_V8_SOFT`** · 0 HIT · 5 soft · best `V8_BSIDE_MA120_F05_KDMAY_COOL1` · Soft-Frozen 公股 KEEP · no V7 retune · `PRIV_FINHC_GATE_V8_DECISION_PACK.md`  
COOL × 台50反1（成立買／結束賣）：**Stage A `COOL_INV_SOFT`** · Soft-Frozen KEEP · `COOL_T50_INV_SATELLITE_DECISION_PACK.md`  
COOL 結束 × 台50正2（`00631L` 搶反彈）：**Stage A `MDD_BLOCK`** · Soft-Frozen KEEP · `COOL_T50_LEV_REBOUND_DECISION_PACK.md`  
`00631L` 短線輔助（確認進場等）：**Stage A `SHORT_ASSIST_HIT` → OBSERVE → LIVE WIRED `CONF_RET3_A10_H5`** · Soft-Frozen KEEP · forward-only · `LIVE_CONF_RET3_A10_H5_00631L_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`  
COOL dual-handoff（防守 `00632R` → 結束 `00631L`）：**Stage A `DUAL_HANDOFF_SOFT`** · 0 HIT · Soft-Frozen KEEP · no live · `COOL_T50_DUAL_HANDOFF_DECISION_PACK.md`  
TEL within-sleeve 三軌（名目／結構／COOL 聯動）：**Stage A `TEL_WITHIN_SOFT`** → densify near-flat → **LIVE WIRED `T3_COOL_INV_VOL20`** · Soft-Frozen KEEP · `LIVE_TEL_T3_COOL_INV_VOL20_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`  
TEL T3 densify／T2 半開／近持平 +0.15：**Stage A `TEL_NEARFLAT_READY`** → human `請上live` → **LIVE WIRED `T3_COOL_INV_VOL20`** · Soft-Frozen KEEP · forward-only · `LIVE_TEL_T3_COOL_INV_VOL20_CUTOVER_BALLOT_EXECUTED_ACCEPT.md`  
Live tip fill 高低點／機制審計：**`FILL_EXTREME_AUDIT_DONE`** · 96 fills · ±5d mean ~3.8% · T+1 結構性 · Soft-Frozen KEEP · no live · `LIVE_FILL_EXTREME_AUDIT_DECISION_PACK.md`  
Soft∥Sleeve ops auto-fuse agenda：**CLOSED**（Gate H FORBIDDEN KEEP）· `ACCEPT_DROP_AUTO_FUSE_AGENDA.md`  
Portfolio: `research/ops/RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md`  
Binding decisions: `research/ops/HUMAN_DECISION_REGISTER.md`  
Live claims: `research/ops/LIVE_CLAIM_TARGET_POLICY.md`  
Strategy update SOP: `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`

## What is live (only this)

| Item | Value |
|---|---|
| Stack | **E16 + Exact T+1 E18 + E22_v3_recv_pay_effdelay** |
| Path | `forward/e21/` |
| Capital / lot | **500M** · board-lot **1000** |
| Clip | Financial **[0.60, 0.80]** · TEL **[0.03, 0.35]** · 0050 **[0.00, 0.50]** via `scripts/e16_soft_frozen_base.py` |
| Within-sleeve | FIN **`KD_OPT`** · TEL **`T3_COOL_INV_VOL20`** (COOL-defend INV_VOL soft-tilt; else EQUAL) · Class D FinPriv V7 F05 carve (`REG_BULL_SIDE` · 5% · `PRIV_KD_MAY`) · FUSE Soft sell **`SELL_a75`** · COOL-exit satellite **`CONF_RET3_A10_H5`/`00631L`** |
| Overlay | **`FUSE_ADDITIVE` KEEP** + **`COOL_c8_f50_d21`** (`LIVE_FUSE_ADDITIVE` / `LIVE_COOL_EXPOSURE`; **DH replaced** 2026-09-25) |
| Offense CAGR paper | Stage A **`OFFENSE_CAGR_SOFT`** (Soft/Sleeve/FUSE densify under COOL · Soft-Frozen KEEP · no live) · `OFFENSE_CAGR_UNDER_COOL_STAGEA_SCREEN.md` |
| Legacy A05 stitch | **DROPPED** (`ACCEPT_2026-09-09_DROP_E45_A05`) — see `E45_A05_STITCH_DROPPED.md` |
| Daily job | `.github/workflows/v412f-forward-paper.yml` (weekdays; **holiday = no tip advance**) |
| QC smoke | `.github/workflows/e21-live-qc-smoke.yml` |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` |

**Books dual clock (intentional — not tip lag):** tip / Stage-E DEFAULT = `E22_v3_recv_pay_effdelay`; FUSE offense full-history rebuild pins preserved cash-on-ex `E22_v2s_tw_effex` (`live_dh_fuse_cutover`). Do not “fix” tip lag by rewriting history.  
**Cash clocks (never merge):** A Exact T+1 `portfolio_state.cash` · B R4 `settled_cash_estimate` · C cash+`e22_receivables` — see `CASHFLOW_THREE_VIEWS.md`.  
**FinMind:** hourly quota + payment-date preserve — `FINMIND_API_QUOTA_AND_RETRY.md`.

**Not live (paper / archive):** independent Soft-assist · Sleeve-tilt · FINCAP BLEND_025 · FIN 民營 native (observe shadow; Class D V7 F05 carve is live) · FIN_CAP_50 · L4 · E50-A · legacy E45 A05 blend stitch · Track A/B · E6/E9/E10 shadows.

## Paper sleeves (observe only)

| Sleeve | Status | Cutover |
|---|---|---|
| FIN_CAP_50 | **OBSERVE CLOSED** (2026-09-28) | **REJECT static cutover for now** (`NOT_READY_SEALED_CAGR`) — register #2 · batch `OBSERVE_UP_DOWN_BATCH_2026-09-28.md` |
| L4_DD_PATH_08_50 | Held-out PASS; YTD **and** trailing_1y PAUSE_REVIEW (asof 2026-09-16) | **DEFER** cutover — register #4; checklist: `CUTOVER_CHECKLIST_L4.md` (hygiene sync `L4_HYGIENE_CHECKLIST_SYNC_2026-09-19.md`) |
| BLEND_025 | **OBSERVE CLOSED** (2026-09-28) | Was sealed-CAGR successor (register #3); live **NOT READY** (#5); promote review **2026-09-26 BLOCKED** · paper queue closed · batch `OBSERVE_UP_DOWN_BATCH_2026-09-28.md` |
| FIN both-quality `B_OR_K9_x_HARD150` | **OBSERVE CLOSED** (2026-09-28) | Superseded by COMPOSITE · `COMPOSITE_OBSERVE_OPEN_PARENTS_CLOSE_2026-09-28.md` |
| `SAT_A20_H5` | **OBSERVE CLOSED** (2026-09-28) | Superseded by COMPOSITE · `COMPOSITE_OBSERVE_OPEN_PARENTS_CLOSE_2026-09-28.md` |
| FIN×SAT COMPOSITE `COMP_H150_x_A20` | **OBSERVE OPEN** (2026-09-28) | Stage A HIT · cutover **BLOCKED** · `FIN_SAT_COMPOSITE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| `SAT_A20_RELAX` tip-first densify | **OBSERVE OPEN** (2026-09-28) | Stage A `SAT_RELAX_HIT` · cutover **BLOCKED** · `SAT_A20_RELAX_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| FIN×SAT Path3 `P3_T0_STATE` | **OBSERVE OPEN** (2026-09-28) | Exact T+0 carve `T0_CARVE_FIN_SAT_SWITCH` · cutover **BLOCKED** · `FIN_SAT_PATH3_T0_STATE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| tip Soft Exact T+1 `P3_THETA_NEARPEAK3` | **OBSERVE OPEN** (2026-09-30) | meta-detect Path3 near-peak3 · Exact T+1 only · hybrid T+0 **FORBIDDEN** · cutover **BLOCKED** · `TIPSOFT_P3_NEARPEAK3_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| tip Soft Exact T+1 `TIPSOFT_P3_ON_UNLESS_MUTE_FT_CASH` | **OBSERVE OPEN** (2026-10-01) | Path3 ON unless lag63 prem_p3<-0.01 ∧ sat_lead · OFF→FIN∪TEL→cash · Soft FIN/TEL stay OFF · Exact T+1 tip Soft twin · apply/cutover **BLOCKED** · `TIPSOFT_IP3_HIGHON_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| tip Soft Exact T+1 `TIPSOFT_P3_TRAIL42_FT_CASH` | **OBSERVE OPEN** (2026-10-01) | TRAIL42≥−0.01 × FT→CASH · sealed MDD **ACCEPTABLE** (−0.36) · Soft FIN/TEL stay OFF · apply/cutover **BLOCKED** · `TIPSOFT_IP3_TRAIL42_CASH_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| tip Soft Exact T+1 `LIVE_OVERRIDE_W42_M05_K3` | **LIVE WIRED (stamps/telemetry)** (2026-09-30) | ACCEPT Exact T+1 OVERRIDE · gate stamps only · Path3 WITHIN KEEP · Soft FIN/TEL stay OFF · broker **false** · apply path Stage A **`APPLY_TIPY_OWNERSHIP_BLOCK`** (0kb6) · `TIPSOFT_IP3_LIVE_OVERRIDE_BALLOT_EXECUTED_ACCEPT.md` |
| Offense SOFT near-flat (`SELL_a75`) | **LIVE WIRED** under COOL | sell boost 0.75 · coexists FUSE+COOL · Soft-Frozen KEEP · `LIVE_SELL_A75_UNDER_COOL_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| `00631L` short-assist `CONF_RET3_A10_H5` | **LIVE WIRED** (forward-only) | COOL exit · RET3 · α=0.10 · H=5 · Soft-Frozen KEEP · `LIVE_CONF_RET3_A10_H5_00631L_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| TEL `T3_COOL_INV_VOL20` | **LIVE WIRED** (forward-only) | COOL-defend INV_VOL soft-tilt · else EQUAL · Soft-Frozen KEEP · `LIVE_TEL_T3_COOL_INV_VOL20_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| Track A S9A1 | KEEP (paper/monitor) | N/A — pointer: `TRACK_A_RUNBOOK_POINTER.md` |
| Track B S1 | STOP | Closed |

## Cadence

| Cadence | How |
|---|---|
| Daily live | `v412f-forward-paper` · tip-write gate `forward_tip_write_gate.py` (fail-closed if post-forward `ok!=true`) · day-commit `commit_day_books` (state last) |
| Live QC smoke | `e21-live-qc-smoke` |
| Month-end pack | `ops-month-end-paper-pack` / `scripts/ops_month_end_paper_pack.py` · freshness: `MONTH_END_PACK_FRESHNESS.md` |
| Live↔paper recon | Inside pack + `scripts/e21_live_vs_paper_recon.py` |
| Live modularization | `research/ops/ARCH_LIVE_MODULARIZE.md` (`live_config` / strategy / execution / ledger) |
| Installable package | `pyproject.toml` · `pip install -e .` · ops image `Dockerfile` |
| Docker QC smoke | `scripts/ops_docker_qc_smoke.sh` · `docker compose` · workflow `docker-ops-qc-smoke` |
| TWSE session calendar | `twse_session_sources.py` + P2 `twse_forward_session_gate` in `v412f-forward-paper` (`session_skip.json`) · Y±1 **loader** · **2025 CSV pinned** · **2027 wait** for TWSE publish |
| Fill ports | `paper` · `dry_run` · P4 `broker` preflight + fixture-ack shadow (`broker_acks/`; Soft-Frozen default untouched) |
| Broker live-write 防呆 | `broker_safety` + **`broker_risk`**（狀態機／panic／黑名單／限額／限流／重啟對帳／熔斷讀寫分離＋half-open cooldown／stale 標記／告警；另含 process lock／dedupe／confirm）· `BROKER_RISK_RECOVERY.md`；`LIVE.broker_live_write_accepted=False` until ACCEPT |
| 元大 SPARK UAT | 無本機固定 IP 時：最小 GCP 靜態 IP VM 教學 `YUANTA_SPARK_UAT_GCP_STATIC_IP_HOWTO.md`（**不**寫 Soft-Frozen） |
| 元大 SPARK adapter | 離線骨架 `yuanta_spark_adapter.py`（BasketNo／張數／ack map；`API_WIRED=False`）· `YUANTA_SPARK_ADAPTER_SKELETON.md` |
| 元大 SPARK PROD | 正式開通後只讀：`YUANTA_SPARK_PROD_READONLY_HOWTO.md`（教學）· `YUANTA_SPARK_PROD_READONLY_CHECKLIST.md`（上限；**不下單**） |
| 元大 SPARK 條件單 | App↔API 對照（營業員建議二擇一）：`YUANTA_SPARK_CONDITIONAL_OCO_NOTES.md`（研究；**未** SendAlgo） |
| Fee model | `0.001425×0.6` + sell 證交稅；**MIN_COMMISSION NT$20** floor (`live_ledger.fees_tax_for`) · day-trade tax not modeled |
| T+2 settlement estimate | R4 daily artifact via `v412f-forward-paper` · R5 `twse_t2_broker_reconcile.py` (observe) · week-1 checklist `R4_R5_WEEK1_OBSERVE_CHECKLIST.md` |
| 除權息入帳延後 | Stage-E live DEFAULT `E22_v3_recv_pay_effdelay` (receivable + effective pay); preserved `E22_v2s_tw_effex`; MOPS overlay; Gap 6.9c stock-pay observe |
| **現金流三視角** | Human priority **算準現金流** (2026-09-20) · A Exact T+1 `cash` · B R4 `settled_cash_estimate` · C Stage-E `cash+e22_receivables` (TAX0) · tip **aligned** 2026-09-21 · `CASHFLOW_THREE_VIEWS.md` · `cashflow_three_views_report.py` · Monday **CONFIRMED** `TIP_CATCHUP_MONDAY_2026-09-21.md` |
| NHI 股利補充保費 | Human: 單次達 **NT$20,000** → **2.11%** 就源扣（≠ 所得稅 ballot A）· sandbox `E22_v3_recv_pay_effdelay_nhi211` · **not** live · purpose `TAX_FOR_CASHFLOW_PURPOSE.md` · `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md` |
| Realism → 全自動化 gap-close | Phase **0–1+2+3+5 LANDED** · Phase **4 scaffold** (synthetic R5) · Phase 2 tip **CONFIRMED** 2026-09-21 · roadmap `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md` · `PHASE_2_TIP_CATCHUP_CONFIRMED_2026-09-21.md` |
| Held-\|MDD\|≤17% paper target | R1 **`MDD17_HIT_CAGR_OK`** · R2 Stage B **`TIPSAFE_STRETCH`** · **`COOL_c8_f50_d21` LIVE WIRED** 2026-09-25 (replace DH, keep FUSE) · Soft-Frozen **KEEP** · `LIVE_COOL_C8_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| Full-review harden (2026-09-20) | Ex entitlement snapshot · Y±1 **loader** (`load_calendar_window`) · **2025 CSV pinned** (`twse_sessions_2025.csv`) · **2027 wait** for TWSE publish · blank-pay fail-closed · uncommitted orders/nav · NHI211 settle-time premium · forward GHA allow flags · R5 path jail · tax CLI stripped · Soft-Frozen **KEEP** |
| Residual gap-close (2026-09-20) | TAX0 vs NHI211 observe `E22_TAX0_VS_NHI211_OBSERVE.*` (`promote_ready=false`) · Gap6 `nhi211_*` tax sensitivity · `DIV_APPLIED_EMPTY_IN_RECV_WINDOW` · e50 Y±1 calendar align · Soft-Frozen **KEEP** |
| E22 payment-date completeness | Soft-Frozen + private cash/stock pay blank **0%** after re-backfill 2026-09-21 (`E22_PAYMENT_DATE_REBACKFILL_2026-09-21.md`) · DQ `kpi_ok` · Soft-Frozen **KEEP** |
| Month-end monitors | all thin wrappers → `ops_dual_paper_month_end` (`DualPaperMonitorSpec` / `MultiPaperMonitorSpec`) |
| Repro/ops dedupe | Decision packs SSOT in `research/ops` · `repro/*/reports` pointers · no reports≡outputs NAV · `REPRO_DEDUPE_HYGIENE.md` · helper `ops_repro_ssot.py` |
| Dual-paper ledgers | shared driver `ops_dual_paper_ledgers` (14/14 wrapped; M2=`chal_market` · DH=`post_base` · priv=`sim_context`) |

Latest pack: `research/ops/MONTH_END_PAPER_PACK.md` (2026-09-10 primary observe: `OPS_CADENCE_2026-09-10_PRIMARY_OBSERVE.md`)  
Data freshness: `research/ops/MONTH_END_DATA_FRESHNESS.md` · guidance `MONTH_END_PACK_FRESHNESS.md`  
Alerts: `research/ops/OPS_ALERTS.md`  
E22 KPI: `research/ops/E22_DATA_QUALITY_KPI.md`  
Gap #6 fidelity: `research/ops/E22_GAP6_FIDELITY_KPI.md`  
Data-source resilience: `research/ops/DATA_SOURCE_RESILIENCE.md`  
Data-source resilience KPI: `research/ops/DATA_SOURCE_RESILIENCE_KPI.md`  
Data-source shadow reconcile (Phase B): `research/ops/DATA_SOURCE_SHADOW_RECONCILE.md`  
Odd-lot promote (**PROMOTED** 2026-09-05): `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`  
Odd-lot promote decision pack (**ACCEPT promote**): `research/ops/ODD_LOT_PROMOTE_DECISION_PACK.md`  
Par-value lookup charter: `research/ops/PAR_VALUE_LOOKUP_CHARTER.md`  
Par-value inventory: `research/ops/PAR_VALUE_INVENTORY.md` · `data/corporate_actions/par_value_by_code.csv`  
Tax/receivable formal books: Stage-E live **TAX0** · human **BALLOT A KEEP TAX0** (2026-09-20) — after-tax DEFAULT path closed this cycle; sandbox tax10/20 research-only · NHI211 dual-book observe `E22_TAX0_VS_NHI211_OBSERVE.md` · `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` · Stage B `E22_V3_TAX_RECV_STAGE_B_STATUS.md`  
Realism automation gap-close (toward 全自動化): Phase **0–1 + 2 + 3 + 5 LANDED** — tip Stage-E confirm 2026-09-21 · verify · `ops_alert_scan` R4/tip-lag · `v412e22-dividend-events` weekday cron · Phase 4 R5 **synthetic OK** 2026-09-27 (`R5_OBSERVE_SYNTHETIC_2026-09-27.md`) · waiting real custody drop-in · roadmap `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md` · `PHASE_2_TIP_CATCHUP_CONFIRMED_2026-09-21.md` · next tip catch-up **2026-09-29** `TIP_CATCHUP_2026-09-29_CHECKLIST.md`
E45 A05 live-stitch (**DROPPED** 2026-09-09): Soft-Frozen CRITICAL class KEEP as paper; dual-paper observe **OPERATING**; A05 live wire **retired** (`E45_A05_STITCH_DROPPED.md`); live risk overlay was **DH_dd06** + **FUSE** (ACCEPT 2026-09-13) → **COOL_c8 replace DH, keep FUSE** (ACCEPT 2026-09-25). Tip books align ACCEPT 2026-09-19 → tip catch-up **CONFIRMED** 2026-09-21: `ACCEPT_TIP_BOOKS_ALIGN_V3.md` · `TIP_CATCHUP_MONDAY_2026-09-21.md`. Paper/live fill skip align: `ACCEPT_PAPER_LIVE_FILL_SKIP_ALIGN.md`. Ops residual 全修 ACCEPT 2026-09-19: `ACCEPT_OPS_RESIDUAL_FULL_FIX.md` (dual-paper refresh + tip-lag stamp + INDEX_DRIFT non-decision; no challenger/broker promote).
FIN50 sealed-CAGR charter: `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md`  
FIN50 charter screen: `research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md`  
BLEND_025 paper-promote proposal: `research/gaps/FINCAP_BLEND025_DUAL_PAPER_PROMOTE_PROPOSAL.md`  
E45 blend-α=0.25 observe **ARCHIVED** (2026-09-13): `research/ops/E45_BLEND025_OBSERVE_OPEN.md` · monitor `E45_BLEND025_MONTH_END_MONITOR.md`  
E45 paper research roadmap (1–7 status): `research/ops/E45_PAPER_RESEARCH_ROADMAP.md`  
E45 P1–P7 integrated analysis: `research/ops/E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`
E45 sleeve-local deep-dive (post-P7): `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md`  
E45 sleeve-local observe **CLOSED** (2026-09-28): `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN.md`（中文：`E45_SLEEVE_LOCAL_OBSERVE_OPEN.zh-TW.md`）  
E45 blend-α=0.05 observe **CLOSED** (2026-09-28): `research/ops/E45_BLEND005_OBSERVE_OPEN.md` · monitor `research/gaps/E45_BLEND005_MONTH_END_MONITOR.md`  
  
E45 dual-sleeve monitor dashboard (#7): `research/e45/E45_DUAL_SLEEVE_MONITOR_DASHBOARD.md`  
E45 sleeve-local overlay (#6): `research/e45/E45_SLEEVE_LOCAL.md`  
E45 crisis-year attribution (#5): `research/e45/E45_CRISIS_YEAR_ATTRIBUTION.md`  
E45 alpha cost/turnover (#4): `research/e45/E45_ALPHA_COST_TURNOVER.md`  
E45 mild max_cut profile (#3): `research/e45/E45_MAXCUT_MILD_PROFILE.md`  
E45 low-alpha deep-dive (0.05–0.15): `research/e45/E45_LOW_ALPHA_DEEP_DIVE.md`  
E45 blend-alpha fine grid (step 0.05): `research/e45/E45_BLEND_ALPHA_GRID_FINE.md`  
E45 crisis-triggered alpha (paper): `research/e45/E45_CRISIS_TRIGGERED_ALPHA.md`  
E45 blend-alpha paper screen: `research/e45/E45_BLEND_ALPHA_PAPER_SCREEN.md`  
E45 A05 stitch checklist (**DROPPED / RETIRED**): `research/ops/E45_STITCH_CHECKLIST.md` · `E45_A05_STITCH_DROPPED.md`  
E45 dual-paper observe: `research/e45/E45_DUAL_PAPER_OBSERVE.md` / open `E45_DUAL_PAPER_OBSERVE_OPEN.md`  
E45 month-end: `research/gaps/E45_MONTH_END_MONITOR.md`  
L4 dual-paper promote proposal: `research/gaps/L4_DD_PATH_PROMOTE_PROPOSAL.md`  
L4 month-end: `research/gaps/L4_DD_PATH_MONTH_END_MONITOR.md`  
L4 month-end runbook: `research/gaps/L4_DD_PATH_MONTH_END_RUNBOOK.md`  
L4 cutover checklist (prep / NOT AUTHORIZED): `research/ops/CUTOVER_CHECKLIST_L4.md` · hygiene sync `L4_HYGIENE_CHECKLIST_SYNC_2026-09-19.md`  
BLEND_025 dual-paper observe: `research/gaps/BLEND_025_DUAL_PAPER_OBSERVE.md`  
BLEND_025 month-end: `research/gaps/BLEND_025_MONTH_END_MONITOR.md`  
BLEND_025 month-end runbook: `research/gaps/BLEND_025_MONTH_END_RUNBOOK.md`  
BLEND_025 cutover checklist (prep): `research/ops/CUTOVER_CHECKLIST_BLEND025.md`  
民營 native dual-paper **OBSERVE CLOSED** (2026-09-28): `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPEN.md` · Class D V7 F05 live carve KEEP · batch `OBSERVE_UP_DOWN_BATCH_2026-09-28.md` · cutover **BLOCKED** `CUTOVER_CHECKLIST_FIN_PRIV_NATIVE.md`  
 
Live claim / target policy: `research/ops/LIVE_CLAIM_TARGET_POLICY.md`  
Live E22 evidence readiness: `research/ops/LIVE_E22_FIELD_EVIDENCE.md`  
Post-forward E22 verify: `research/ops/POST_FORWARD_E22_VERIFY_RUNBOOK.md`  
Archive sentinel policy: `research/ops/ARCHIVE_SENTINEL_HYGIENE.md`  
Five-layer gaps: `research/ops/FIVE_LAYER_GAP_CHECKLIST.md`  
Human decision register: `research/ops/HUMAN_DECISION_REGISTER.md`  
Strategy update SOP: `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`  
Legacy forward config: `research/ops/FORWARD_LEGACY_NOTE.md`

## Commands

```bash
pip install -e .   # once per env; required for imports (no sys.path hacks)
python3 scripts/e21_qc.py --state-dir forward/e21
python3 scripts/ops_month_end_paper_pack.py
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers --fail-on-stale  # formal month-end
python3 scripts/ops_month_end_data_freshness.py  # tip/age only
python3 scripts/ops_alert_scan.py --report-only
python3 scripts/e22_data_quality_kpi.py
python3 scripts/e22_gap6_fidelity_kpi.py
python3 scripts/data_source_resilience_kpi.py
python3 scripts/data_source_shadow_reconcile.py
python3 scripts/data_source_phase_c_probes.py
python3 scripts/taiex_fetch_with_failover.py --help
python3 scripts/e21_live_vs_paper_recon.py
python3 scripts/e16_blend025_dual_paper_ledgers.py
python3 scripts/e16_blend025_month_end_monitor.py
python3 scripts/e45_dual_paper_ledgers.py
python3 scripts/e45_month_end_monitor.py
python3 scripts/e45_blend025_dual_paper_ledgers.py
python3 scripts/e45_blend025_month_end_monitor.py
```

## Engineering standards (2026-09-06)

- Full project code review: `research/ops/PROJECT_CODE_REVIEW_2026-09-06.md`
- E45 paper landmine review: `research/ops/E45_PAPER_LANDMINE_CODE_REVIEW.md`
- Project coding standards: `research/ops/CODING_STANDARDS.md`
- Coverage map: `research/ops/CODING_STANDARDS_COVERAGE.md`
- Hygiene: `python3 scripts/check_project_coding_hygiene.py`
- Hygiene: `python3 scripts/check_e45_paper_hygiene.py`

## Authority

1. Cutover / Now-Next: `research/STRATEGY_DEBT_BOARD.md`  
2. Strategy update SOP: `research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`  
3. This map: `research/ops/OPS_STATUS.md`  
4. Plan: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
5. Retention: `research/ops/ARTIFACT_RETENTION.md`  
6. Class ≠ live: `FROZEN_GOVERNANCE.md`

## Hard rules

- No auto Soft-Frozen flip  
- Dual-paper / held-out PASS ≠ cutover  
- Never rewrite `forward/e21` history  
- **`mtd` annualized CAGR = display-only** (non-decision)  
- Strategy merge only via human PR after checklist gates  
