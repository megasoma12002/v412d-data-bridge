# External Strategy Borrow Soft-Sell Stage A — Research Charter (paper only)

Date: 2026-09-12  
Status: **PAPER STAGE A OPEN**  
Parent lock: `RESEARCH_POSTURE_LOCK_RULEPATH_FIRST_DL_NEW_MECH` · Soft observe **KEEP** `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` · Sleeve observe **KEEP** `SLEEVE_RSI14_LT30_a0225`

Script: `scripts/e16_external_strategy_borrow_stagea_screen.py`  
Screen: `EXTERNAL_STRATEGY_BORROW_STAGEA_SCREEN.md`  
Prior hygiene notes: `EXTERNAL_BORROW_NOTES.md` (governance) — this charter turns **public exit / overbought motifs** into finite Soft **sell** books.

## Why this charter exists

Human ask: research strategies others share. We do **not** scrape login walls or paste proprietary curves. We map **citable public motifs** onto Soft-assist sell softs and paper-test them against the operating Soft observe.

## Question

Keeping Soft observe **buy** softs fixed (`BELOW_MA120@1` + `K9_LT30@1`), do **public overbought / exit** Soft-sell motifs clear tip-MDD hygiene and **promote-shaped-beat** Soft observe `…__SELL_a05`?

## Public borrow map (cite → local book)

| Motif | Public source (summary) | Local Soft sell book |
|---|---|---|
| RSI classic overbought exit (~70) | Investopedia RSI overbought / exit below strength | `EXT_RSI14_GT70_SELL_a05` / `_a10` |
| Trend-aligned sell (sell into strength) | Investopedia: prefer RSI sells with trend context | `EXT_RSI14_GT70_SELL_a05__TREND_MA60` |
| Bollinger upper exhaustion | Common public BB “upper band” exit folklore | `EXT_BB_UPPER_SELL_a05` |
| Money-flow overbought | Public MFI>80 overbought exit motif | `EXT_MFI14_GT80_SELL_a05` |
| Soft informs, does not replace | AQR “To Trade or Not” / our Note 2 | Buy soft stays Soft observe; only sell soft changes |

## Promote-shaped

tip YTD+1y **PASS** **and** tip YTD+1y MDD not worse than base **and** held-out score > 0.  
Success vs Soft observe = promote-shaped **and** held > Soft observe.

## Finite Stage A books (8)

1. `LIVE_KD_OPT` — base  
2. `SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05` — Soft observe (beat target)  
3. `SOFT_CHAMP_PLUS_K9_LT30_a10` — prior Soft (sell @1.0)  
4. `EXT_RSI14_GT70_SELL_a05` — RSI14>70 sell α=0.5  
5. `EXT_RSI14_GT70_SELL_a10` — RSI14>70 sell α=1.0  
6. `EXT_BB_UPPER_SELL_a05` — BB upper sell α=0.5  
7. `EXT_MFI14_GT80_SELL_a05` — MFI>80 sell α=0.5  
8. `EXT_RSI14_GT70_SELL_a05__TREND_MA60` — RSI14>70 sell α=0.5 only if `ABOVE_MA60`

## Non-actions

- No web scrape of login / TOS-blocked sources; no verbatim republication of third-party equity curves  
- No live Soft-assist / Soft-Frozen / KD / TEL / E45 / Sleeve wire  
- No Soft or Sleeve observe swap from this screen  
- No Soft×Sleeve auto-combo  
- No Soft-buy MLP deepen / no T2 Soft-buy reopen  

## Label

`EXTERNAL_STRATEGY_BORROW_STAGEA_CHARTER_2026-09-12__PAPER_OPEN`
