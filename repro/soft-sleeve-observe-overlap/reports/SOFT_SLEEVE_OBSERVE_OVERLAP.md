# Soft-assist vs Sleeve-tilt Observe Overlap (paper only)

Generated: `2026-09-12T13:42:13.814092+00:00` · asof **2026-09-11**
Soft `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` ∥ Sleeve `SLEEVE_RSI14_LT30_a0225` · **no combo · no live wire**

## Held-out (2019+) snapshot

- Corr(excess): **0.112**
- Same-sign frac: **48.1%**
- Both-underperform frac: **25.1%**
- Joint DD day frac: **46.9%**
- Mean joint DD depth: **0.1%**
- Report flags: high_overlap=`False` · high_joint_dd=`True`

## Windows

| Window | N | Corr | Same-sign | Both− | Joint DD days | Mean joint DD | Soft rel MDD | Sleeve rel MDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `full` | 3355 | 0.064 | 51.4% | 26.1% | 31.4% | 0.2% | -1.2% | -0.3% |
| `heldout_2019_plus` | 1861 | 0.112 | 48.1% | 25.1% | 46.9% | 0.1% | -0.4% | -0.3% |
| `sealed_2023_plus` | 884 | 0.267 | 50.2% | 26.1% | 63.0% | 0.1% | -0.4% | -0.2% |
| `ytd` | 167 | 0.907 | 81.4% | 44.3% | 0.0% | 0.0% | -0.4% | -0.0% |
| `trailing_1y` | 242 | 0.833 | 69.0% | 38.0% | 0.0% | 0.0% | -0.4% | -0.1% |

## Reading

- Excess = challenger daily return − that track’s base daily return.
- High held-out corr / same-sign / joint DD → **independent observe still required**; do **not** auto-combo.
- This report never opens live cutover or a joint ACCEPT ballot.

## Non-actions

- No Soft-assist × Sleeve-tilt combo
- No live wire from this report

## Label

`SOFT_SLEEVE_OBSERVE_OVERLAP_2026-09-11__NO_COMBO__NO_LIVE`
