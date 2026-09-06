# E45 M2 — True DEF Data Ingest v0 (BEFORE any M2-v1 sealed metrics)

Date: 2026-09-06  
Status: **FROZEN INGEST FOR RESEARCH** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent honesty gap: `E45_M2_DEF_SLEEVE_V0_FROZEN.md` (DEF_TEL equity proxy; DEF_CASH0 @ 0%)  
Fetcher: `scripts/fetch_e45_true_def_proxies.py`  
Store: `data/def_proxies/` (QC: `data/def_proxies/qc_summary.json`)  
Claimed MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## Why this pack exists

M2 §2 PASS used **`DEF_TEL`** (Telecom equity) because `forward/e21/live_market.csv` had no cash / short-duration / gov-bond series.  
This pack **fills research-grade DEF proxies** so a future **M2 v1** freeze can relocate to true DEF — it does **not** rewrite M2 v0 PASS, does **not** merge into live market, and does **not** open Soft-Frozen / stitch / observe.

## Frozen proxy table

| Code | Class | Currency | Source | First date (ingest) | Role |
|---|---|---|---|---|---|
| `00719B` | `tw_bond_etf` | TWD | FinMind | 2018-02-01 | **Preferred short-duration TWD** DEF destination |
| `00679B` | `tw_bond_etf` | TWD | FinMind | 2017-01-17 | Long USD IG via TW wrapper — **not** cash; duration stress only |
| `00687B` | `tw_bond_etf` | TWD | FinMind | 2017-04-13 | Long USD IG twin — same honesty as `00679B` |
| `BIL` | `usd_cash_like` | USD | Yahoo | 2010-01-04 | **Preferred cash-like USD**; needs FX join |
| `SHY` | `usd_cash_like` | USD | Yahoo | 2010-01-04 | Short Treasury twin |
| `USDTWD` | FX mid | TWD/USD | FinMind | 2010-01-04 | Spot mid `(buy+sell)/2` — research join only |

Primary M2-v1 destination candidates (pick in a **new** freeze, not here):

1. `DEF_719B` → relocate residual to **`00719B`** (TWD short-duration) when listed  
2. `DEF_BIL_FX` → relocate to **`BIL`** marked in TWD via `USDTWD` mid (full history; FX risk explicit)

## Honesty bounds (binding)

1. **Not in live market.** Do not append these codes to `forward/e21/live_market.csv` without a dedicated paper pack + human-reviewed join.
2. **Listing lag.** Before each TW ETF first date, that TWD DEF does not exist — no synthetic backfill of bond prices.
3. **Long bond ≠ cash.** `00679B` / `00687B` are long-duration; crisis years may **hurt** vs equity shrink. Do not label them “cash DEF”.
4. **USD proxies need FX.** `BIL`/`SHY` returns in a TWD book without `USDTWD` join are **invalid** for sealed claims.
5. **`DEF_TEL` remains equity.** M2 v0 PASS still stands on Telecom relocate; true DEF is a **v1** amendment.
6. **No RF invent on cash@0.** `DEF_CASH0` stays the shrink control until a dated yield series is frozen separately.

## QC gate (this ingest)

`overall_pass` requires `00719B`, `BIL`, `SHY`, and `USDTWD` all pass row/null checks in `qc_summary.json`.  
Re-run:

```bash
python3 scripts/fetch_e45_true_def_proxies.py
```

## Explicit non-actions

- Do **not** open Soft-Frozen / DEFAULT / stitch ballots from this ingest
- Do **not** auto-OPEN M2 observe (see dedicated ballot draft)
- Do **not** densify E45 mild-α as a substitute for true DEF
- Do **not** change M2 v0 formulas; M2 v1 = new freeze id after join rules are written
- Do **not** invent a replacement for the retired MDD narrative

## Next paper (out of scope here)

Draft `E45_M2_DEF_SLEEVE_V1_FROZEN` only after:

1. Calendar join of DEF series onto early-stack trading dates  
2. Pre-list policy (cash@0 vs skip relocate vs require BIL_FX)  
3. Cost model for bond ETF / FX (or explicit 0× ablation honesty)

Label: `E45_M2_TRUE_DEF_DATA_V0_FROZEN_2026-09-06__INGEST_ONLY__STITCH_FORBIDDEN`
