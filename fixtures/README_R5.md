# R5 custody fixtures (observe-only)

| File | Role |
|---|---|
| `r5_custody_synthetic.csv` | **CI / scaffold only** — byte-mirror of `forward/e21/settlement_cash_estimate.csv` fill rows so `twse_t2_broker_reconcile.py` returns `all_ok=true` |
| `r5_custody_dropin.example.csv` | **Schema example** (safe to commit) — copy shape into `r5_custody_dropin.csv` |
| `uat_readonly_evidence.example.json` | Redacted UAT Login evidence shape — real file gitignored |
| `r5_reconcile_smoke/` | Generated smoke pack (CI) |
| `r5_reconcile_observe/` | Generated observe pack from `ops_r5_observe_auto.py` |

## Real ops use

```bash
# Drop-in path (PREP automation — still observe-only):
cp /path/to/broker_export.csv fixtures/r5_custody_dropin.csv
python3 scripts/ops_r5_observe_auto.py

# Or explicit:
python3 scripts/twse_t2_broker_reconcile.py \
  --estimate forward/e21/settlement_cash_estimate.csv \
  --custody path/to/real_custody.csv \
  --allow-external-custody \
  --asof YYYY-MM-DD \
  --out-dir fixtures/r5_reconcile_observe
```

Schema: `fill_id,settle_date,settlement_cash[,code,side]` **or** aggregate `settle_date,settlement_cash_net`.

**Does not** flip Soft-Frozen · fill_port · broker live-write · NAV.
