# Month-End Data Freshness

Generated: `2026-09-19T05:46:51.968902+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen unchanged; no live wire; no auto-fetch.

- Fresh OK (hard): **True**
- Live market tip: **2026-09-16** (age **3** cal days)
- E22 events mtime age: **5** cal days · fetch_status **PASS** · kpi_ok **True**
- Shadow reconcile all_ok: **True** (age **0** cal days)

## Hard warnings

- None

## Soft warnings

- None

## Cadence vs fetch

- **Month-end pack** = paper monitors / recon / KPI (this snapshot).
- **Data re-fetch** (E22 etc.) = on-demand; not the pack default.
- **Formal month-end** should use `--refresh-ledgers` (rebuild observe NAVs).

See `research/ops/MONTH_END_PACK_FRESHNESS.md`.

