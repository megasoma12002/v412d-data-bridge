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

When live evidence lands, Gap6 flag `LIVE_LEDGER_E22_FIELDS_MISSING` should clear (INFO only while missing).
