# R5 observe — synthetic run evidence (2026-09-27)

Status: **OBSERVE_OK_SYNTHETIC** · Soft-Frozen **KEEP** · no broker live-write  
Calendar: tip asof still `2026-09-24` · next TWSE session **2026-09-29** (9/25 中秋 · 9/28 教師節 closed)

## What ran

```bash
python3 scripts/ops_r5_observe_auto.py --asof 2026-09-24
python3 scripts/ops_broker_r5_oco_prep_status.py --run-r5 --fail-if-gates-open
```

| Field | Value |
|---|---|
| custody | `fixtures/r5_custody_synthetic.csv` (CI mirror — **not** real broker export) |
| estimate | `forward/e21/settlement_cash_estimate.csv` |
| all_ok | **true** (synthetic) |
| out | `fixtures/r5_reconcile_observe/` (gitignored) |
| execute_blocked | true |

## Real custody still required

Drop a same-day / settle-day export:

```bash
cp /path/to/broker_export.csv fixtures/r5_custody_dropin.csv
# schema: see fixtures/r5_custody_dropin.example.csv
python3 scripts/ops_r5_observe_auto.py --asof 2026-09-29   # after tip advances
```

Do **not** merge R5 into Exact T+1 NAV. Soft-Frozen KEEP.

Label: `R5_OBSERVE_SYNTHETIC_2026-09-27__WAITING_DROPIN`
