# Ops Status — One-Page Map

Date: 2026-09-25 (Deferred ops ACCEPT: day-commit atomicity · tip-write gate · broker PREP · Stage-E sandbox research)  
Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`  
Live Soft-Frozen clips: **F[0.60, 0.80] T[0.03, 0.35] E[0.00, 0.50]** (β densify ACCEPT 2026-09-25; was FINBAND F[0.60,0.90] E[0.00,0.35])  
**Cutover `#257`: CLOSED** (not merged) · `ACCEPT_CLOSE_CUTOVER_BUNDLE_257.md` · live KEEP 公股+FUSE+DH · reopen only new mechanism or sealed-gate  
**Deferred ops ACCEPT:** `ACCEPT_DEFERRED_OPS_HARDEN_2026-09-25.md` · broker PREP `ACCEPT_PREP_BROKER_LIVE_WRITE_2026-09-25.md` · Stage-E sandbox `ACCEPT_RESEARCH_STAGE_E_FULL_HISTORY_SANDBOX_2026-09-25.md`
新機制 N1–N3：**STOP / ladder exhausted** · `PRIV_MDD_NEW_MECH_N3_DECISION_PACK.md`  
新機制 V2 S1–S2：**STOP / ladder exhausted** · `PRIV_MDD_SENSOR_S2_DECISION_PACK.md`  
新機制 V3：**STOP** · `PRIV_MDD_M1_SCALE_V3_DECISION_PACK.md`（N1–N3+V2+V3 STOP）  
新機制 V4：**STOP**（A0 span>120 · A1 未開）· `PRIV_MDD_SEALED_EPISODE_V4_DECISION_PACK.md`（N1–N3+V2+V3+V4 STOP）  
新機制 V5：**STOP** · `PRIV_MDD_DH_PRIV_WINDOW_V5_DECISION_PACK.md`（N1–N3+V2+V3+V4+V5 STOP）  
新機制 V6：**STOP** · `PRIV_MDD_SHADOW_RELNAV_V6_DECISION_PACK.md`（N1–N3+V2+V3+V4+V5+V6 STOP）  
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
| Within-sleeve | FIN **`KD_OPT`** · TEL **`TEL_EQUAL`** |
| Overlay | **`FUSE_ADDITIVE` KEEP** + **`COOL_c8_f50_d21`** (`LIVE_FUSE_ADDITIVE` / `LIVE_COOL_EXPOSURE`; **DH replaced** 2026-09-25) |
| Offense CAGR paper | Stage A **`OFFENSE_CAGR_SOFT`** (Soft/Sleeve/FUSE densify under COOL · Soft-Frozen KEEP · no live) · `OFFENSE_CAGR_UNDER_COOL_STAGEA_SCREEN.md` |
| Legacy A05 stitch | **DROPPED** (`ACCEPT_2026-09-09_DROP_E45_A05`) — see `E45_A05_STITCH_DROPPED.md` |
| Daily job | `.github/workflows/v412f-forward-paper.yml` (weekdays; **holiday = no tip advance**) |
| QC smoke | `.github/workflows/e21-live-qc-smoke.yml` |
| QC | `scripts/e21_qc.py` → `forward/e21/qc_status.json` |

**Books dual clock (intentional — not tip lag):** tip / Stage-E DEFAULT = `E22_v3_recv_pay_effdelay`; FUSE offense full-history rebuild pins preserved cash-on-ex `E22_v2s_tw_effex` (`live_dh_fuse_cutover`). Do not “fix” tip lag by rewriting history.  
**Cash clocks (never merge):** A Exact T+1 `portfolio_state.cash` · B R4 `settled_cash_estimate` · C cash+`e22_receivables` — see `CASHFLOW_THREE_VIEWS.md`.  
**FinMind:** hourly quota + payment-date preserve — `FINMIND_API_QUOTA_AND_RETRY.md`.

**Not live (paper / archive):** independent Soft-assist · Sleeve-tilt · FINCAP BLEND_025 · FIN 民營 native · FIN_CAP_50 · L4 · E50-A · legacy E45 A05 blend stitch · Track A/B · E6/E9/E10 shadows.

## Paper sleeves (observe only)

