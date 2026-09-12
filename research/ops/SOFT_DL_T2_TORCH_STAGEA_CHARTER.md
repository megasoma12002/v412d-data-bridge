# Soft-Assist DL T2 Torch Stage A — Research Charter (paper only)

Date: 2026-09-12  
Status: **PAPER STAGE A DONE** · verdict **`RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT`**  
Parent: `SOFT_DL_T2_SEQ_STAGEA` (numpy toehold = **`RULE_PROMOTE_ONLY_NO_T2_LIFT`**)  
Human lock: Soft `SELL_a05` ∥ Sleeve `RSI14_a0225` independent OPEN; same-MLP binary Soft-buy deepen **parked**; DL only via **new** charter.

Script: `scripts/e16_soft_dl_t2_torch_stagea_screen.py`  
Screen: `SOFT_DL_T2_TORCH_STAGEA_SCREEN.md`

Soft-Frozen **clips KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · Soft-assist observe **KEEP** `SOFT_CHAMP_PLUS_K9_LT30_a10` · Sleeve-tilt observe **KEEP** · E45 **OFF**

## Why this charter exists

Numpy T2 Stage A (flat / MLP h8 / 1D-CNN) produced **0** DL promote-shaped wins vs Soft observe. Cloud Agent env now has **CPU torch**. This Stage A opens the parked **TCN / tiny LSTM** slot under a **new** objective charter — still Soft-assist track only.

## Question

Do **torch** causal sequence models (shallow **TCN** / tiny **LSTM**) on past-L log-returns as Soft **buy** boosts clear tip-MDD hygiene and **promote-shaped** beat Soft observe?

**Promote-shaped** = tip YTD+1y **PASS** **and** tip YTD+1y MDD not worse than base **and** held-out score > 0.  
Success vs Soft observe = promote-shaped **and** held > Soft observe.

## Design (torch CPU)

| Item | Choice |
|---|---|
| Scope | Soft-assist track **only** (Sleeve separate; no fuse) |
| Features | Causal past **L∈{10,20}** daily log-return sequences |
| Models | Shallow causal **TCN** (Conv1d ch=8, k=3); tiny **LSTM** (h=8, 1 layer) |
| Objective | Next **10-session** forward return regression → soft buy boost in `[0, α]` |
| Training | Walk-forward by calendar year; train years `< Y`, apply `Y`; Adam; CPU |
| Sell soft | Keep observe sell `RSI6_GT80`; one book pairs rule `SELL_a05` |
| Live | **Never** wired from this screen |

## Finite Stage A books

1. `LIVE_KD_OPT` — base  
2. `SOFT_CHAMP_PLUS_K9_LT30_a10` — Soft observe  
3. `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` — rule sell-amp ref  
4. `DL_T2_TORCH_TCN10_a05` — L=10 TCN, α=0.5  
5. `DL_T2_TORCH_LSTM10_a05` — L=10 LSTM, α=0.5  
6. `DL_T2_TORCH_TCN20_a05` — L=20 TCN, α=0.5  
7. `DL_T2_TORCH_TCN10_a025` — L=10 TCN, α=0.25  
8. `DL_T2_TORCH_LSTM10_a05__SELL_a05` — LSTM buy + rule sell amp  

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire  
- No Soft-assist or Sleeve observe swap from this screen  
- No Soft×Sleeve auto-combo  
- No same-MLP binary Soft-buy deepen  
- No CUDA requirement (CPU torch only)

## Label

`SOFT_DL_T2_TORCH_STAGEA_CHARTER_2026-09-12__RULE_PROMOTE_ONLY_NO_T2_TORCH_LIFT`
