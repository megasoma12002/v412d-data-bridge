# Soft-Assist Tiny-MLP Stage A — Research Charter (paper only)

Date: 2026-09-12  
Status: **PAPER STAGE A DONE** · verdict **`BEATS_LIVE_NO_OBSERVE_LIFT`** · **no live wire** · **no Soft×Sleeve fuse** · Soft-assist observe **KEEP**  
Human ask: 有辦法試試看深度學習嗎

Script: `scripts/e16_soft_dl_mlp_stagea_screen.py`  
Screen: `SOFT_DL_MLP_STAGEA_SCREEN.md`

Soft-Frozen **clips KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · Soft-assist observe **KEEP** `SOFT_CHAMP_PLUS_K9_LT30_a10` · Sleeve-tilt observe **UNCHANGED** · E45 **OFF**

## Question

Can a **tiny feed-forward MLP** (numpy, no torch) — trained walk-forward on causal TA low-features — produce an additive Soft buy score that **promote-shaped** tip-clean beats `LIVE_KD_OPT` and/or lifts Soft-assist observe `SOFT_CHAMP_PLUS_K9_LT30_a10`?

**Promote-shaped** = tip YTD+1y PASS **and** tip YTD+1y MDD not worse than base **and** held-out score > 0.

## Why this is “try DL” but still honest

| Item | Choice |
|---|---|
| Scope | Soft-assist track **only** (Sleeve separate; no fuse) |
| Model | Tiny MLP `n_feat → 8 → 1` (+ linear ablation) — **shallow NN**, not LSTM/transformer |
| Features | Existing causal `ta_indicator_catalog` **LOW** panels (bool→float) |
| Training | Walk-forward by calendar year; train on prior years only |
| Target | Next **10-session** name return → sigmoid soft boost in `[0, α]` |
| Sell soft | Keep observe sell `RSI6_GT80` (isolate buy-side DL) |
| Live | **Never** wired from this screen |

This is a **first DL toehold** under Stage A governance — not a claim that deep learning is live-ready.

## Stage A books (finite ≤6)

1. `LIVE_KD_OPT` — base  
2. `SOFT_BOTH__BELOW_MA120__RSI6_GT80` — prior Soft champion  
3. `SOFT_CHAMP_PLUS_K9_LT30_a10` — operating Soft-assist observe  
4. `DL_SOFT_LINEAR_a10` — linear/logistic soft ablation (α=1.0)  
5. `DL_SOFT_MLP_h8_a10` — tiny MLP α=1.0  
6. `DL_SOFT_MLP_h8_a05` — tiny MLP α=0.5 (“sin a little”)

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire  
- No Soft-assist observe swap from this screen alone  
- No Soft×Sleeve auto-combo  
- No hard-AND reopen  
- No torch/TF dependency in live path  

## Label

`SOFT_DL_MLP_STAGEA_CHARTER_2026-09-12__BEATS_LIVE_NO_OBSERVE_LIFT`
