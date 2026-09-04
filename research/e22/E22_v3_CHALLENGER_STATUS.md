# Stage 5b — E22_v3 Paper Challenger Seeded

Date: **2026-09-04**  
Package: **`E22_v3_CASH_PAY_PAPER_CHALLENGER`**  
Class: **EXPERIMENTAL_PAPER** (not SOFT_FROZEN)

## What landed

| Surface | Path |
|---|---|
| Script | `scripts/e22_v3_challenger_forward_pipeline.py` |
| QC | `scripts/e22_v3_challenger_qc.py` |
| Ledgers | `forward/e22_v3_challenger/` |

- Seeded from live `forward/e22_v2/` on **2026-09-04** (8 pending orders carried)
- Credits on **`cash_payment_date`** (H1 rule)
- QC **PASS** at cutover seed
- **No** edits to `forward/e22_v2/` or `forward/e21/`

## Ops

```bash
PYTHONPATH=scripts python3 scripts/e22_v3_challenger_forward_pipeline.py
PYTHONPATH=scripts python3 scripts/e22_v3_challenger_qc.py
```

Official daily path remains:

```bash
PYTHONPATH=scripts python3 scripts/e22_v2_forward_pipeline.py
PYTHONPATH=scripts python3 scripts/e22_v2_qc.py
```

## Promotion

Requires explicit `APPROVE E22_v3_*` after paper evidence. H1 sandbox was only *interesting* with a thin util margin — do not treat seeding as approval.
