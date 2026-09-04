# Industry PIT Challenger (free / sparse)

Generated: 2026-09-04T13:44:09.924306+00:00

## What this is
- **Event table** of TWSE/TPEx industry reclassifications assembled from public
  announcements / reputable media reprints.
- **Sparse Wayback ISIN snapshots** (`C_public.jsp?strMode=1`) for a few years.
- **Event-touched sparse PIT** for tickers that appear in the event table only.

## What this is NOT
- Not TWT58U daily archive.
- Not a full-universe historical industry map.
- Not a silent patch to E50-A0 / A0 security_master.

## Files
| File | Meaning |
|---|---|
| `industry_reclass_events.csv` | old→new on effective_date |
| `snapshot_isin_class_main_listed.csv` | live ISIN named industries (listed) |
| `snapshot_twse_current.csv` | TWSE OpenAPI codes + ISIN names |
| `industry_code_map.csv` | 2-digit code → industry name |
| `wayback_isin_snapshots/` | sparse archived ISIN maps (partial universe) |
| `wayback_isin_sparse_all.csv` | combined Wayback rows |
| `event_touched_sparse_pit.csv` | reconstructed as-of for event tickers only |
| `fetch_status.json` | machine status |

## Still required for true industry-neutral alpha
1. Buy/archive TWSE E-Shop **TWT58U** (from 2019-12-23), or
2. TEJ company-attribute PIT (from ~2013), with lineage QC vs TWSE codes.
