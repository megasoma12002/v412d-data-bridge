# Live E22 Field Evidence — Readiness Note

Date: 2026-09-05  
Status: **CODE READY / LIVE EVIDENCE PENDING**  
Soft-Frozen: **[0.50, 0.95] KEEP** — no history rewrite.

## Current live ledger

`forward/e21/portfolio_state.json` keys today: `cash`, `last_date`, `last_nav`, `positions`  
Gap #6 flag: **`LIVE_LEDGER_E22_FIELDS_MISSING`**

Missing (expected until next weekday forward commit):

- `e22_books_version`
- `e22_manifest`
- `dividends_applied.csv`

## Code path (already on main)

`scripts/e21_forward_pipeline.py` writes on each successful forward:

- `e22_books_version`
- `e22_manifest`
- append-only `dividends_applied.csv` (idempotent)

GHA: `.github/workflows/v412f-forward-paper.yml` (weekdays)

## What to do / not do

| Do | Do not |
|---|---|
| Wait for next weekday forward bot commit | Rewrite historical `forward/e21` rows |
| Re-run `e22_gap6_fidelity_kpi` after forward | Soft-Frozen flip |
| Keep QC smoke Gap6 summary (already wired) | Treat missing fields as Soft-Frozen defect |

## Cadence check

```bash
python3 scripts/e21_qc.py --state-dir forward/e21
python3 scripts/e22_gap6_fidelity_kpi.py
python3 scripts/ops_alert_scan.py --report-only
```

Full post-forward procedure: `research/ops/POST_FORWARD_E22_VERIFY_RUNBOOK.md`

When live evidence lands, Gap6 flag `LIVE_LEDGER_E22_FIELDS_MISSING` should clear (INFO only while missing).

## Refresh 2026-09-06 (ops research batch)

- Weekday: **Sunday** — no forward bot commit expected.
- Re-ran runbook checks: Exact T+1 QC **PASS**; Gap6 still **`LIVE_LEDGER_E22_FIELDS_MISSING`**.
- Status remains **CODE READY / LIVE EVIDENCE PENDING**.
- Soft-Frozen KEEP · no history rewrite · not a cutover signal.

## Refresh 2026-09-07 (human 「幫我驗E22／Gap6」)

- Full note: `E22_GAP6_VERIFY_2026-09-07.md`
- QC **PASS**; data-quality KPI **PASS**; Gap6 still blocked.
- Partial: `portfolio_state` has `e22_books_version` + `e22_manifest` (from 2026-09-06 push re-run).
- Still missing for Gap6 clear: **`nav.csv` column `e22_version`** (and optional `dividends_applied.csv`).
- Monday schedule forward **not yet landed** at verify time; manual dispatch **403**.
- Status remains **CODE READY / LIVE EVIDENCE PENDING** until weekday forward appends a nav row.

