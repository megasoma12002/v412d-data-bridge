# Human Decision Register — Objective Priority

Date: 2026-09-05  
Authority: `research/STRATEGY_DEBT_BOARD.md` · map: `OPS_STATUS.md`  
Live Soft-Frozen Financial clip: **[0.60, 0.80]** (β densify ACCEPT 2026-09-25; prior FINBAND [0.60, 0.90])
TEL **[0.03, 0.35]** · 0050 **[0.00, 0.50]**

## Decision rules (frozen)

1. Red gate → do **not** open a live cutover decision.  
2. Live change > paper observe (higher blast radius → later).  
3. If waiting reduces uncertainty cheaply, wait (trailing / sealed numbers).  
4. Structural fail ≠ “wait on the same lock” (FIN50 sealed CAGR).  
5. No charter → default **DEFER** (E45 / odd-lot / formal tax books).

## Explicit decisions (2026-09-05)

| Pri | Decision | Verdict | Binding effect |
|---:|---|---|---|
| 0 | Live cutover bundle `#257` | **CLOSED** (2026-09-19) | Closed not merged · keep 公股+FUSE · DH later **replaced by COOL_c8** 2026-09-25 · reopen only new mechanism or sealed-gate · 無民股小包**暫不拆** · `ACCEPT_CLOSE_CUTOVER_BUNDLE_257.md` · `LIVE_COOL_C8_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| 0b | 公股＋民營並存 × MDD | **STOP** (2026-09-19) | Stage A 0 sealed-MDD coexist · archive `#258` · `PUB_PRIV_COEXIST_MDD_DECISION_PACK.md` |
| 0c | 四類 SF4 + DH/L4 防禦 × MDD | **STOP** (2026-09-19) | Stage A 0 sealed-MDD coexist · archive `#259` · `SF4_DEFENCE_MDD_DECISION_PACK.md` |
| 0d | 民股／四類 × MDD **新機制** (N1→N2→N3) | **STOP N1–N3** (2026-09-19) | Ladder exhausted · 0 sealed coexist · Soft-Frozen KEEP · `PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md` |
| 0e | 民股 MDD **新機制 V2**（廣度／FinPub–TAIEX／FX／CBC） | **STOP S1–S2** (2026-09-19) | V2 ladder exhausted · Soft-Frozen KEEP · `PRIV_MDD_SENSOR_S2_DECISION_PACK.md` |
| 0f | 民股 MDD **新機制 V3**（M1 連續縮放 FinPriv） | **STOP** (2026-09-19) | 0 sealed coexist · best tip-clean sealed `V3_C50_0050` −0.44 · Soft-Frozen KEEP · `PRIV_MDD_M1_SCALE_V3_DECISION_PACK.md` |
| 0g | 民股 MDD **新機制 V4**（sealed 事件剖檢→日曆閘） | **STOP** (2026-09-19) | A0 span>120 · A1 未開 · Soft-Frozen KEEP · `PRIV_MDD_SEALED_EPISODE_V4_DECISION_PACK.md` |
| 0h | 民股 MDD **新機制 V5**（DH 防衛窗 → 只關 FinPriv） | **STOP** (2026-09-19) | 0 sealed coexist · best tip-clean sealed `V5_DH_0050_XTIGHT` −0.27 · Soft-Frozen KEEP · `PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION_PACK.md` |
| 0i | 民股 MDD **新機制 V6**（shadow 相對 NAV 連續阻尼 FinPriv） | **STOP** (2026-09-19) | 0 sealed coexist · best tip-clean sealed `V6_C100_PUB` −0.24 · Soft-Frozen KEEP · `PRIV_MDD_SHADOW_RELNAV_V6_DECISION_PACK.md` |
| 0k | COOL 成立買 **台50反1**／結束賣 | **STAGE A SOFT** (2026-09-25) | 0 HIT · α=0.25 MDD↑ / CAGR↓ · Soft-Frozen KEEP · `COOL_T50_INV_SATELLITE_DECISION_PACK.md` |
| 0k2 | COOL 觸發 **極短脈衝** 00632R | **STAGE A SOFT** (2026-09-25) | 0 HIT · H=1 最小傷害仍 CAGR↓ · Soft-Frozen KEEP · `COOL_T50_INV_PULSE_DECISION_PACK.md` |
| 0k3 | FUSE Soft-sell → 00632R | **STAGE A MDD_BLOCK** (2026-09-25) | 0 HIT · CAGR↓ sealed MDD↓ · Soft-Frozen KEEP · `FUSE_SOFTSELL_T50_INV_DECISION_PACK.md` |
| 1 | Soft-Frozen live clip **[0.60, 0.80]** / ETF **[0.00, 0.50]** | **FLIPPED** (ACCEPT 2026-09-25 β densify) | Was FINBAND [0.60,0.90]/ETF[0.00,0.35]; note `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_BETA_0050.md` · prior FINBAND note KEEP |
| 1b | Live starting capital | **500M** (ACCEPT 2026-09-09) | Was 3M restore; prior 15M then 3M; see `CAPITAL_500M_2026-09-09.md` |
| 2 | FIN_CAP_50 **static** live cutover | **REJECT for now** | Do not open cutover PR; do not retune FIN50 lock |
| 3 | Sealed-CAGR successor path | **FINCAP BLEND_025 OPERATING OBSERVE** | FINCAP sleeve KEEP; observe ≠ promote · **E45_BLEND025 archived 2026-09-13** |
| 4 | L4_DD_PATH live cutover | **DEFER** | No PR until checklist all-green (≥1 clean month-end, no YTD/1y PAUSE) |
| 5 | BLEND_025 → live | **NOT DECISION-READY** | Checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md`) but **NOT AUTHORIZED**; needs sustained trailing + human PR |
| 6a | Odd-lot default → `E22_v2s_tw` | **DONE** (2026-09-05) | #73+#74 merged; live `DEFAULT_BOOKS_VERSION = E22_v2s_tw`; Soft-Frozen KEEP; forward-only |
| 6b | Formal tax·receivable books | **ACCEPT charter** · tax books **BALLOT A KEEP TAX0** (2026-09-20) | Stage-E live **TAX0** affirmed; 本國人＋慣例；**no** after-tax DEFAULT this cycle; sandbox tax10/20 research-only · Soft-Frozen KEEP · `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` |
| 6c | E45 live stitch | **ROLLBACK `DROP_E45_A05`** (2026-09-09) | Was ACCEPTED `BLEND_E45_A05` same day; unwired after paper drag · `E45_STITCH_ROLLBACK_ACCEPTED_DROP_A05.md` |

## Research portfolio (2026-09-08)

| Decision | Verdict | Binding effect |
|---|---|---|
| β densify near-flat paper observe | **PROMOTED LIVE** (2026-09-25) | `OPEN … BETA_F0.60-0.80_E0.00-0.50` · Soft-Frozen KEEP · cutover BLOCKED · `#284` · `BETA_0050_DENSIFY_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| β／0050 densify under COOL | **HIT → LIVE clip** (2026-09-25) | `F[0.60,0.80] E[0,0.50]` +0.57pp tip-OK · **observe only** · Soft-Frozen KEEP · `#284` · `BETA_0050_DENSIFY_UNDER_COOL_DECISION_PACK.md` |
| Active research KEEP | **LOCKED** | FIN quartet (**`MIX_L75`** + **`KD_OPT`**) + E45 **`A05`/`C35`** + month-end gates |
| FIN within-sleeve live | **`KD_OPT` LIVE** (ACCEPT 2026-09-09) | `FIN_PRE_EXDIV_KD` forward-only; Soft-Frozen KEEP; note `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md` |
| FIN autumn post-ex probe | **STOP** (2026-09-09) | small-search+dual no lift vs KD_OPT · `FIN_KD_AUTUMN_DUAL_SEASON.md` · live KD_OPT untouched |
| FIN hold posture | **LOCKED** (2026-09-09) | Maintain KD_OPT + month-end observe; no FIN micro-tune; 大勝 → clip or new-mechanism ballot · `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md` |
| 「大勝」ballots OPEN | **EXECUTED** (2026-09-09) | Clip observe OPEN + Class D FINBAND flip + E45 A05 stitch · `BIG_WIN_BALLOTS_OPEN.md` |
| Soft-Frozen clip flip | **`F0.60-0.80_E0.00-0.50` LIVE** (2026-09-25) | `SOFT_FROZEN_CLIP_FLIP_ACCEPTED_BETA_0050.md` · prior FINBAND note KEEP |
| 「大勝」EXECUTED data re-run | **DONE** (2026-09-09) | First re-run under FINBAND+A05; NEW_LIVE −0.68 tip ALERT |
| Live-stack rollback | **EXECUTED `DROP_E45_A05`** (2026-09-09) | E45 stitch OFF; FINBAND+KD_OPT KEEP · `E45_STITCH_ROLLBACK_ACCEPTED_DROP_A05.md` |
| Post-rollback data re-run | **DONE** (2026-09-09) | `LIVE_STACK_RERUN.md` CURRENT_LIVE tip PASS held-out +0.02 · month-end pack refresh |
| Post-rollback improve status | **IMPROVED** (2026-09-09) | vs retired A05: held-out lift **+0.70**, tip ALERT→PASS · `LIVE_STACK_IMPROVE_STATUS.md` |
| Telecom async split (FIN-parallel) | **STOP** (2026-09-09) | Stage D + summer KD grid no lift vs TEL_EQUAL · keep live EQUAL · `TELECOM_WITHIN_SLEEVE_ASYNC_DECISION_PACK.md` |
| Telecom pack cutover ballot | **EXECUTED KEEP TEL_EQUAL** (2026-09-09) | Human `KEEP live TEL_EQUAL` · no live wire · `TELECOM_PACK_CUTOVER_KEEP_TEL_EQUAL.md` |
| 民營金控 paper re-screen | **STOP** (2026-09-09) | Stage A vs `LIVE_PUB_KD` · 0 coexist · Soft-Frozen 公股 R1 KEEP · post div/adj fill still STOP · `PRIVATE_FIN_HOLDINGS_DECISION_PACK.md` |
| 金融公/金融民 dual-sleeve | **STOP** (2026-09-09) | Dollar-split Stage A tip-clean but held-out&lt;0 · keep 公股 R1 · `FIN_PUB_PRIV_DUAL_SLEEVE_DECISION_PACK.md` |
| Soft-Frozen 4-sleeve (公/民 clips) | **STOP** (2026-09-09) | Stage A 48-challenger grid 0 coexist · live 3-sleeve KEEP · `SOFT_FROZEN_4SLEEVE_DECISION_PACK.md` |
| 民營 native within-sleeve | **OPTIMAL + OBSERVE OPERATING** (2026-09-09) | `PRIV_EQUAL`∥`PRIV_KD_MAY_Klt25_T15` month-end wired (asof 2026-09-09 alerts=0) · `FIN_PRIV_NATIVE_WITHIN_SLEEVE_DECISION_PACK.md` |
| 民營 native observe posture | **LOCKED KEEP OBSERVE** (2026-09-09) | Fixed month-end cadence + tip/structural watch + status ballot DRAFT · no live wire · `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md` |
| E22 payment-date restore | **DONE** (2026-09-10) | Soft-Frozen cash/stock pay blank **0%** restored post-#166; private residual 1/129 Yahoo-empty · `E22_PAYMENT_DATE_RESTORE_2026-09-10.md` · Soft-Frozen KEEP |
| E22 2891 cash-pay fill | **DONE** (2026-09-10) | Last private blank → `2010-08-23` via CNYES `#3283475` · private pay blank 0% · Soft-Frozen KEEP · `E22_2891_CASH_PAYMENT_FILL_2010-08-23.md` |
| E22 stock-web source sweep | **DONE** (2026-09-10) | Pay dates complete; residual `0050` announce×27 · `E22_STOCK_WEB_SOURCE_SWEEP_2026-09-10.md` |
| Indicator buy/sell charter + R1 screen | **OPEN / PAPER DONE** (2026-09-10) | Verdict **`COEXIST_NO_LIFT_VS_LIVE`** — BB/RSI/VOL coexist but **0 beat live KD_OPT** · keep live · `INDICATOR_BUY_SELL_CHARTER.md` · `INDICATOR_BUY_SELL_SCREEN_R1.md` |
| Indicator buy/sell R2 split (buy-low vs sell-high) | **PAPER DONE** (2026-09-10) | Separate tracks; coexist only live KD_OPT; **0 beat live** · best BUY=`BELOW_MA60` · best SELL=`RSI14_GT70` · `INDICATOR_BUY_SELL_SCREEN_R2_SPLIT.md` |
| Indicator combo catalog R3 (market TA × cross) | **PAPER DONE** (2026-09-10) | Finite catalog 16 low × 15 high + aggregates; **278 books**; coexist only live KD_OPT; **0 beat live** · `INDICATOR_COMBO_CATALOG_SCREEN_R3.md` |
| KD_OPT + indicator assist | **PAPER DONE** (2026-09-10) | Keep KD base; AND-low buy / high sell assists; **272 books**; verdict **`ASSIST_NO_LIFT`** · `KD_OPT_INDICATOR_ASSIST_SCREEN.md` |
| Soft assist + KD retune + TEL/sleeve | **PAPER DONE** (2026-09-10) | Soft weights + KD grid + TEL/sleeve; **422 books**; overall **`BEATS_LIVE`** (paper) — soft both / sleeve MA60 tip-clean lift; **TEL within-sleeve no lift**; live KD/TEL/Soft-Frozen **KEEP** until ACCEPT · `KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.md` |
| Soft-assist promote ballot | **EXECUTED OPEN OBSERVE** (2026-09-10) | Human `OPEN Soft-assist observe: SOFT_BOTH__BELOW_MA120__RSI6_GT80` · later superseded by K9+ OPEN · `SOFT_ASSIST_PROMOTE_BALLOT_EXECUTED_OPEN_OBSERVE.md` |
| Soft-assist K9 observe ballot | **EXECUTED OPEN OBSERVE** (2026-09-11) | Human sequence「照順序全做」→ `OPEN Soft-assist observe: SOFT_CHAMP_PLUS_K9_LT30_a10` · live KD KEEP · `SOFT_ASSIST_K9_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| Tip-safe FAST `COOL_c8_f50_d21` observe | **EXECUTED OPEN OBSERVE** (2026-09-25) | Human `開 COOL_c8_f50_d21 paper observe` · dual-paper OPERATING · later LIVE WIRED · Soft-Frozen KEEP · `COOL_C8_PROXY_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| Live COOL_c8 replace DH keep FUSE | **EXECUTED ACCEPT / LIVE WIRED** (2026-09-25) | Human `ACCEPT Live cutover: COOL_c8_f50_d21（ replace DH、keep FUSE）。` · `LIVE_COOL_EXPOSURE=True` · `LIVE_DH_EXPOSURE=False` · FUSE KEEP · stack FORBIDDEN · `LIVE_COOL_C8_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| Soft-assist SELL_a05 observe ballot | **EXECUTED OPEN OBSERVE** (2026-09-12) | Human `規則路徑OPEN` → `OPEN Soft-assist observe: SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` · live KD KEEP · no Soft×Sleeve fuse · `SOFT_SELL_A05_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| Soft-assist DL T2 seq Stage A | **PAPER DONE / RULE_PROMOTE_ONLY_NO_T2_LIFT** (2026-09-12) | numpy causal logret seq L10/L20 · flat linear/h8 + 1D-CNN · no torch in screen · DL promote>observe **0** · rule SELL_a05 still_best_vs_dl **True** · no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_T2_SEQ_STAGEA_SCREEN.md` |
| Soft-assist DL T2 torch Stage A | **PAPER DONE / RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT** (2026-09-12) | torch CPU TCN/LSTM causal logret L10/L20 · DL promote>observe **0** · rule SELL_a05 still_best_vs_dl **True** · no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_T2_TORCH_STAGEA_SCREEN.md` |
| Soft-assist DL T2 tiny causal Transformer Stage A | **PAPER DONE / RULE_PROMOTE_ONLY_NO_T2_XFMR_LIFT** (2026-09-12) | torch CPU tiny causal XFMR d8/h2/l1 · logret L10/L20 · DL promote>observe **0** · rule SELL_a05 still_best_vs_dl **True** · no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_T2_TRANSFORMER_STAGEA_SCREEN.md` |
| Soft-assist DL tip-MDD sell Stage A | **PAPER DONE / BEATS_LIVE_NO_OBSERVE_LIFT** (2026-09-12) | new label path-MDD/giveback · Soft sell role · tip-MDD promote>observe **0** · observe still_best_vs_tipmdd **True** · no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.md` |
| External strategy borrow Soft-sell Stage A | **PAPER DONE / BEATS_LIVE_NO_OBSERVE_LIFT** (2026-09-12) | public RSI70/BB/MFI Soft-sell motifs · ext promote>observe **0** · observe still_best_vs_ext **True** · no scrape-login / no live / no fuse · Soft∥Sleeve OPEN unchanged · `EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.md` |
| Month-end Soft∥Sleeve promote gate (2026-09-11 pack) | **KEEP_OBSERVE / KEEP_OBSERVE** (2026-09-12) | Soft `…__SELL_a05` held≈+0.101 alerts=0 · Sleeve `RSI14_a0225` held≈+0.099 alerts=0 · overlap corr≈+0.112 high_joint_dd=True · Gate H no combo · cutovers BLOCKED · `MONTH_END_PROMOTE_GATE_CHECKLIST.md` · `MONTH_END_PAPER_PACK.md` |
| Soft×Sleeve paper fuse Stage A screen | **PAPER DONE / FUSE_PROMOTE_SHAPED_BEATS_BOTH** (2026-09-12) | fuse promote-shaped **2** · beats both **1** · Soft-only held **0.101** · Sleeve-only held **0.099** · ops auto-fuse still FORBIDDEN · no live / no observe swap · `SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md` |
| Soft×Sleeve paper fuse Stage A charter | **PAPER DONE / FUSE_PROMOTE_SHAPED_BEATS_BOTH** (2026-09-12) | finite 8-book joint-actuator fuse · `FUSE_ADDITIVE` beats both independents on paper · ops auto-fuse still FORBIDDEN · no live / no observe swap · dedicated FUSE_ADDITIVE paper-observe ballot EXECUTED OPEN · `SOFT_SLEEVE_PAPER_FUSE_STAGEA_CHARTER.md` |
| FUSE_ADDITIVE observe ballot | **EXECUTED OPEN OBSERVE** (2026-09-12) | Human 開 FUSE_ADDITIVE 專用 ballot → `OPEN Soft×Sleeve fuse observe: FUSE_ADDITIVE` · paper only · Soft/Sleeve observes KEEP · no live · `FUSE_ADDITIVE_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| Live DH_dd06 + FUSE_ADDITIVE cutover | **EXECUTED ACCEPT / LIVE WIRED** (2026-09-13) → **DH replaced 2026-09-25** | Human `ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE` · later COOL replace DH keep FUSE · `LIVE_DH_FUSE_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` · `LIVE_COOL_C8_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| FUSE_ADDITIVE dual-paper observe | **OPERATING** (2026-09-12) | `LIVE_STACK` ∥ `FUSE_ADDITIVE` · held≈+0.164 · month-end wired · cutover **BLOCKED** · Soft∥Sleeve auto-fuse still FORBIDDEN · `FUSE_ADDITIVE_DUAL_PAPER_OBSERVE_OPEN.md` |
| Soft∥Sleeve ops auto-fuse agenda | **CLOSED** (2026-09-19) | Human `ACCEPT drop auto-fuse agenda` · Gate H **FORBIDDEN KEEP** · ≠ drop live `FUSE_ADDITIVE` · `ACCEPT_DROP_AUTO_FUSE_AGENDA.md` |
| E45 defend-window → handoff paper charter | **PAPER CHARTER OPEN** (2026-09-12) | Stage A **DONE** → `HANDOFF_PROMOTE_SHAPED` (`DH_dd06_vz1p0`) · stitch **FORBIDDEN** · `E45_DEFEND_HANDOFF_PAPER_CHARTER.md` · `E45_DEFEND_HANDOFF_STAGEA_SCREEN.md` |
| E45 defend-handoff observe ballot | **EXECUTED OPEN OBSERVE** (2026-09-13) | Human `E45 防衛窗 DH_dd06 開 observe` → `OPEN E45 defend-handoff observe: DH_dd06_vz1p0` · paper only · no stitch · `E45_DEFEND_HANDOFF_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| E45 defend-handoff dual-paper observe | **OPERATING** (2026-09-13) | `LIVE_STACK` ∥ `DH_dd06_vz1p0` · month-end wired · cutover **BLOCKED** · Soft/Sleeve/FUSE KEEP · `E45_DEFEND_HANDOFF_DUAL_PAPER_OBSERVE_OPEN.md` |
| Soft-assist dual-paper observe | **OPERATING** (2026-09-12) | `LIVE_KD_OPT` ∥ `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` · month-end wired · cutover **BLOCKED** · KEEP OBSERVE · rule-path OPEN · `SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPEN.md` |
| Soft-assist DL 4-track Stage A | **PAPER DONE / RULE_PROMOTE_ONLY_NO_DL_LIFT** (2026-09-12) | T1 reg/rank + T3 sell-role + T4 rep→gate · T2 charter-only (no torch) · DL promote>observe **0** · rule SELL_a05 still_best_vs_dl **True** · no live / no fuse / Soft∥Sleeve OPEN unchanged · `SOFT_DL_4TRACK_STAGEA_SCREEN.md` |
| Soft KD/BB sensitivity (soft OR + champ+) | **PAPER ARCHIVE / BEATS_CHAMPION** (2026-09-11) | Soft add-score only · **no hard AND** · beat-champ **1**=`SOFT_CHAMP_PLUS_K9_LT30_a10` · follow-on Soft-assist observe OPEN **#195** · `SOFT_KD_BB_SENSITIVITY_SCREEN.md` · `SOFT_KD_BB_SENSITIVITY_CHARTER.md` |
| Soft∥Sleeve borrow-promote Stage A | **PAPER DONE / HAS_PROMOTE_SHAPED_CANDIDATE** (2026-09-12) | Soft amplitude + Sleeve tip-MDD hygiene · Soft promote `…K9_a10__SELL_a05` / `…_a15` · Sleeve promote `SLEEVE_RSI14_LT30_a02` · **no observe swap / no fuse / no live wire** · `SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.md` · `SOFT_SLEEVE_BORROW_PROMOTE_CHARTER.md` |
| Soft∥Sleeve academic literature notes | **REFERENCE** (2026-09-12) | 2020–2024 papers mapped to Soft-assist∥Sleeve-tilt · no live / no fuse · `SOFT_SLEEVE_ACADEMIC_LITERATURE_NOTES.md` |
| Full-repo code review (post Soft-assist) | **DONE** (2026-09-10) | CI 3M capital + Soft-assist NAV fallback + MIX sell_scores fixed · live healthy · `PROJECT_CODE_REVIEW_2026-09-10.md` |
| Full-repo code review (2026-09-12) | **DONE** (2026-09-12) | Soft-Frozen checklist align + e21 asof/partial-fill + Soft/Sleeve alert scan + CI observe dirs + div fail-closed · live KEEP · `PROJECT_CODE_REVIEW_2026-09-12.md` |
| E22 dividend amount repair (parse-fail → refetch) | **OPERATING** (2026-09-12) | Live load repairs dirty amount cells once (FinMind/Yahoo/Yuanta) then fail-closed · no Soft-Frozen flip · `E22_DIVIDEND_AMOUNT_REPAIR_OPERATING.md` |
| Dry-powder drawdown sleeve | **STOP** (2026-09-10) | Stage A 37 books · verdict **`NO_LIFT`** · 0 tip-clean / 0 coexist · cash drag · live Soft-Frozen/KD/TEL **KEEP** · `DRY_POWDER_DRAWDOWN_SCREEN.md` |
| Sleeve-layer tilt charter | **EXECUTED OPEN OBSERVE** (2026-09-10) | Human `OPEN Sleeve-tilt observe: SLEEVE_BELOW_MA60_a01` · dual-paper OPERATING · cutover **BLOCKED** · Soft-assist independent · `SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPEN.md` |
| Sleeve RSI14_a0225 observe ballot | **EXECUTED OPEN OBSERVE** (2026-09-12) | Human `規則路徑OPEN` → `OPEN Sleeve-tilt observe: SLEEVE_RSI14_LT30_a0225` · live KEEP · Soft-assist independent · `SLEEVE_RSI14_A0225_OBSERVE_BALLOT_EXECUTED_OPEN.md` |
| Sleeve-layer tilt dual-paper observe | **OPERATING** (2026-09-12) | `LIVE_STACK` ∥ `SLEEVE_RSI14_LT30_a0225` · month-end wired · no live wire · rule-path OPEN · `SLEEVE_LAYER_TILT_OBSERVE_POSTURE.md` |
| ETF ex-calendar Stage A (0050 paper) | **STOP** (2026-09-11) | Stage A 13 books · verdict **`NEAR_NO_BEAT`** · 0 beat-live / 0 coexist / 0 beat-BH · tip-clean vs live 5 (=BH overlay) · live Soft-Frozen/KD/TEL **KEEP** · `ETF_EX_CALENDAR_SCREEN.md` |
| External borrow notes (Soft∥Sleeve∥month-end) | **REFERENCE** (2026-09-11) | Five practitioner notes mapped to Soft-assist / Sleeve-tilt observe + Gates A–I · **no live · no combo** · `EXTERNAL_BORROW_NOTES.md` |
| Research archive batch (human 請封存) | **ARCHIVED** (2026-09-13) | Seal A05 stitch reopen · E45 densify · DL · indicator hard · TEL challengers · structure fails · dry-powder · ETF calendar · FIN50/L4 agenda · KEEP Soft/Sleeve/FUSE/BLEND_025/priv observe · E45 defend paper-only next · `RESEARCH_ARCHIVE_BATCH_2026-09-13.md` · `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` |
| Kelly exposure Stage A charter + screen | **ARCHIVED** (2026-09-13 · human 請封存) | Stage A **`COEXIST_NO_LIFT`** · best `KELLY_LIVE_W252_k50` · **no observe / no live** · batch `RESEARCH_ARCHIVE_BATCH_KELLY_2026-09-13.md` · `KELLY_EXPOSURE_STAGEA_SCREEN.md` |
| E45_BLEND025 observe archive | **ARCHIVED** (2026-09-13 · human 封存 E45_BLEND025 observe) | `BLEND_E45_A25` tip YTD/1y ~11 pp PAUSE · removed from month-end/alert queue · FINCAP BLEND_025 **KEEP** · stitch still forbidden · `RESEARCH_ARCHIVE_BATCH_E45_BLEND025_2026-09-13.md` |
| Remainder | **ARCHIVE** | Evidence retained; no new expansion; not primary agenda |

Detail: `RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` · batch `RESEARCH_ARCHIVE_BATCH_2026-09-13.md` · FIN posture: `FIN_WITHIN_SLEEVE_OBSERVE_POSTURE.md` · 民營 posture: `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md`

### Register #6 sequential ballots

| Topic | Pack | Status |
|---|---|---|
| Odd-lot default → `E22_v2s_tw` | `ODD_LOT_PROMOTE_DECISION_PACK.md` | **DONE** — #73+#74 merged; DEFAULT=`E22_v2s_tw` |
| Tax / receivable formal books | `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `TAX_RECEIVABLE_CHARTER_DECISION_PACK.md` | **ACCEPT charter** — Stage B OPEN; no DEFAULT flip |
| E45 live stitch (A05) | `E45_A05_STITCH_DROPPED.md` · `E45_STITCH_ROLLBACK_ACCEPTED_DROP_A05.md` · dual-paper observe still OPEN | **DROPPED** 2026-09-09 — not pending second ACCEPT; live overlay = DH_dd06+FUSE |

