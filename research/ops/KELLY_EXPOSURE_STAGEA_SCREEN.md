# Kelly exposure — Stage A screen

- screen_id: `KELLY_EXPOSURE_STAGEA_SCREEN`
- charter: `KELLY_EXPOSURE_STAGEA_CHARTER`
- generated_at_utc: `2026-09-13T07:17:45Z`
- status: **DONE** · mode: PAPER_ONLY · live_wire: false · observe_open: false

## Verdict

- **`COEXIST_NO_LIFT`**
- best_variant_id (primary EDGE_LIVE_ROLL only): `KELLY_LIVE_W252_k50`
- detail: `{"held_score": -2.2079, "n_coexist": 1}`

Promote gate uses **EDGE_LIVE_ROLL** only. `EDGE_0050_ROLL` is sensitivity / report-only.

## Primary (EDGE_LIVE_ROLL)

| variant | kappa | W | tip_clean | class | held score | held MDD up | tip ytd MDD up | tip 1y MDD up | mean e | frac@bound |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| `KELLY_LIVE_W63_k25` | 0.25 | 63 | False | `ESTIMATE_UNSTABLE` | 4.4007 | 6.9467 | 1.2168 | 1.2168 | 0.840607 | 0.950238 |
| `KELLY_LIVE_W63_k50` | 0.50 | 63 | False | `ESTIMATE_UNSTABLE` | 4.54645 | 6.945 | 0.7319 | 0.7319 | 0.859803 | 0.976162 |
| `KELLY_LIVE_W126_k25` | 0.25 | 126 | False | `ESTIMATE_UNSTABLE` | 0.2193 | 3.1071 | 2.7795 | 2.7795 | 0.867102 | 0.925805 |
| `KELLY_LIVE_W126_k50` | 0.50 | 126 | False | `ESTIMATE_UNSTABLE` | 0.3759 | 2.7747 | 3.2023 | 3.2023 | 0.891696 | 0.973182 |
| `KELLY_LIVE_W252_k25` | 0.25 | 252 | False | `ESTIMATE_UNSTABLE` | -2.23375 | 0.1893 | 2.0349 | 2.0349 | 0.858646 | 0.917163 |
| `KELLY_LIVE_W252_k50` | 0.50 | 252 | True | `COEXIST_NO_LIFT` | -2.2079 | -0.7465 | -0.447 | -0.447 | 0.89339 | 0.964839 |

## Sensitivity (EDGE_0050_ROLL, report-only)

| variant | kappa | W | tip_clean | class | held score | mean e | frac@bound |
|---|---:|---:|---|---|---:|---:|---:|
| `KELLY_0050_W63_k25` | 0.25 | 63 | False | `ESTIMATE_UNSTABLE` | 6.8755 | 0.815671 | 0.920143 |
| `KELLY_0050_W63_k50` | 0.50 | 63 | False | `ESTIMATE_UNSTABLE` | 7.40675 | 0.843263 | 0.967819 |
| `KELLY_0050_W126_k25` | 0.25 | 126 | False | `ESTIMATE_UNSTABLE` | 0.3273 | 0.825706 | 0.913588 |
| `KELLY_0050_W126_k50` | 0.50 | 126 | False | `ESTIMATE_UNSTABLE` | 0.0174 | 0.858043 | 0.956496 |
| `KELLY_0050_W252_k25` | 0.25 | 252 | False | `ESTIMATE_UNSTABLE` | -2.02805 | 0.815998 | 0.926996 |
| `KELLY_0050_W252_k50` | 0.50 | 252 | False | `ESTIMATE_UNSTABLE` | -1.60485 | 0.850077 | 0.94994 |

## Base windows (LIVE_STACK)

```json
{
  "full": {
    "cagr": 0.140238,
    "max_drawdown": -0.217203,
    "n_days": 3356
  },
  "heldout_2019_plus": {
    "cagr": 0.183933,
    "max_drawdown": -0.217203,
    "n_days": 1861
  },
  "sealed_2023_plus": {
    "cagr": 0.25573,
    "max_drawdown": -0.128078,
    "n_days": 884
  }
}
```

## Non-actions

- No Soft-Frozen clip flip
- No live KD_OPT / TEL_EQUAL / Soft / Sleeve / FUSE / BLEND / priv / E45 / DH wire
- No Soft||Sleeve ops auto-fuse
- No E45 stitch reopen / no undo DROP_E45_A05
- No Stage A fusion with DH/Soft/Sleeve/FUSE
- No full Kelly / no f_hi>1 / no shorts
- Even KELLY_PROMOTE_SHAPED -> paper observe ballot only; never live from this screen

Artifact: `research/ops/KELLY_EXPOSURE_STAGEA_SCREEN.md`
Repro: `repro/kelly-exposure-stagea/`

## Next authorized action

- KEEP research note; no observe unless human expands charter.

## Archive seal (2026-09-13)

Human **請封存**. Batch: `RESEARCH_ARCHIVE_BATCH_KELLY_2026-09-13.md`.  
No observe · no live · reopen only with new charter + human ballot.
