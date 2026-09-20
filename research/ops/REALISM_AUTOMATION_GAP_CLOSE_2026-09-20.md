# Realism automation — gap-close roadmap (toward 全自動化)

Date: 2026-09-20  
Status: **RESEARCH / OPS ROADMAP** — Soft-Frozen **KEEP** · no alpha cutover · no broker live-write · no tax DEFAULT promote  
Audience: close execution/accounting **真實性** gaps so later full automation is fail-closed and ballot-gated  
Parent SSOT: `OPS_STATUS.md` · `HUMAN_DECISION_REGISTER.md` · tip-align `ACCEPT_TIP_BOOKS_ALIGN_V3.md` · ops residual `ACCEPT_OPS_RESIDUAL_FULL_FIX.md`

## Goal

Make the live accounting loop **self-running on open sessions** (forward → R4 → verify → alerts → dividend refresh), with **human ballots only** where money/compliance/DEFAULT flips are involved.  
「全自動化」here means **unattended observe + evidence**, not auto Soft-Frozen / alpha / SendAlgo.

## What already runs unattended

| Cadence | Workflow / surface | Covers |
|---|---|---|
| Weekday cron `30 8 * * 1-5` | `.github/workflows/v412f-forward-paper.yml` | Session gate → data → E21 forward → **R4** T+2 estimate → `e21_qc` → commit `forward/` |
| Month-start cron | `.github/workflows/ops-month-end-paper-pack.yml` | Dual-paper refresh + Gap6/DQ/recon/alerts (`--fail-on-stale`) |
| PR/push | `.github/workflows/e21-live-qc-smoke.yml` | `e21_qc` + Gap6 (`code_ok`) + `ops_alert_scan --fail-on critical` |
| Manual / owner issue | `.github/workflows/v412e22-dividend-events.yml` | Dividend event ledger refresh — **no cron** |

Fail-closed already in code: session skip · Soft-Frozen `e21_session.lock` · canonical path forced `paper` fill · `broker_live_write_accepted=False` · Yuanta `API_WIRED=False`.

**Tip snapshot (research time):** `forward/e21` asof `2026-09-16`, tip books `E22_v2s_tw_effex` while code DEFAULT = `E22_v3_recv_pay_effdelay` (authorized tip lag until next weekday forward).

---

## Gap matrix (真實性 → automation)

| ID | Gap | Blocker type | Auto-close design | Still needs human |
|---|---|---|---|---|
| **G1** | Tip → Stage-E DEFAULT | weekend / calendar | Next green `v412f-forward-paper` already writes `LIVE.e22_books_version` | No (ACCEPT tip-align done) |
| **G2** | Post-forward verify runbook | ops-manual | Chain QC+Gap6+**DQ**+alert scan after non-skip forward; commit/upload artifacts | Policy only (evidence ≠ cutover) |
| **G3** | R4 week-1 spot-check | ops-manual (emit done) | Assert CSV/JSON schema in forward job; alert missing/empty | Never promote estimate into NAV |
| **G4** | R5 custody reconcile | missing-data | Fixture drop → `twse_t2_broker_reconcile.py` workflow (observe) | Custody export + later broker ballot |
| **G5** | Tax Stage-B DEFAULT | human-ballot + incomplete resident rule | Automate sealed compare + Gap6 tax KPI only | Resident appendix + promote ACCEPT |
| **G6** | Broker live-write | ballot + `API_WIRED=False` | Dry-run / fixture-ack off canonical path | Dedicated ACCEPT + env + safety |
| **G7** | `dividends_applied.csv` / tax KPI | missing live apply rows | Append-only on div days; auto Gap6 tax section when n>0 | No backfill of history |
| **G8** | Dividend events cron | ops-manual | Add schedule to `v412e22-dividend-events.yml` (fetch-only) | Owner issue still OK as override |

### Wrong auto-promote risks (must stay fail-closed)

- Rewrite historical `nav.csv` / weekend invent tip  
- Treat Gap6/R4 green as L4/FIN50/BLEND/Soft flip  
- Merge T+2 `settled_cash_estimate` into Exact T+1 `portfolio_state.cash`  
- Env-only or GHA secret alone enabling SendAlgo  
- Auto DEFAULT → `tax10`/`tax20` while `promote_ready=false`

---

## Phased roadmap (implement later; this note does not ship the wires)

### Phase 0 — Observe harden (no ballot) — **LANDED 2026-09-20**

1. In `v412f-forward-paper.yml`, after R4: assert estimate CSV/JSON exist + summary keys when `skip!=true`.  
2. Optional upload of Gap6/DQ even if tip still lags (INFO, not fail).  
Scripts: `twse_t2_settlement_estimate.py`, `e21_qc.py`, `e22_gap6_fidelity_kpi.py`, **`post_forward_e22_verify.py`**.

