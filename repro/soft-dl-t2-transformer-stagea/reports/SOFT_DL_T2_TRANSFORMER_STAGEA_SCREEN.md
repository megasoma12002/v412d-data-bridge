# Soft-Assist DL T2 Tiny Causal Transformer Stage A Screen

Generated: `2026-09-12T11:00:22.593685+00:00` · asof **2026-09-11**
Verdict: **`RULE_PROMOTE_ONLY_NO_T2_XFMR_LIFT`** · books **7** · torch **2.14.0+cpu** (cuda=False)
Live wire: **false** · Soft×Sleeve fuse: **forbidden** · observe swap: **false**

## Question

Does a tiny causal Transformer Soft buy boost promote-shaped-beat Soft observe (vs Soft observe + rule `SELL_a05`) after numpy/TCN/LSTM T2 showed no lift?

## Summary

- Observe `SOFT_CHAMP_PLUS_K9_LT30_a10` held **0.085** · tip_mdd_clean **True**
- Rule `SELL_a05` held **0.101** · tip_mdd_clean **True** · still_best_vs_dl **True**
- Beat live: **2** → `['SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05', 'SOFT_CHAMP_PLUS_K9_LT30_a10']`
- Promote-shaped > observe: **1** → `['SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05']`
- **DL tiny Transformer** promote-shaped > observe: **0** → `[]`

## Books

| ID | Track | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |
|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|
| `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` | rule_sell_ref | PASS | PASS | Y | Y | 0.101 | 0.101 | 18.39% | -21.62% | 25.53% | -12.47% |
| `SOFT_CHAMP_PLUS_K9_LT30_a10` | observe | PASS | PASS | Y | Y | 0.085 | 0.105 | 18.43% | -21.62% | 25.56% | -12.58% |
| `LIVE_KD_OPT` | base | PASS | PASS | Y | N | 0.000 | 0.000 | 18.39% | -21.72% | 25.57% | -12.81% |
| `DL_T2_TORCH_XFMR10_a025` | t2_torch_xfmr10 | PASS | PASS | N | N | -0.058 | -0.013 | 18.48% | -21.73% | 25.69% | -13.10% |
| `DL_T2_TORCH_XFMR10_a05__SELL_a05` | t2_torch_xfmr10_sell_a05 | PASS | PASS | N | N | -0.067 | -0.032 | 18.46% | -21.75% | 25.65% | -13.03% |
| `DL_T2_TORCH_XFMR20_a05` | t2_torch_xfmr20 | PASS | PASS | N | N | -0.090 | -0.047 | 18.48% | -21.77% | 25.65% | -13.12% |
| `DL_T2_TORCH_XFMR10_a05` | t2_torch_xfmr10 | PASS | PASS | N | N | -0.099 | -0.050 | 18.49% | -21.77% | 25.69% | -13.06% |

## Reading

- Features: causal past L∈{10,20} daily log-return sequences.
- Model: tiny causal Transformer (`d_model=8`, `nhead=2`, `nlayers=1`, causal mask) on CPU.
- Refs: Soft observe + rule `SELL_a05`; parent numpy/TCN/LSTM T2 screens remain no-lift baselines.
- Soft∥Sleeve OPEN ballots stay independent; this screen never fuses or wires live.

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire
- No Soft-assist or Sleeve observe swap from this screen
- No Soft×Sleeve auto-combo
- No same-MLP binary Soft-buy deepen

## Label

`SOFT_DL_T2_TRANSFORMER_STAGEA_SCREEN_2026-09-11__RULE_PROMOTE_ONLY_NO_T2_XFMR_LIFT`