| Sleeve | Status | Cutover |
|---|---|---|
| FIN_CAP_50 | Dual-paper OPERATING; YTD/1y PAUSE | **REJECT static cutover for now** (`NOT_READY_SEALED_CAGR`) — register #2 |
| L4_DD_PATH_08_50 | Held-out PASS; YTD **and** trailing_1y PAUSE_REVIEW (asof 2026-09-16) | **DEFER** cutover — register #4; checklist: `CUTOVER_CHECKLIST_L4.md` (hygiene sync `L4_HYGIENE_CHECKLIST_SYNC_2026-09-19.md`) |
| BLEND_025 | Dual-paper **OPERATING OBSERVE** | Sole sealed-CAGR successor (register #3); live **NOT READY** (#5); checklist prep: `CUTOVER_CHECKLIST_BLEND025.md` |
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
Realism automation gap-close (toward 全自動化): Phase **0–1 + 2 + 3 + 5 LANDED** — tip Stage-E confirm 2026-09-21 · verify · `ops_alert_scan` R4/tip-lag · `v412e22-dividend-events` weekday cron · roadmap `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md` · `PHASE_2_TIP_CATCHUP_CONFIRMED_2026-09-21.md`  
E45 A05 live-stitch (**DROPPED** 2026-09-09): Soft-Frozen CRITICAL class KEEP as paper; dual-paper observe **OPERATING**; A05 live wire **retired** (`E45_A05_STITCH_DROPPED.md`); live risk overlay was **DH_dd06** + **FUSE** (ACCEPT 2026-09-13) → **COOL_c8 replace DH, keep FUSE** (ACCEPT 2026-09-25). Tip books align ACCEPT 2026-09-19 → tip catch-up **CONFIRMED** 2026-09-21: `ACCEPT_TIP_BOOKS_ALIGN_V3.md` · `TIP_CATCHUP_MONDAY_2026-09-21.md`. Paper/live fill skip align: `ACCEPT_PAPER_LIVE_FILL_SKIP_ALIGN.md`. Ops residual 全修 ACCEPT 2026-09-19: `ACCEPT_OPS_RESIDUAL_FULL_FIX.md` (dual-paper refresh + tip-lag stamp + INDEX_DRIFT non-decision; no challenger/broker promote).
FIN50 sealed-CAGR charter: `research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md`  
FIN50 charter screen: `research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md`  
BLEND_025 paper-promote proposal: `research/gaps/FINCAP_BLEND025_DUAL_PAPER_PROMOTE_PROPOSAL.md`  
E45 blend-α=0.25 observe **OPERATING**: `research/ops/E45_BLEND025_OBSERVE_OPEN.md` · monitor `E45_BLEND025_MONTH_END_MONITOR.md`  
E45 paper research roadmap (1–7 status): `research/ops/E45_PAPER_RESEARCH_ROADMAP.md`  
E45 P1–P7 integrated analysis: `research/ops/E45_PAPER_P1_P7_INTEGRATED_ANALYSIS.md`
E45 sleeve-local deep-dive (post-P7): `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md`  
E45 sleeve-local observe **OPERATING**: `research/ops/E45_SLEEVE_LOCAL_OBSERVE_OPEN.md`（中文：`E45_SLEEVE_LOCAL_OBSERVE_OPEN.zh-TW.md`）  
E45 blend-α=0.05 observe **OPERATING**: `research/ops/E45_BLEND005_OBSERVE_OPEN.md` · monitor `research/gaps/E45_BLEND005_MONTH_END_MONITOR.md`  
  
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
民營 native dual-paper **OPERATING OBSERVE** (KEEP OBSERVE): `FIN_PRIV_NATIVE_DUAL_PAPER_OBSERVE_OPEN.md` · runbook `FIN_PRIV_NATIVE_MONTH_END_RUNBOOK.md` · posture `FIN_PRIV_NATIVE_OBSERVE_POSTURE.md` · status ballot DRAFT `FIN_PRIV_NATIVE_OBSERVE_STATUS_BALLOT_DRAFT.md` · cutover **BLOCKED** `CUTOVER_CHECKLIST_FIN_PRIV_NATIVE.md`  
 
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