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
| FinMind `TaiwanStockInfo` | Free API | **No** — current snapshot (+ multi-tag rows) | Unsafe for industry-neutral alpha history |
| TWSE Data E-Shop **TWT58U** | Paid daily product | Point-in-time if archived daily | Official security→industry map |
| TWSE 產業類別劃分暨調整要點 + 調整公告 | Regulation + MOPS/TWSE notices | Event-level reclassification | Manual event calendar → rebuild PIT |
| TWMD `issuer-classification` | Paid | Provider-derived; verify `as_of_date` | Not a substitute for raw TWSE history without lineage QC |

**Next actionable path:** buy/archive daily TWT58U (or equivalent) and build `industry_pit.csv` challenger under `repro/`; do not silently patch A0.

---

## 3. Next-gen Alpha 3A / microstructure / alt-data

Stage 3–4 fundamental YoY remixes are **STOP**. New family needs a **new PIT source**.

| Family | Free / low-friction | Challenger / paid |
|---|---|---|
| Margin / short balances | FinMind `TaiwanStockMarginPurchaseShortSale`; TWSE `MI_MARGN` | TWMD `margin-short` |
| Securities lending | FinMind `TaiwanStockSecuritiesLending` | TWMD `chip-deep-securities-lending-daily` (2007→) |
| Futures / options OI | FinMind `TaiwanFuturesDaily` (`open_interest`); TAIFEX daily | FinMind options / vendor OP chain |
| Tick / microstructure | FinMind tick (**member tier**); TWSE intraday paid | Tick→Amihud/impact features |
| Institutional flow | FinMind `TaiwanStockInstitutionalInvestorsBuySell` | TWSE 三大法人 open data |
| Alt-data | Only if checked-in with available_date | Satellite / card / app — skip unless PIT contract exists |

Verified live in this environment (2026-09-04): margin, securities lending, futures OI, financial statements, month revenue.

---

## 4. G4 hedge — real instrument book (H2)

| Instrument | Where to get | Use |
|---|---|---|
| 融券餘額 / 可賣 | FinMind margin-short; TWSE credit reports | Capacity / borrow proxy, not fill model |
| 借券費率 / 成交 | FinMind securities lending (`fee_rate`) | Cost of synthetic short |
| Index futures (TX / MTX) | FinMind `TaiwanFuturesDaily`; TAIFEX | Preferred liquid hedge sleeve |
| ETF short (0050) | Same margin + lending feeds | Stock-borrow constrained |
| Put budget | TAIFEX option settles / vendor IV | H3 insurance ceiling |

G4 H1 (cash de-lever) needs **no** new market data — only existing NAV/exposure series.

---

## 5. E6 earliest board announcement

| Source | Limitation |
|---|---|
| FinMind `AnnouncementDate` / MOPS | Not guaranteed = first board dividend-proposal date |
| MOPS 重大訊息全文 | Manual NLP / keyword search for 董事會通過股利 |
| Vendor CA with `board_resolution_date` | Preferred if promoting E6 beyond shadow |

Keep E6 as **shadow** until a board-date challenger QC exists.

---

## 6. Priority to close gaps

```
P0  Keep E22_v2 ex-date ops (done) + MOPS payment reconcile QC (this PR)
P1  Manual/vendor fill of 29 early payment dates → enables fair E22_v3 H1
P2  Archive TWT58U (or event-based reclass calendar) → industry PIT challenger
P3  Wire FinMind lending + futures OI into a non-fundamental 3A/G4 sandbox
P4  E6 board-date challenger only if promoting beyond shadow
```

No item here authorizes gate promotion or in-place SOFT_FROZEN edits.
