# Soft KD / Bollinger Sensitivity Screen — Stage A

Generated: `2026-09-11T00:54:41.009400+00:00` · asof **2026-09-10**
Verdict: **`BEATS_CHAMPION`** · books **16** · hard-AND **forbidden**

## Question

Do soft (non-blocking) KD-low / BB-lower buy score adds — alone or as second soft on Soft-assist champion — tip-clean beat `LIVE_KD_OPT` or lift the Soft-assist champion?

## Summary

- Beat live: **8** → `['SOFT_CHAMP_PLUS_K9_LT30_a10', 'SOFT_BOTH__BELOW_MA120__RSI6_GT80', 'SOFT_CHAMP_PLUS_K9_LT30_a05', 'SOFT_CHAMP_PLUS_BB_LOWER_a025', 'SOFT_CHAMP_PLUS_BB_LOWER_a05', 'SOFT_CHAMP_PLUS_BB_PCTB_LT0_a05', 'SOFT_CHAMP_PLUS_BB_LOWER_a10', 'SOFT_CHAMP_PLUS_BB_PCTB_LT0_a10']`
- Beat Soft-assist champion: **1** → `['SOFT_CHAMP_PLUS_K9_LT30_a10']`
- Champion `SOFT_BOTH__BELOW_MA120__RSI6_GT80` held score: **0.069**

## Top 12

| ID | Track | Tip YTD | Tip 1y | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |
|---|---|---|---|---:|---:|---:|---:|---:|---:|
| `SOFT_CHAMP_PLUS_K9_LT30_a10` | champ_sens | PASS | PASS | 0.086 | 0.105 | 18.11% | -21.62% | 24.84% | -12.58% |
| `SOFT_BOTH__BELOW_MA120__RSI6_GT80` | champion | PASS | PASS | 0.069 | 0.079 | 18.09% | -21.64% | 24.76% | -12.48% |
| `SOFT_CHAMP_PLUS_K9_LT30_a05` | champ_sens | PASS | PASS | 0.060 | 0.082 | 18.11% | -21.64% | 24.82% | -12.57% |
| `SOFT_CHAMP_PLUS_BB_LOWER_a025` | champ_sens | PASS | PASS | 0.045 | 0.060 | 18.10% | -21.66% | 24.78% | -12.52% |
| `SOFT_CHAMP_PLUS_BB_LOWER_a05` | champ_sens | PASS | PASS | 0.036 | 0.051 | 18.10% | -21.67% | 24.76% | -12.52% |
| `SOFT_CHAMP_PLUS_BB_PCTB_LT0_a05` | champ_sens | PASS | PASS | 0.036 | 0.051 | 18.10% | -21.67% | 24.76% | -12.52% |
| `SOFT_CHAMP_PLUS_BB_LOWER_a10` | champ_sens | PASS | PASS | 0.010 | 0.030 | 18.11% | -21.69% | 24.77% | -12.52% |
| `SOFT_CHAMP_PLUS_BB_PCTB_LT0_a10` | champ_sens | PASS | PASS | 0.010 | 0.030 | 18.11% | -21.69% | 24.77% | -12.52% |
| `LIVE_KD_OPT` | base | PASS | PASS | 0.000 | 0.000 | 18.07% | -21.72% | 24.86% | -12.81% |
| `SOFT_BUY_K9_LT30__SELL_RSI6` | soft_or | PASS | PASS | -0.011 | 0.037 | 18.16% | -21.68% | 25.02% | -13.08% |
| `SOFT_BUY_K9_LT30_OR_BB_LOWER_a025__SELL_RSI6` | soft_or | PASS | PASS | -0.040 | -0.001 | 18.15% | -21.72% | 24.95% | -13.02% |
| `SOFT_BUY_K9_LT20__SELL_RSI6` | soft_or | PASS | PASS | -0.050 | 0.006 | 18.18% | -21.71% | 25.00% | -13.11% |

## Reading

- Soft OR = additive score boosts (both can fire); **not** boolean AND buy gate.
- Champion sensitivity keeps Soft-assist buy `BELOW_MA120` + sell `RSI6_GT80`, adds BB/K soft.
- Soft-assist observe / live KD unchanged from this screen alone.

## Non-actions

- No hard AND · no Soft-assist observe swap · no live wire · no Soft-Frozen / E45 change

## Label

`SOFT_KD_BB_SENSITIVITY_SCREEN_STAGE_A_2026-09-11__BEATS_CHAMPION`
