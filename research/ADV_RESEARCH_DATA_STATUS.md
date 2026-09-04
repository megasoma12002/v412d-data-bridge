# Advanced Research Data Fetch — 2026-09-04

Pack: `data/research_advanced/`  
Script: `scripts/fetch_advanced_research_data.py`  
Frozen ledgers: **untouched**

## What we grabbed (free / working)

| Dataset | File | Rows (approx) | Use |
|---|---|---:|---|
| TWSE company→industry snapshot | `twse_company_industry_snapshot.csv` | 1,094 | Current industry map (**not** historical PIT) |
| FinMind stock info snapshot | `finmind_taiwan_stock_info_snapshot.csv` | ~4k | Current tags |
| TWSE margin snapshot | `twse_mi_margn_snapshot.json` | market-wide | Same-day margin/short |
| Margin/short history (11 names) | `finmind_margin_short_history.csv` | 23,216 | G4 capacity / crowding |
| Securities lending (11 names) | `finmind_securities_lending_history.csv` | 59,340 | Borrow fee / G4 cost |
| Institutional flow (11 names) | `finmind_institutional_history.csv` | 116,045 | Flow features |
| TX futures daily + OI | `finmind_tx_futures_daily.csv` | 45,154 | Timing / hedge sleeve |
| MTX futures daily | `finmind_mtx_futures_daily.csv` | (see status) | Smaller hedge |
| TXO options daily 2020–2026 | `finmind_txo_option_daily_2020_2026.csv` | (see status) | Put-budget / H3 ceiling |
| E6 announce proxy | `e6_announcement_date_proxy.csv` | 150 | Shadow E6 only |

Status machine-readable: `fetch_status.json`

## Still blocked / paid / incomplete

| Need | Status |
|---|---|
| Historical industry reclassification (TWT58U archive) | **Not free here** — only snapshots |
| Equity tick / microstructure | FinMind tick endpoints **unavailable** on free tier |
| Guaranteed first board dividend-proposal date | Still **AnnouncementDate proxy**; needs MOPS full-text |

## Suggested Stage-7 probes using this pack

1. TX/`open_interest` timing overlay on early-stack NAV  
2. G4 paper: margin + lending fee capacity book (no live shorts)  
3. Options put-budget ceiling from TXO daily  
4. Defer industry-neutral alpha until TWT58U PIT purchased/archived  