## Re-open triggers (only then re-agenda)

| Topic | Trigger to re-open human decision |
|---|---|
| L4 cutover | ≥1 clean month-end (no YTD/1y `PAUSE_REVIEW`) + `CUTOVER_CHECKLIST_L4` all YES |
| FIN50 static cutover | Go-live verify **not** `NOT_READY_SEALED_CAGR` **and** Gate E clean — else stay rejected |
| BLEND_025 promote (FINCAP) | Sustained clean trailing on **FINCAP** BLEND_025 observe **and** cutover checklist drafted (`CUTOVER_CHECKLIST_BLEND025.md` — **drafted 2026-09-05**, still NOT AUTHORIZED) · **≠** archived E45_BLEND025 |
| Soft-Frozen flip | Explicit human cutover PR only (never pack/monitor green alone) |
| Soft-Frozen clip **search** (paper) | `SOFT_FROZEN_CLIP_SEARCH_DECISION_PACK.md` — **ACCEPT charter** ✓ Stage B done; Soft-Frozen KEEP; Class D flip still separate |
| FIN within-sleeve live cutover | `CUTOVER_CHECKLIST_FIN_WITHIN_SLEEVE.md` · **ACCEPTED KD_OPT 2026-09-09** · `FIN_WITHIN_SLEEVE_CUTOVER_ACCEPTED_KD_OPT.md` |
| Telecom within-sleeve alloc (paper) | Async **STOP** · pack ballot **EXECUTED KEEP TEL_EQUAL** · live EQUAL |
| 民營金控 / ALL12 universe expand | Stage A **STOP** · Soft-Frozen 公股 R1 KEEP · re-open only with tip-clean + held-out>0 |
| 金融公/金融民 dual-sleeve | Dollar-split Stage A **STOP** · Soft-Frozen 3-sleeve KEEP · 4-sleeve needs new charter |
| Soft-Frozen 4-sleeve FinPub/FinPriv clips | Stage A **STOP** · live 3-sleeve KEEP · Class D flip needs new positive evidence |
| 民營 native within-sleeve | **OBSERVE OPEN / KEEP OBSERVE** · `PRIV_EQUAL`∥`PRIV_KD_MAY_Klt25_T15` · no live wire · status ballot `FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md` · cutover `CUTOVER_CHECKLIST_FIN_PRIV_NATIVE.md` **BLOCKED** |
| Odd-lot default | Human **ACCEPT promote** on `ODD_LOT_PROMOTE_DECISION_PACK.md` + checklist all YES + **par inventory VERIFIED** (`PAR_VALUE_LOOKUP_CHARTER.md`) |
| Tax / receivable books | Human **ACCEPT charter** then sandbox evidence + later promote PR |
| E45 stitch | Charter **ACCEPT** ✓ + retired MDD narrative **RETIRED** ✓ + dual-paper observe **OPEN** ✓ — V1–V6 PASS; live stitch **rolled back** `DROP_E45_A05` (2026-09-09); any future live stitch needs a new dedicated ACCEPT |
| Indicator buy/sell (FIN) | R1–R3 + **KD hard assist** **DONE** (`ASSIST_NO_LIFT`) · soft KD/BB sensitivity **`BEATS_CHAMPION`** · Soft-assist observe on `SOFT_CHAMP_PLUS_K9_LT30_a10` · **no hard-AND reopen** · live KEEP · `SOFT_KD_BB_SENSITIVITY_SCREEN.md` |
| Research posture lock (rule-path first / DL new-mech only) | **LOCKED** (2026-09-12) | Priority observe Soft `…__SELL_a05` ∥ Sleeve `RSI14_a0225` · same Soft-buy MLP deepen **PARKED** · T2 Soft-buy boost families **DONE no lift** · further DL only via new charter (mechanism/label/role) · no live / no fuse · `RESEARCH_POSTURE_LOCK_RULEPATH_FIRST_DL_NEW_MECH.md` |
| Soft-assist / sleeve tilt promote | Soft-assist **OPEN OBSERVE** on `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` (2026-09-12 rule-path) · sleeve tilt **OPEN OBSERVE** on `SLEEVE_RSI14_LT30_a0225` (2026-09-12 rule-path) · both cutovers **BLOCKED** · **no auto-combo** · month-end paper gates `MONTH_END_PROMOTE_GATE_CHECKLIST.md` · `DUAL_OBSERVE_RULE_PATH_OPEN_EXECUTED.md` · posture lock `RESEARCH_POSTURE_LOCK_RULEPATH_FIRST_DL_NEW_MECH.md` (rule-path first; DL new-mech only) |
| Dry-powder drawdown sleeve | Stage A **STOP** (`NO_LIFT`) · live KEEP · re-open only with human-expanded grid · `DRY_POWDER_DRAWDOWN_SCREEN.md` |
| Sleeve-layer tilt | **OPEN OBSERVE EXECUTED** · dual-paper OPERATING · Soft-Frozen clips KEEP · cutover BLOCKED until ACCEPT · `SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPEN.md` |
| ETF ex-calendar (0050) | Stage A **STOP** (`NEAR_NO_BEAT`) · live KEEP · re-open only with human-expanded grid · `ETF_EX_CALENDAR_SCREEN.md` |
| E45_BLEND025 observe | **ARCHIVED** · reopen only with **new charter + human ballot** · `RESEARCH_ARCHIVE_BATCH_E45_BLEND025_2026-09-13.md` |
| Kelly exposure overlay | **ARCHIVED** · re-open only with **new charter + human ballot** · `RESEARCH_ARCHIVE_BATCH_KELLY_2026-09-13.md` |

