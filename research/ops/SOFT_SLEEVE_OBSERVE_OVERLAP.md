# Soft-assist vs Sleeve-tilt Observe Overlap (paper only)

Generated: `2026-09-11T16:44:29.574059+00:00` · asof **2026-09-10**
Soft `SOFT_CHAMP_PLUS_K9_LT30_a10` ∥ Sleeve `SLEEVE_BELOW_MA60_a01` · **no combo · no live wire**

## Held-out (2019+) snapshot

- Corr(excess): **-0.025**
- Same-sign frac: **55.0%**
- Both-underperform frac: **26.5%**
- Joint DD day frac: **33.1%**
- Mean joint DD depth: **0.1%**
- Report flags: high_overlap=`False` · high_joint_dd=`False`

## Windows

| Window | N | Corr | Same-sign | Both− | Joint DD days | Mean joint DD | Soft rel MDD | Sleeve rel MDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `full` | 3354 | -0.010 | 50.5% | 24.2% | 22.1% | 0.1% | -1.2% | -0.2% |
| `heldout_2019_plus` | 1860 | -0.025 | 55.0% | 26.5% | 33.1% | 0.1% | -0.4% | -0.2% |
| `sealed_2023_plus` | 883 | -0.091 | 60.1% | 28.9% | 18.6% | 0.1% | -0.4% | -0.2% |
| `ytd` | 166 | -0.841 | 33.7% | 13.9% | 27.2% | 0.1% | -0.3% | -0.2% |
| `trailing_1y` | 242 | -0.715 | 43.0% | 19.8% | 27.2% | 0.1% | -0.3% | -0.2% |

## Reading

- Excess = challenger daily return − that track’s base daily return.
- High held-out corr / same-sign / joint DD → **independent observe still required**; do **not** auto-combo.
- This report never opens live cutover or a joint ACCEPT ballot.

## Non-actions

- No Soft-assist × Sleeve-tilt combo
- No live wire from this report

## Label

`SOFT_SLEEVE_OBSERVE_OVERLAP_2026-09-11__NO_COMBO__NO_LIVE`
