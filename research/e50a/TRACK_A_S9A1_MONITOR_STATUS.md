# Track A — S9A1 Paper Monitor Status

Generated: `2026-09-04T19:28:20.189464+00:00`
Mode: `ARCHIVE_BOOTSTRAP`

**Paper/monitor only.** No live wire. No cut retune.

## Locked config

```json
{
  "challenger_id": "S9A1",
  "controller": "FREEZE_REB",
  "detector": "COMBO_VOL70_VAL03",
  "vol_roll_window": 252,
  "vol_roll_pctl": 0.7,
  "val_ic_min": 0.03,
  "hysteresis_on": 2,
  "hysteresis_off": 5,
  "top_k": 22,
  "rebalance_every": 42,
  "exit_multiple": 2.25,
  "neutralization": "NONE",
  "industry_cap": 5,
  "min_hold_cycles": 0,
  "liquidity_floor": 20000000.0,
  "replace_rank_gap": 5,
  "feature_set": "TECH2",
  "mode": "BREADTH_REGIME",
  "ridge_lambda": 1.0
}
```

Lock decision: `MIXED_HELDOUT`

**2026-09-05:** Track B S1 held-out failed → keep this monitor (`STOP_S1_HELDOUT_KEEP_TRACK_A`). No successor.

## KPI snapshot (S9A1)

| Window | CAGR | MDD | TO | Boot | Stress share | Stress mean excess |
|---|---:|---:|---:|---:|---:|---:|
| validation_2019_2022 | 23.45% | -29.79% | 2.38% | 0.6232 | 9.9% | 0.0007770435301989302 |
| sealed_2023_latest | 59.00% | -25.01% | 1.38% | 1.0 | 18.6% | 0.001094896017991568 |

## Monitor alerts

- Stress edge vs C4 (val): `0.0004297539348247233` (positive=True)
- Bootstrap soft warning (val &lt; 0.70): `True`
- Pause rule: If stress edge vs C4 negative for two consecutive review periods → pause paper overlay; do not retune.

## Artifacts

- `/workspace/repro/e50a-dual-track/track_a_s9a1_monitor/monitor_status.json`
- Runbook: `repro/e50a3r1-turnover-diagnosis-20260903/S9A1_PAPER_MONITOR_RUNBOOK.md`

