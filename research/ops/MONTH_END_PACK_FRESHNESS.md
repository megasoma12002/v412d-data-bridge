# Month-end pack — freshness & how to use it

Date: 2026-09-14  
Status: **OPS guidance** — Soft-Frozen unchanged; no live wire; no auto cutover  
Authority: `OPS_STATUS.md` · pack `scripts/ops_month_end_paper_pack.py` · freshness `scripts/ops_month_end_data_freshness.py`

## What month-end is (and is not)

| Is | Is not |
|---|---|
| Paper / ops **cadence pack** (monitors, recon, KPIs) | A new “monthly data re-iteration” product |
| Optional **ledger rebuild** (`--refresh-ledgers`) | Soft-Frozen flip or challenger live-wire |
| **Freshness snapshot** (market tip / E22 age / shadow) | Automatic FinMind E22 re-fetch |
| Cron on the 1st (UTC) as a formal reminder | Replacement for weekday forward job |

## Recommended usage

```bash
# Fast path — monitors only (dev / mid-month check)
python3 scripts/ops_month_end_paper_pack.py

# Formal month-end — rebuild observe ledgers + fail on hard stale
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers --fail-on-stale

# Freshness only
python3 scripts/ops_month_end_data_freshness.py
python3 scripts/ops_month_end_data_freshness.py --fail-on-stale
```

GitHub Actions `ops-month-end-paper-pack`:
- **schedule (1st)**: always `--refresh-ledgers --fail-on-stale`
- **workflow_dispatch**: defaults `refresh_ledgers=true`, `fail_on_stale=true` (uncheck for fast path)

## Freshness signals

| Signal | Hard fail (`fresh_ok`) | Soft warn |
|---|---|---|
| `forward/e21/live_market.csv` tip age > 7 cal days (or missing) | Yes | — |
| `data/dividend_events/e22_dividend_events.csv` mtime > 45 cal days (or missing) | Yes | — |
| Shadow reconcile `all_ok=false` (if artifact present) | Yes | — |
| Shadow missing / shadow age / E22 KPI flags / non-PASS fetch_status | — | Yes |

Artifacts: `research/ops/MONTH_END_DATA_FRESHNESS.{md,json}` (also embedded in `MONTH_END_PAPER_PACK.*`).

## If E22 looks stale

Pack **does not** fetch dividends. On-demand only:

- Workflow: `v412e22-dividend-events`
- Then re-run pack (or freshness alone)

## Hard rules

- No Soft-Frozen flip from pack green / freshness green
- Dual-paper / held-out PASS ≠ cutover license
- Never rewrite `forward/e21` history from this pack
- No live Soft∥Sleeve independent auto-fuse

## Label

`MONTH_END_PACK_FRESHNESS_2026-09-14__USE_EXISTING_PACK__NO_PARALLEL_ITERATOR`
