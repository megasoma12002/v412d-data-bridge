# Stage 4 — Revenue YoY + CFO YoY

Score: `z(rev_yoy_12m) + z(cfo_yoy)` (not OI/Amihud).

## Decision: `STOP_STAGE4_FEATURE_SET`

### Dev gates (2019–2024)
```json
{
  "net40_mean_excess_gt_0": true,
  "net40_no_consec_neg_3y": false,
  "loyo_not_fragile": false,
  "industry_cap_net40_gt_m10bps": true
}
```

| Cost | Mean excess |
|---|---:|
| 20 bps | 0.097% |
| 40 bps | 0.017% |
| 60 bps | -0.063% |

Sealed 2025+ net40: **0.297%**

No promotion. Artifact: `repro/stage4-rev-cfo-20260904/stage4_report.json`