## Non-decisions (ops wait — no strategy vote needed)

- **Full-review harden** (2026-09-20): code-review pack landed — entitlement cum shares · Y±1 **loader** (`load_calendar_window`) · **2025 CSV pinned** · **2027 wait** for TWSE publish · blank pay refuse · ledger orphan detect · NHI settle haircut sandbox · GHA allow flags · Soft-Frozen KEEP · tip history untouched  
- **Tax purpose** (human 2026-09-20「稅的目的是要有精準的現金流」): tax/withholding modeling = **cashflow precision** · year-end 所得稅 stays outside (ballot A) · pay-day NHI in sandbox `E22_v3_recv_pay_effdelay_nhi211` · `TAX_FOR_CASHFLOW_PURPOSE.md`  
- **Cashflow number priority** (human 2026-09-20「主要是要計算好現金流的數字」): keep A/B/C clocks separate — Exact T+1 paper · R4 settled · Stage-E cash+recv (TAX0) · SSOT `CASHFLOW_THREE_VIEWS.md` · report `cashflow_three_views_report.py` · **not** after-tax flat tax10/20 DEFAULT for cashflow  
- **NHI 補充保費** (human 2026-09-20「股利超過20000會需要繳補充保費」): 單次達 2 萬 → 2.11% 就源扣；**cashflow fidelity** vs Stage-E TAX0 gross · sandbox ready · **not** live · ≠ ballot A 所得稅 · `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md`  
- Tip Stage-E catch-up **CONFIRMED** 2026-09-21 (`last_date=2026-09-21`, books `E22_v3_recv_pay_effdelay`) — `TIP_CATCHUP_MONDAY_2026-09-21.md` · `POST_FORWARD_E22_VERIFY_RUNBOOK.md` · Gap6 tip-lag debt cleared · cashflow View C clock live  
- Grow live history toward ≥~60 sessions; `INDEX_DRIFT` under thin overlap is **ops note only** (ACCEPT Ops residual 全修 2026-09-19) — never a cutover vote  
- Calendar month-end pack re-run (L4 / FIN50 / FINCAP BLEND_025 / Soft / Sleeve / FUSE / priv / DH; **E45_BLEND025 skipped**) — default **KEEP OBSERVE**; cutover only via dedicated ACCEPT  
- Soft-assist×sleeve-tilt **ops auto-fuse agenda CLOSED** 2026-09-19 (`ACCEPT_DROP_AUTO_FUSE_AGENDA.md`) — Gate H **FORBIDDEN KEPT**; live `FUSE_ADDITIVE` KEEP; Soft∥Sleeve observes stay independent  
- Soft-assist×sleeve-tilt combo **not** authorized while both observe independently  
- Soft-Frozen cutover checklist is **ACCEPTED / LIVE WIRED** for FINBAND — do not re-read as DRAFTED (`CUTOVER_CHECKLIST_SOFT_FROZEN_CLIP.md`)
- Fill `MONTH_END_PROMOTE_GATE_CHECKLIST.md` after each Soft-assist / Sleeve-tilt pack (paper gates only · include Soft↔Sleeve overlap from `SOFT_SLEEVE_OBSERVE_OVERLAP.md` · **no live wire** · **no auto-combo**)
- Practitioner borrow map (reference only): `EXTERNAL_BORROW_NOTES.md` / `EXTERNAL_BORROW_NOTES.zh-TW.md` — does not open live or combo
- Ops residual 全修 **ACCEPTED** 2026-09-19 — dual-paper refresh + tip-lag Gap6 stamp + INDEX_DRIFT non-decision · `ACCEPT_OPS_RESIDUAL_FULL_FIX.md` · does **not** promote L4/FIN50/BLEND/Soft/Sleeve/priv/broker/tax Stage-B
- Deferred ops harden **ACCEPTED** 2026-09-25 — day-commit atomicity + tip-write gate EXECUTE; broker live-write **PREP only** (flags stay False); Stage-E full-history sandbox RESEARCH only · `ACCEPT_DEFERRED_OPS_HARDEN_2026-09-25.md`
- R2 MDD band floor **−14.5% ACCEPTED** 2026-09-25 — paper rescore only · Soft-Frozen KEEP · no live wire · `ACCEPT_R2_MDD_BAND_FLOOR_14_5_2026-09-25.md` · Stage A still `BAND_ONLY`
- R2/Stage-B MDD band floor **−15% ACCEPTED** 2026-09-25 — tip-safe FAST rescore **`TIPSAFE_STRETCH`** (`COOL_c8_f50_d21` · `GATE_g04_f50_d21`) · Soft-Frozen KEEP · `ACCEPT_R2_MDD_BAND_FLOOR_15_2026-09-25.md`
- Realism → 全自動化: Phase **0–1+2+3+5 LANDED** · Phase **4 scaffold** (synthetic R5) · Phase 2 tip **CONFIRMED** 2026-09-21 · Phase 6/7 ballot · `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md` · `PHASE_2_TIP_CATCHUP_CONFIRMED_2026-09-21.md`

## Claim policy

Live may not claim numeric CAGR/MDD target badges until a cutover PR merges.  
See `research/ops/LIVE_CLAIM_TARGET_POLICY.md`.

## How to run a future strategy update

End-to-end stage map (classify → charter → paper → observe → register gate → checklist → human cutover PR → post-QC):  
`research/ops/STRATEGY_UPDATE_STANDARD_PROCESS.md`.

This register remains the **only** place that re-opens live cutover agendas; the SOP does not add new verdicts.

## Label

`HUMAN_DECISION_REGISTER_2026-09-05`
