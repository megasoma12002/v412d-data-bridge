# E22_v2 Official Forward

**Version:** `E22_v2_CASH_EX_OFFICIAL_PATH`  
**Status:** `SOFT_FROZEN` (approved 2026-09-04)

- Official script: `scripts/e22_v2_forward_pipeline.py`
- State: `forward/e22_v2/`
- Mechanism: Exact T+1 + cash dividend credit on `cash_ex_date`
- Cutover seed date: `2026-09-03` (inherited from E21; **no** dividend backfill)
- Preserved forever: `forward/e21/`

## Daily run

```bash
python scripts/e22_v2_forward_pipeline.py
python scripts/e22_v2_qc.py
```
