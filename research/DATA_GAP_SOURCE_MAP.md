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
| Official reconcile | MOPS `ajax_t108sb27`（公司股利分派公告資料彙總表／現金股利發放日） | Same early-year blanks; **0 additional official fills** into missing set |
| Cross-check 2015+ | FinMind vs MOPS | Both populated; use as ongoing QC |
| Research-only overlay | Median lag **28** calendar days from known events | `e22_payment_date_research_proxy.csv` (`quality=PROXY_MEDIAN_LAG`) |

Script:

```bash
python3 scripts/e22_reconcile_payment_dates_mops.py --write-proxy
```

### Official rule

- **Do not** merge proxy dates into `e22_dividend_events.csv`.
- Official `E22_v2` remains **ex-date** credit; payment-date is E22_v3 H1 challenger only.

### Where to get true early-year payment dates

| Source | URL / access | Coverage | Cost | Notes |
|---|---|---|---|---|
| MOPS 股利分派公告彙總 | `https://mopsov.twse.com.tw/mops/web/t108sb27` | Bulk HTML; payment blank pre-~2014 for our names | Free | Already scraped |
| FinMind Dividend | `dataset=TaiwanStockDividend` | 2005→now; payment often blank early | Free / Backer | Current primary |
| TDCC 帳簿劃撥交付日期 | `https://openapi.tdcc.com.tw/v1/opendata/1-7` | **Recent ~2y**; stock delivery reasons | Free | **Not** cash dividend payment |
| TWSE OpenAPI 股利分派 | `https://openapi.twse.com.tw/v1/opendata/t187ap45_L` | Current snapshot; **no** payment date field | Free | Board/shareholder dates only |
| Company annual reports / 除權息公告原文 | MOPS 重大訊息 + IR PDFs | Event-level | Free, manual | Best free path for the 29 rows |
| TEJ / CMONEY / Bloomberg CA | vendor terminals | Full history | Paid | Cleanest backfill |
| TW Market Data corporate-actions | `GET /v2/datasets/corporate-actions` | Normalized MOPS/TWSE | Paid API key | Check whether `payment_date` is populated historically |

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
