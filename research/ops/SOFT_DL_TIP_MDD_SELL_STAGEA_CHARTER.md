# Soft-Assist DL Tip-MDD / Giveback Sell-Role Stage A — Research Charter (paper only)

Date: 2026-09-12  
Status: **PAPER STAGE A DONE** · verdict **`BEATS_LIVE_NO_OBSERVE_LIFT`**  
Parent lock: `RESEARCH_POSTURE_LOCK_RULEPATH_FIRST_DL_NEW_MECH`  
Prior: Soft DL 4-track T3 sell used **fwd&lt;0** labels → tip sometimes clean, held &lt; Soft observe; T2 Soft-buy boosts **DONE no lift**; Soft-buy MLP deepen **PARKED**.

Script: `scripts/e16_soft_dl_tip_mdd_sell_stagea_screen.py`  
Screen: `SOFT_DL_TIP_MDD_SELL_STAGEA_SCREEN.md`

Soft-Frozen **clips KEEP** · live **`KD_OPT` KEEP** · **`TEL_EQUAL` KEEP** · Soft-assist observe **KEEP** `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` · Sleeve-tilt observe **KEEP** `SLEEVE_RSI14_LT30_a0225` · E45 **OFF**

## Why this charter exists

Human lock: further DL only via **new mechanism / label / role**. This Stage A changes the **label** (tip-path MDD / giveback severity) while keeping Soft **sell role** (not Soft-buy deepen, not T2 reopen). Rule Soft observe `…__SELL_a05` remains the beat target — this screen never swaps observe.

## Question

Keeping Soft observe **buy** softs fixed (`BELOW_MA120@1` + `K9_LT30@1`), does a walk-forward tiny MLP Soft **sell** score trained on **forward path-MDD / giveback-shaped labels** clear tip-MDD hygiene and **promote-shaped-beat** Soft observe `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05`?

## Design

| Item | Choice |
|---|---|
| Scope | Soft-assist track **only** (Sleeve observe unchanged; no fuse) |
| Buy soft | Fixed Soft observe buy (no Soft-buy DL) |
| Role | Soft **sell** amplitude from DL risk score |
| Features | HIGH-side TA bool catalog (same T3 feature family) |
| Labels | Forward H=10 path MDD: clf `1{path_mdd ≤ −τ}` · reg `−path_mdd` (giveback severity) |
| Model | TinyMLP h8 · year walk-forward · train years `&lt; Y`, apply `Y` |
| Amplitude | Soft sell = `1 + α · risk_score` with α∈{0.25,0.5}; one book × `RSI6_GT80` gate |
| Live | **Never** wired from this screen |

## Promote-shaped

tip YTD+1y **PASS** **and** tip YTD+1y MDD not worse than base **and** held-out score &gt; 0.  
Success vs Soft observe = promote-shaped **and** held &gt; Soft observe.

## Finite Stage A books (8)

1. `LIVE_KD_OPT` — base  
2. `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` — Soft observe (rule-path OPEN)  
3. `SOFT_CHAMP_PLUS_K9_LT30_a10` — prior Soft (sell @1.0 archive)  
4. `DL_T3_SELL_DOWN_a05` — T3 control (`fwd&lt;0` clf → sell α=0.5)  
5. `DL_TIPMDD_SELL_CLF_a05` — path-MDD clf → sell α=0.5  
6. `DL_TIPMDD_SELL_REG_a05` — giveback / −path-MDD reg → sell α=0.5  
7. `DL_TIPMDD_SELL_CLF_a025` — path-MDD clf → sell α=0.25  
8. `DL_TIPMDD_SELL_CLF_a05__RSI_GATE` — path-MDD clf × `RSI6_GT80`  

## Non-actions

- No live Soft-assist / Soft-Frozen / KD / TEL / E45 / Sleeve wire  
- No Soft-assist or Sleeve observe swap from this screen  
- No Soft×Sleeve auto-combo  
- No same-MLP Soft-buy deepen · no T2 Soft-buy boost reopen  
- No T3 reopen that only changes α on `fwd&lt;0` without tip-MDD labels  

## Label

`SOFT_DL_TIP_MDD_SELL_STAGEA_CHARTER_2026-09-12__BEATS_LIVE_NO_OBSERVE_LIFT`
