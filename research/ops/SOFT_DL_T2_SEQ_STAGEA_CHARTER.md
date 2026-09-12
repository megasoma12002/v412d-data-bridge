# Soft-Assist DL T2 Sequence Stage A — Research Charter (paper only)

Date: 2026-09-12  
Status: **PAPER STAGE A DONE** · verdict **`RULE_PROMOTE_ONLY_NO_T2_LIFT`** · **no live wire** · **no Soft×Sleeve fuse** · Soft / Sleeve OPEN ballots **UNCHANGED**  
Parent: `SOFT_DL_4TRACK_STAGEA` (T2 was **CHARTER_ONLY_NO_TORCH**)  
Human lock: Soft `SELL_a05` ∥ Sleeve `RSI14_a0225` independent OPEN; same-MLP binary Soft-buy deepen **parked**; DL only via **new** objective / features / role / rep→rule.

Script: `scripts/e16_soft_dl_t2_seq_stagea_screen.py`  
Screen: `SOFT_DL_T2_SEQ_STAGEA_SCREEN.md`

Soft-Frozen **clips KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · Soft-assist observe **KEEP** `SOFT_CHAMP_PLUS_K9_LT30_a10` · Sleeve-tilt observe **KEEP** · E45 **OFF**

## Why this charter exists

4-track Stage A parked **T2** (seq / TCN / LSTM) because torch was missing. This Stage A opens T2 with a **numpy-only** causal sequence toehold — **no torch import** in the screen path — so paper evidence can land before (or without) torch-backed TCN/LSTM.

## Question

Do **causal past-L log-return sequences** (flattened linear / tiny MLP / shallow 1D-CNN) as Soft **buy** boosts clear tip-MDD hygiene and **promote-shaped** beat Soft observe — without deepening the parked binary TA-bool Soft-buy MLP?

**Promote-shaped** = tip YTD+1y **PASS** **and** tip YTD+1y MDD not worse than base **and** held-out score > 0.  
Success vs Soft observe = promote-shaped **and** held > Soft observe.

## Design (numpy, no torch)

| Item | Choice |
|---|---|
| Scope | Soft-assist track **only** (Sleeve separate; no fuse) |
| Features | Causal past **L∈{10,20}** daily log-return sequences per name (no future bars) |
| Models | Flattened → linear; flattened → MLP `h8`; shallow numpy **1D-CNN** (no torch) |
| Objective | Next **10-session** forward return regression → soft buy boost in `[0, α]` |
| Training | Walk-forward by calendar year; train years `< Y`, apply `Y` |
| Sell soft | Keep observe sell `RSI6_GT80` (isolate buy-side seq); one book pairs rule `SELL_a05` |
| Live | **Never** wired from this screen |

## Finite Stage A books (≤6 DL + refs)

1. `LIVE_KD_OPT` — base  
2. `SOFT_CHAMP_PLUS_K9_LT30_a10` — Soft observe  
3. `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` — rule sell-amp ref  
4. `DL_T2_SEQ10_FLAT_h8_a05` — L=10 flatten + MLP h8, α=0.5  
5. `DL_T2_SEQ20_FLAT_h8_a05` — L=20 flatten + MLP h8, α=0.5  
6. `DL_T2_SEQ10_LIN_a05` — L=10 flatten + linear, α=0.5  
7. `DL_T2_SEQ10_CNN_a05` — L=10 numpy 1D-CNN, α=0.5  
8. `DL_T2_SEQ10_FLAT_h8_a025` — L=10 flatten + MLP h8, α=0.25  
9. `DL_T2_SEQ10_FLAT_h8_a05__SELL_a05` — seq buy + rule sell amp  

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 wire  
- No Soft-assist or Sleeve observe swap from this screen  
- No Soft×Sleeve auto-combo  
- No hard-AND reopen  
- No same-MLP binary Soft-buy deepen  
- No torch/TF in **this** screen path (torch may be added to Cloud Agent env separately for future TCN/LSTM)

## Label

`SOFT_DL_T2_SEQ_STAGEA_CHARTER_2026-09-12__RULE_PROMOTE_ONLY_NO_T2_LIFT`
