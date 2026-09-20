# Post-Forward E22 Evidence Verify Runbook


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Date: 2026-09-05 · **Phase 0–1 wired 2026-09-20**  
Status: **OPS AUTOMATED (weekday forward)** + manual re-verify workflow  
Soft-Frozen (at writing): **[0.50, 0.95]** · **live today [0.60, 0.90]** — never rewrite `forward/e21` history  
Related: `LIVE_E22_FIELD_EVIDENCE.md` · Gap6 KPI · `ops_alert_scan` · `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md`

## Automation (Phase 0–1)

Primary (unattended): `.github/workflows/v412f-forward-paper.yml` after R4 + QC runs:

```bash
python3 scripts/post_forward_e22_verify.py \
  --state-dir forward/e21 --require-r4 --skip-qc --fail-on critical
```

Also: `.github/workflows/post-forward-e22-verify.yml` (`workflow_dispatch` / `workflow_run` after forward success).

Fail-closed: R4 missing · QC FAIL · Gap6 `code_ok` false · CRITICAL alerts.  
**Does not fail:** tip lag (INFO) · DQ flags (report-only) · HIGH PAUSE_REVIEW.

## When to run (manual)

After the weekday GHA `v412f-forward-paper` (or equivalent) commits a new live session **and** ledger keys are expected to include E22 fields — or any time via:

```bash
python3 scripts/post_forward_e22_verify.py --require-r4 --fail-on critical
```

Today (weekend): **do not** invent evidence; wait for the bot (session_skip is OK).

## Steps (manual equivalent)

```bash
# 1) Live QC
python3 scripts/e21_qc.py --state-dir forward/e21

# 2) Gap6 fidelity (should clear LIVE_LEDGER_E22_FIELDS_MISSING when fields land)
python3 scripts/e22_gap6_fidelity_kpi.py

# 3) Completeness KPI (payment / ex-date)
python3 scripts/e22_data_quality_kpi.py

# 4) Alert scan (report-only)
python3 scripts/ops_alert_scan.py --report-only

# 5) Cashflow three views (A Exact T+1 · B R4 settled · C Stage-E cash+recv)
python3 scripts/cashflow_three_views_report.py --write

# Or one-shot (also attaches cashflow into POST_FORWARD_E22_VERIFY.*):
python3 scripts/post_forward_e22_verify.py --require-r4 --fail-on critical
```

Cashflow SSOT: `CASHFLOW_THREE_VIEWS.md` · Monday asserts: `TIP_CATCHUP_MONDAY_CHECKLIST.md`

## Pass criteria (evidence only — not cutover)

| Check | Expect |
|---|---|
| QC | PASS; Exact T+1 ok |
| Ledger keys | `e22_books_version` / `e22_manifest` present (names per pipeline) |
| Dividends artifact | append-only applied file exists / grows only on div days |
| Gap6 flag | `LIVE_LEDGER_E22_FIELDS_MISSING` absent or cleared |
| Soft-Frozen | unchanged vs note date **[0.50, 0.95]** (live today **[0.60, 0.90]**) |

## Fail / incomplete

| Symptom | Action |
|---|---|
| Fields still missing after weekday forward | File ops note; check forward pipeline write path — **do not** backfill history |
| QC FAIL | Escalate via alert scan CRITICAL path; no cutover talk |
| Temptation to rewrite history | Forbidden |

## After evidence lands

1. Update `LIVE_E22_FIELD_EVIDENCE.md` status → **EVIDENCE PRESENT** (date + commit).  
2. Leave Soft-Frozen KEEP.  
3. Do not treat evidence as L4/FIN50/BLEND cutover license.

## Label

`POST_FORWARD_E22_VERIFY_RUNBOOK`