### Phase 1 — Post-forward verify automation — **LANDED 2026-09-20**

1. Chained in `v412f-forward-paper.yml` after QC: `post_forward_e22_verify.py --require-r4 --skip-qc --fail-on critical`.  
2. Standalone `.github/workflows/post-forward-e22-verify.yml` (`workflow_dispatch` / `workflow_run` after forward success).  
3. Commits/uploads `POST_FORWARD_E22_VERIFY.*` + Gap6/DQ/`OPS_ALERTS.*`.  
4. Fail: CRITICAL / Gap6 `code_ok`. Allow: tip≠DEFAULT (INFO) · DQ flags · HIGH PAUSE.  
Authority: `POST_FORWARD_E22_VERIFY_RUNBOOK.md`.

### Phase 2 — Tip catch-up confirmation

1. After first weekday session with tip==`E22_v3_recv_pay_effdelay`: regenerate Gap6; clear tip-lag debt wording.  
2. Optional alert rule: tip≠DEFAULT for N open sessions after tip-align ACCEPT → HIGH ops (not CRITICAL).  
3. Still: no history rewrite.

### Phase 3 — R4 continuous observe

1. Encode `R4_R5_WEEK1_OBSERVE_CHECKLIST.md` spot fields as JSON schema checks in `ops_alert_scan.py` (missing estimate / empty unsettled on active week).  
2. Label every alert: liquidity view **≠** NAV.

### Phase 4 — R5 when fixture exists

1. Workflow `r5-broker-reconcile.yml` (manual / path to private custody artifact).  
2. CLI: `twse_t2_broker_reconcile.py --estimate forward/e21/settlement_cash_estimate.csv --custody … --out-dir forward/e21/broker_reconcile`.  
3. Observe-only exit; never flip `fill_port` or Soft-Frozen.

### Phase 5 — Dividend data cadence

1. Add weekday/weekly cron to `v412e22-dividend-events.yml` (fetch `data/dividend_events/` only).  
2. When live produces `dividends_applied.csv`: Gap6 tax sensitivity becomes report-only automatically.  
3. Optional: alert if positions in ex→pay window but apply row missing (after tip on Stage-E).

### Phase 6 — Tax Stage-B (automation stops at promote_ready)

1. Nightly or month-end: `e22_v3_stage_b_sealed_compare.py` + sandbox metrics.  
2. Gate stays human: complete `E22_V3_WITHHOLDING_RESIDENT_NOTE.md` (residency, treaty, timing, refunds) → `promote_ready=true` → dedicated ACCEPT.  
3. R4/R5 week-1 rule: **at most one** of {tax formal promote, broker live} per week.

### Phase 7 — Broker path (still gated)

1. Off-canonical dry_run / fixture-ack only.  
2. Live write requires: ACCEPT PR + `broker_live_write_accepted` + ballot file + `E21_BROKER_WRITE_LIVE` + `API_WIRED` + green R5 + locks.  
3. Canonical `forward/e21` stays paper until that ballot.

---

## Suggested concrete surfaces (future PRs)

| Surface | Change |
|---|---|
| `.github/workflows/v412f-forward-paper.yml` | Phase 0 assert + optional Phase 1 verify steps before/after commit |
| `.github/workflows/post-forward-e22-verify.yml` | `workflow_run` after forward success (cleaner separation) |
| `.github/workflows/v412e22-dividend-events.yml` | Add `schedule:` cron (Phase 5) |
| `.github/workflows/r5-broker-reconcile.yml` | Manual + fixture (Phase 4) |
| `scripts/ops_alert_scan.py` | tip-lag INFO/HIGH · missing R4 artifact · R5 mismatch (policy careful) |
| `scripts/e22_gap6_fidelity_kpi.py` | Already flags tip lag; keep as SSOT stamp |

Machine index: `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.json`

---

## Explicit non-goals

- Soft-Frozen clip flip / FUSE·DH retune  
- L4 / FIN50 / BLEND_025 / Soft-assist / Sleeve / 民營 / E45 stitch promote  
- Ops auto-fuse (Gate H FORBIDDEN; agenda CLOSED)  
- Auto tax DEFAULT or auto broker SendAlgo  
- Merging Exact T+1 paper cash with custody T+2 into one NAV clock  
- Weekend invent / rewrite `forward/e21` history

---

## Operator “until Phase 1 lands”

```bash
# After next weekday forward (tip catch-up):
python3 scripts/e21_qc.py --state-dir forward/e21
python3 scripts/e22_gap6_fidelity_kpi.py
python3 scripts/e22_data_quality_kpi.py
python3 scripts/ops_alert_scan.py --report-only
# see POST_FORWARD_E22_VERIFY_RUNBOOK.md
```

## Label

`REALISM_AUTOMATION_GAP_CLOSE_2026-09-20__OBSERVE_FIRST_BALLOT_GATED`
