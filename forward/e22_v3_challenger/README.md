# E22_v3 Paper Challenger (EXPERIMENTAL)

**Version:** `E22_v3_CASH_PAY_PAPER_CHALLENGER`  
**Status:** `EXPERIMENTAL_PAPER` (seeded 2026-09-04) — **not** official

- Challenger script: `scripts/e22_v3_challenger_forward_pipeline.py`
- State: `forward/e22_v3_challenger/`
- Mechanism: Exact T+1 + cash dividend credit on `cash_payment_date`
- Cutover seed date: `2026-09-04` (inherited from E22_v2; **no** dividend backfill)
- Official path unchanged: `forward/e22_v2/` (ex-date)

## Daily paper run

```bash
python scripts/e22_v3_challenger_forward_pipeline.py
python scripts/e22_v3_challenger_qc.py
```
