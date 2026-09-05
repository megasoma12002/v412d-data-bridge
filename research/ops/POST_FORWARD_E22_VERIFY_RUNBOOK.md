# Post-Forward E22 Evidence Verify Runbook

Date: 2026-09-05  
Status: **OPS PREP** — run after next **weekday** live forward  
Soft-Frozen: **[0.50, 0.95] KEEP** — never rewrite `forward/e21` history  
Related: `LIVE_E22_FIELD_EVIDENCE.md` · Gap6 KPI · `ops_alert_scan`

## When to run

After the weekday GHA `v412f-forward-paper` (or equivalent) commits a new live session **and** ledger keys are expected to include E22 fields.

Today (weekend): **do not** invent evidence; wait for the bot.

## Steps

```bash
# 1) Live QC
python3 scripts/e21_qc.py --state-dir forward/e21

# 2) Gap6 fidelity (should clear LIVE_LEDGER_E22_FIELDS_MISSING when fields land)
python3 scripts/e22_gap6_fidelity_kpi.py

# 3) Completeness KPI (payment / ex-date)
python3 scripts/e22_data_quality_kpi.py

# 4) Alert scan (report-only)
python3 scripts/ops_alert_scan.py --report-only
```

## Pass criteria (evidence only — not cutover)

| Check | Expect |
|---|---|
| QC | PASS; Exact T+1 ok |
| Ledger keys | `e22_books_version` / `e22_manifest` present (names per pipeline) |
| Dividends artifact | append-only applied file exists / grows only on div days |
| Gap6 flag | `LIVE_LEDGER_E22_FIELDS_MISSING` absent or cleared |
| Soft-Frozen | unchanged **[0.50, 0.95]** |

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
