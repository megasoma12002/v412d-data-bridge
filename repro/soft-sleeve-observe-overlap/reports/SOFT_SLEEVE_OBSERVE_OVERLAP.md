# Soft-assist vs Sleeve-tilt Observe Overlap (paper only)

Generated: `2026-09-19T05:46:18.445904+00:00` · asof **2026-09-16**
Soft `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` ∥ Sleeve `SLEEVE_RSI14_LT30_a0225` · **no combo · no live wire**

## Held-out (2019+) snapshot

- Corr(excess): **0.795**
- Same-sign frac: **65.7%**
- Both-underperform frac: **33.1%**
- Joint DD day frac: **97.5%**
- Mean joint DD depth: **1.3%**
- Report flags: high_overlap=`True` · high_joint_dd=`True`

## Windows

| Window | N | Corr | Same-sign | Both− | Joint DD days | Mean joint DD | Soft rel MDD | Sleeve rel MDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `full` | 3358 | 0.749 | 63.2% | 31.7% | 87.9% | 1.0% | -5.4% | -3.3% |
| `heldout_2019_plus` | 1864 | 0.795 | 65.7% | 33.1% | 97.5% | 1.3% | -5.4% | -3.3% |
| `sealed_2023_plus` | 887 | 0.870 | 48.5% | 25.8% | 62.0% | 0.8% | -4.9% | -2.7% |
| `ytd` | 170 | 0.960 | 84.7% | 45.9% | 95.6% | 0.8% | -4.5% | -2.4% |
| `trailing_1y` | 242 | 0.940 | 67.4% | 36.8% | 79.8% | 0.8% | -4.5% | -2.4% |

## Reading

- Excess = challenger daily return − that track’s base daily return.
- High held-out corr / same-sign / joint DD → **independent observe still required**; do **not** auto-combo.
- This report never opens live cutover or a joint ACCEPT ballot.

## Non-actions

- No Soft-assist × Sleeve-tilt combo
- No live wire from this report

## Label

`SOFT_SLEEVE_OBSERVE_OVERLAP_2026-09-11__NO_COMBO__NO_LIVE`
