# Phase 4 scaffold landed — R5 reconcile wiring (synthetic)

Date: 2026-09-20  
Status: **SCAFFOLD LANDED** — Soft-Frozen KEEP · observe-only · **not** broker live-write  
Roadmap: `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md` Phase 4

## What this is

| Piece | Path |
|---|---|
| Synthetic custody | `fixtures/r5_custody_synthetic.csv` (mirror of R4 estimate — CI only) |
| README | `fixtures/README_R5.md` |
| Workflow | `.github/workflows/r5-broker-reconcile.yml` (`workflow_dispatch` + PR path) |
| Tests | `tests/test_r5_scaffold.py` |
| Monday tip checklist | `TIP_CATCHUP_MONDAY_CHECKLIST.md` (Phase 2 wait — concrete steps) |

## What this is NOT

- Real custody export (still human drop-in)  
- Auto broker submit / `API_WIRED` / Soft-Frozen flip  
- Closing Phase 4 fully (needs real fixture before ops rely on it)

## Operator

```bash
# CI / local smoke (synthetic):
python3 scripts/twse_t2_broker_reconcile.py \
  --estimate forward/e21/settlement_cash_estimate.csv \
  --custody fixtures/r5_custody_synthetic.csv \
  --asof 2026-09-16 \
  --out-dir fixtures/r5_reconcile_smoke

# Real custody later:
# --custody path/to/broker_export.csv --out-dir forward/e21/broker_reconcile
```

## Label

`PHASE_4_R5_SCAFFOLD_LANDED_2026-09-20`
