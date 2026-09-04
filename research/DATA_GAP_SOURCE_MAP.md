# Data Gap + Challenger Source Map

Date: **2026-09-04**  
Companion: `data/dividend_events/e22_payment_date_gap_report.json`, `research/G5_DATA_WIRING_TICKETS.md`

This note answers two questions:

1. Which gaps can we **fill now** from free official feeds?
2. Where can **challenger-grade** data be fetched for the remaining research tracks?

---

## 1. E22 payment-date gap (`cash_payment_date`)

### What we did

| Step | Source | Result |
|---|---|---|
| Primary ledger | FinMind `TaiwanStockDividend` | 150 rows; **29** cash events missing payment date (mostly 2010–2014) |
| Official reconcile | MOPS `ajax_t108sb27` | Same early-year blanks; **0** official fills |
| GoodInfo / 玩股網 | Cloudflare **403** from this environment | Not usable here |
| CMoney 股利頁 | HTTP OK but **no 發放日 column** (amounts only, recent years) | Not usable for this gap |
| **Yahoo 台股股利政策** | `https://tw.stock.yahoo.com/quote/{code}.TW/dividend` | **29/29 filled** (`現金股利發放日`) |

Script:

```bash
python3 scripts/e22_backfill_payment_dates_yahoo.py
python3 scripts/e22_reconcile_payment_dates_mops.py --write-proxy   # optional QC / legacy proxy
```

Artifacts:

- Official ledger updated: `data/dividend_events/e22_dividend_events.csv`
- Provenance: `e22_payment_date_yahoo_backfill.json`, `web_scrape_payment_dates.csv`
- Full Yahoo dump: `yahoo_tw_dividend_history.csv`

### Note on third-party sites the user named

| Site | Status in this agent env |
|---|---|
| GoodInfo | Cloudflare human-check / 403 |
| 玩股網 Wantgoo | 403 / 404 on dividend URLs |
| CMoney | Loads, but table lacks payment date |
| Yahoo TW | Works; used as substitute aggregator with explicit 現金股利發放日 |

One NEAR match: `5880` FinMind ex `2012-08-02` vs Yahoo ex `2012-08-03` (±1d); payment date taken from Yahoo.

---

## 2. A0 historical industry PIT (T3)

| Source | Access | PIT? | Notes |
|---|---|---|---|
| FinMind `TaiwanStockInfo` | Free API | **No** — current snapshot (+ multi-tag rows) | Fetched → `data/research_advanced/finmind_taiwan_stock_info_snapshot.csv` |
| TWSE OpenAPI `t187ap03_L` | Free | **No** — current profile | Fetched → `twse_company_industry_snapshot.csv` |
| TWSE Data E-Shop **TWT58U** | Paid daily product | Point-in-time if archived daily | **Still missing** — required for true industry PIT |
| TWMD `issuer-classification` | Paid | Provider-derived; verify `as_of_date` | Not a substitute for raw TWSE history without lineage QC |

**Next actionable path:** buy/archive daily TWT58U (or equivalent) and build `industry_pit.csv` challenger under `repro/`; do not silently patch A0.

---

## 3. Next-gen Alpha 3A / microstructure / alt-data

Stage 3–4–6 CS remixes are **STOP**. New family needs a **new PIT source**.

| Family | Free / low-friction | Status in `data/research_advanced/` |
|---|---|---|
| Margin / short balances | FinMind + TWSE `MI_MARGN` | **Fetched** (11-name history + snapshot) |
| Securities lending | FinMind lending | **Fetched** (11-name history) |
| Futures / options OI | FinMind TX/MTX + TXO daily | **Fetched** (TX/MTX full; TXO agg + sample) |
| Tick / microstructure | FinMind tick (member) | **Still blocked** on free tier |
| Institutional flow | FinMind institutional | **Fetched** (11-name history) |
| Alt-data | Only if checked-in with available_date | Still skip unless PIT contract exists |

---

## 4. G4 hedge — real instrument book (H2)

| Instrument | Where / pack file | Use |
|---|---|---|
| 融券餘額 / 可賣 | `finmind_margin_short_history.csv` + `twse_mi_margn_snapshot.json` | Capacity / crowding |
| 借券費率 / 成交 | `finmind_securities_lending_history.csv` | Cost of synthetic short |
| Index futures (TX / MTX) | `finmind_tx_futures_daily.csv`, `finmind_mtx_futures_daily.csv` | Preferred liquid hedge sleeve |
| Put budget | `finmind_txo_option_daily_agg.csv` (+ sample) | H3 insurance ceiling |

G4 H1 (cash de-lever) needs **no** new market data — only existing NAV/exposure series.

---

## 5. E6 earliest board announcement

| Source | Status |
|---|---|
| FinMind `AnnouncementDate` | **Fetched** as proxy → `e6_announcement_date_proxy.csv` |
| Limitation | Still not guaranteed = first board dividend-proposal date |
| Next | MOPS 重大訊息全文 NLP challenger if promoting E6 beyond shadow |

Keep E6 as **shadow** until a board-date challenger QC exists.

---

## 6. Priority to close remaining gaps

```
P0  Done: payment dates, margin/lending/futures/options-agg/institutional packs
P1  Optional Stage-7 probes on TX OI timing / G4 paper capacity book
P2  Paid TWT58U archive → industry PIT (only if industry-neutral alpha reopens)
P3  Tick member tier / MOPS board-date NLP (only if promoting those tracks)
```

No item here authorizes gate promotion or in-place SOFT_FROZEN edits.

Companion status: `research/ADV_RESEARCH_DATA_STATUS.md`
