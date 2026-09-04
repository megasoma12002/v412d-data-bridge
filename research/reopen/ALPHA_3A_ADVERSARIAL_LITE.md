# Alpha 3A Adversarial-Lite

Score frozen: `z(oi_yoy) - z(amihud)`. No retune. Dev 2019–2024; sealed 2025+.

## Decision: `STOP_THIS_FEATURE_SET`

### Dev gates
```json
{
  "net40_mean_excess_gt_0": false,
  "net40_no_consec_neg_3y": false,
  "loyo_not_fragile": false,
  "drop_illiquid_net40_gt_m10bps": false,
  "industry_cap_net40_gt_m10bps": false
}
```

### Cost (dev)
| Round-trip | Mean excess |
|---|---:|
| 20 bps | -0.102% |
| 40 bps | -0.148% |
| 60 bps | -0.193% |

Mean one-way turnover: **22.7%**/month

### Sealed held-out (2025+)
Mean excess net 40 bps: **1.408%**

### Promotion
**False** — even on PASS, needs separate approval for paper sleeve.

Artifact: `repro/alpha3a-adversarial-lite-20260904/adversarial_lite_report.json`
