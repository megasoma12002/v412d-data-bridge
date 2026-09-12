# Soft-Assist DL T2 Torch Stage A Screen

Generated: `2026-09-12T10:27:59.778595+00:00` · asof **2026-09-11**
Verdict: **`RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT`** · books **8** · torch **2.14.0+cpu** (cuda=False)
Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false**

## Question

Do torch causal TCN / tiny LSTM Soft buy boosts promote-shaped-beat Soft observe after the numpy T2 toehold showed no lift?

## Summary

- Observe `SOFT_CHAMP_PLUS_K9_LT30_a10` held **0.085** · tip_mdd_clean **True**
- Rule `SELL_a05` held **0.101** · tip_mdd_clean **True** · still_best_vs_dl **True**
- Beat live: **2** → `['SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05', 'SOFT_CHAMP_PLUS_K9_LT30_a10']`
- Promote-shaped > observe: **1** → `['SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05']`
- **DL torch T2** promote-shaped > observe: **0** → `[]`

## Books

| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |
|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|
| `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` | rule_sell_ref | PASS | PASS | Y | Y | 0.101 | 0.101 | 18.39% | -21.62% | 25.53% | -12.47% |
| `SOFT_CHAMP_PLUS_K9_LT30_a10` | observe | PASS | PASS | Y | Y | 0.085 | 0.105 | 18.43% | -21.62% | 25.56% | -12.58% |
| `LIVE_KD_OPT` | base | PASS | PASS | Y | N | 0.000 | 0.000 | 18.39% | -21.72% | 25.57% | -12.81% |
| `DL_T2_TORCH_LSTM10_a05` | t2_torch_lstm10 | PASS | PASS | N | N | -0.043 | -0.008 | 18.46% | -21.73% | 25.66% | -13.04% |
| `DL_T2_TORCH_LSTM10_a05__SELL_a05` | t2_torch_lstm10_sell_a05 | PASS | PASS | N | N | -0.060 | -0.032 | 18.45% | -21.75% | 25.66% | -13.02% |
| `DL_T2_TORCH_TCN10_a025` | t2_torch_tcn10 | PASS | PASS | N | N | -0.071 | -0.019 | 18.50% | -21.74% | 25.71% | -13.06% |
| `DL_T2_TORCH_TCN20_a05` | t2_torch_tcn20 | PASS | PASS | N | N | -0.094 | -0.040 | 18.50% | -21.76% | 25.72% | -13.10% |
| `DL_T2_TORCH_TCN10_a05` | t2_torch_tcn10 | PASS | PASS | N | N | -0.144 | -0.074 | 18.53% | -21.79% | 25.73% | -13.17% |

## Reading

- Features: causal past L∈{10,20} daily log-return sequences.
- Models: torch causal TCN (ch8/k3) · tiny LSTM (h8) on CPU.
- Parent numpy T2 screen remains the no-torch toehold; this charter is torch-only.
- Soft∥Sleeve OPEN ballots stay independent; this screen never fuses or wires live.

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire
- No Soft-assist or Sleeve observe swap from this screen
- No Soft×Sleeve auto-combo
- No same-MLP binary Soft-buy deepen

## Label

`SOFT_DL_T2_TORCH_STAGEA_SCREEN_2026-09-11__RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT`
