# E45 defend→handoff — Stage A screen

- screen_id: `E45_DEFEND_HANDOFF_STAGEA_SCREEN`
- charter: `E45_DEFEND_HANDOFF_PAPER_CHARTER`
- generated_at_utc: `2026-09-13T02:08:21Z`
- status: **DONE** | mode: PAPER_ONLY | live_wire: false | stitch_reopen: false | observe_open: false

## Verdict

- **`HANDOFF_PROMOTE_SHAPED`**
- best_variant_id: `DH_dd06_vz1p0`
- detail: `{"held_mdd_improve_pp": 4.3416, "held_cagr_giveback_pp": 1.1511, "n_shaped": 1}`

## Held-out / tip deltas vs BASE_LIVE_STACK

| variant | frac_def | held MDD↑ pp | held giveback pp | tip ytd MDD↑ | tip 1y MDD↑ |
|---|---:|---:|---:|---:|---:|
| `DH_dd06_vz1p0` | 0.027 | 4.3416 | 1.1511 | 0.031 | 0.031 |
| `DH_dd06_vz1p5` | 0.026 | 4.2184 | 1.0731 | -0.0016 | -0.0016 |
| `DH_dd08_vz1p0` | 0.009 | -0.2152 | 0.8972 | -0.1551 | -0.1551 |
| `DH_dd08_vz1p5` | 0.009 | -0.2152 | 0.8776 | -0.0917 | -0.0917 |
| `DH_dd10_vz1p0` | 0.009 | 2.5899 | 0.3689 | -0.3554 | -0.3554 |
| `DH_dd10_vz1p5` | 0.009 | 2.5899 | 0.3689 | -0.3554 | -0.3554 |

## Base windows (offense book)

```json
{
  "full": {
    "cagr": 0.140238,
    "max_drawdown": -0.217203,
    "n_days": 3356
  },
  "oof_2011_2018": {
    "cagr": 0.091635,
    "max_drawdown": -0.172795,
    "n_days": 1495
  },
  "validation_2019_2022": {
    "cagr": 0.120574,
    "max_drawdown": -0.217203,
    "n_days": 977
  },
  "sealed_2023_plus": {
    "cagr": 0.25573,
    "max_drawdown": -0.128078,
    "n_days": 884
  },
  "heldout_2019_plus": {
    "cagr": 0.183933,
    "max_drawdown": -0.217203,
    "n_days": 1861
  }
}
```

## Non-actions

- No Soft-Frozen / Soft / Sleeve / FUSE / E45 live wire
- No E45 stitch reopen / no undo DROP_E45_A05
- No observe OPEN from this Stage A alone
- Even HANDOFF_PROMOTE_SHAPED stays research until separate ballot

Artifact: `research/ops/E45_DEFEND_HANDOFF_STAGEA_SCREEN.md`
Repro: `repro/e45-defend-handoff-stagea/`
