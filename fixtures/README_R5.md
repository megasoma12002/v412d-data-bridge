# R5 custody fixtures (observe-only)

| File | Role |
|---|---|
| `r5_custody_synthetic.csv` | **CI / scaffold only** — byte-mirror of `forward/e21/settlement_cash_estimate.csv` fill rows so `twse_t2_broker_reconcile.py` returns `all_ok=true` |
| `r5_reconcile_smoke/` | Generated smoke pack (gitignored outputs OK to regenerate) |

## Real ops use

Replace `--custody` with a same-day (or settle-date) broker/custody export:

```bash
PYTHONPATH=scripts python3 scripts/twse_t2_broker_reconcile.py \
  --estimate forward/e21/settlement_cash_estimate.csv \
  --custody path/to/real_custody.csv \
  --asof YYYY-MM-DD \
  --out-dir forward/e21/broker_reconcile
```

Schema: `fill_id,settle_date,settlement_cash[,code,side]` **or** aggregate `settle_date,settlement_cash_net`.

**Does not** flip Soft-Frozen · fill_port · broker live-write · NAV.
