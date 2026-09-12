# Soft-Assist DL T2 Sequence Stage A Screen

Generated: `2026-09-12T06:53:25.616634+00:00` · asof **2026-09-11**
Verdict: **`RULE_PROMOTE_ONLY_NO_T2_LIFT`** · books **9** · torch_used **false**
Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false**

## Question

Do causal past-L log-return sequences (flat linear / MLP h8 / numpy 1D-CNN) as Soft buy boosts promote-shaped-beat Soft observe — without torch and without deepening the parked binary Soft-buy MLP?

## Summary

- Observe `SOFT_CHAMP_PLUS_K9_LT30_a10` held **0.085** · tip_mdd_clean **True**
- Rule `SELL_a05` held **0.101** · tip_mdd_clean **True** · still_best_vs_dl **True**
- Beat live: **2** → `['SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05', 'SOFT_CHAMP_PLUS_K9_LT30_a10']`
- Promote-shaped > observe: **1** → `['SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05']`
- **DL T2** promote-shaped > observe: **0** → `[]`

## Books

| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |
|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|
| `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` | rule_sell_ref | PASS | PASS | Y | Y | 0.101 | 0.101 | 18.39% | -21.62% | 25.53% | -12.47% |
| `SOFT_CHAMP_PLUS_K9_LT30_a10` | observe | PASS | PASS | Y | Y | 0.085 | 0.105 | 18.43% | -21.62% | 25.56% | -12.58% |
| `LIVE_KD_OPT` | base | PASS | PASS | Y | N | 0.000 | 0.000 | 18.39% | -21.72% | 25.57% | -12.81% |
| `DL_T2_SEQ10_FLAT_h8_a025` | t2_seq10_flat_h8 | PASS | PASS | N | N | -0.044 | -0.006 | 18.47% | -21.73% | 25.66% | -13.01% |
| `DL_T2_SEQ10_LIN_a05` | t2_seq10_linear | PASS | PASS | N | N | -0.050 | -0.007 | 18.48% | -21.73% | 25.66% | -13.03% |
| `DL_T2_SEQ10_FLAT_h8_a05__SELL_a05` | t2_seq10_flat_h8_sell_a05 | PASS | PASS | N | N | -0.052 | -0.033 | 18.43% | -21.75% | 25.62% | -13.01% |
| `DL_T2_SEQ20_FLAT_h8_a05` | t2_seq20_flat_h8 | PASS | PASS | N | N | -0.061 | -0.002 | 18.51% | -21.72% | 25.69% | -13.11% |
| `DL_T2_SEQ10_FLAT_h8_a05` | t2_seq10_flat_h8 | PASS | PASS | N | N | -0.074 | -0.027 | 18.49% | -21.75% | 25.68% | -13.09% |
| `DL_T2_SEQ10_CNN_a05` | t2_seq10_cnn | PASS | PASS | N | N | -0.089 | -0.037 | 18.50% | -21.76% | 25.67% | -13.06% |

## Reading

- Features: causal past L∈{10,20} daily log-return sequences (no future bars).
- Models: flattened linear · flattened MLP h8 · shallow numpy 1D-CNN (no torch).
- Sell isolation: observe sell on most books; one book pairs rule `SELL_a05`.
- Soft∥Sleeve OPEN ballots stay independent; this screen never fuses or wires live.

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire
- No Soft-assist or Sleeve observe swap from this screen
- No Soft×Sleeve auto-combo
- No same-MLP binary Soft-buy deepen
- No torch import in this numpy T2 screen path

## Label

`SOFT_DL_T2_SEQ_STAGEA_SCREEN_2026-09-11__RULE_PROMOTE_ONLY_NO_T2_LIFT`
