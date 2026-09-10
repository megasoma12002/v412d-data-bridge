# E22 stock-web source sweep (2026-09-10)

Human: **「網路上有很多跟股票有關的資訊網站都找看看」**  
Scope: Soft-Frozen + private FIN dividend ledger completeness after payment-date restore/fill.  
Soft-Frozen / live wire: **unchanged**.

## Ledger status (after #172/#173)

| Field | Soft-Frozen | Private FIN | Notes |
|---|---:|---:|---|
| Cash ex-date | **0% blank** | **0% blank** | |
| Cash payment-date | **0% blank** | **0% blank** | last blank `2891`/`2010-07-29` filled via CNYES `#3283475` → `2010-08-23` |
| Stock ex-date | **0% blank** | **0% blank** | |
| Stock payment-date | **0% blank** | **0% blank** | |
| Announcement-date | **27 blanks** (all `0050`) | **0** | FinMind also empty for 0050 |

Soft-Frozen E22 DQ KPI remains **`kpi_ok=true`** (announce blank is reported, not a fail flag).

## Site matrix (this environment)

| Site | Access | 除息/除權 | 發放日 | 公告日 | Notes |
|---|---|---|---|---|---|
| Yahoo TW quote dividend | OK | Yes | Yes | **No** | Best machine-readable pay dates; `0050` has pay, no announce |
| FinMind `TaiwanStockDividend` | OK | Yes | Yes (often blank early) | Yes (stocks) / **empty for 0050** | Official research feed |
| MOPS `t108sb27` | OK | Yes | Yes when filed | via major notices | **0050 not a MOPS “company”** (`之公司不存在`) |
| CNYES twstock dividend | OK | Yes | **No** | **No** | News reprints useful (e.g. 2891 pay date) |
| Wantgoo ex-dividend | Browser OK / HTTP **403** | Yes | Yes (often `--` early) | **No** | 2891 `2010-07-29` still `--` on Wantgoo |
| Goodinfo dividend policy | **Cloudflare blocked** | — | — | — | Do not reopen as backup |
| HiStock financial | OK (t=2) | Yes | Year only / weak | **No** | |
| MoneyDJ zcc | Thin / login-ish | Weak | No | No | |
| PChome MegaTime | Stub | No | No | No | |
| Wearn share | Weak | No | No | No | |
| YuantaETFs 0050 配息 | SPA; table not reliably scrapeable here | Expected | Expected | Unknown | Official issuer; needs human/browser JS |
| TWSE open ETF-div JSON tried | 404 / HTML | — | — | — | Endpoints stale |

## Spot checks

1. **2891 cash pay `2010-08-23`** — CNYES announcement body verified; Wantgoo still blank; Yahoo `cashPayDate=null`. Ledger keep CNYES fill.  
2. **Do not confuse** `2010-08-31` (stock ex) with cash pay.  
3. **Yahoo hist vs ledger** — no conflicting non-null pay dates found; Yahoo hist universe still misses some Soft-Frozen/`0050` rows that ledger already holds from prior MOPS/FinMind fills.

## Residual (not inventable from this sweep)

- **`0050` `announcement_date` × 27** — no accessible site exposes ETF announce dates in a scrapeable table; FinMind blank; MOPS company query N/A.  
  Next options (human/ops): Yuanta ETF 配息行事曆 manual export, or TWSE ETF issuer notices — **not** Yahoo/Wantgoo/Goodinfo.

## Non-actions

- No Soft-Frozen flip / no live e21 rewrite  
- No Goodinfo/Wantgoo reopen as automated backups  
- No proxy lag invention for missing announce dates  

## Artifacts

- Sweep JSON: `/tmp/stock_site_sweep_summary.json` (ephemeral run)  
- This note: `research/ops/E22_STOCK_WEB_SOURCE_SWEEP_2026-09-10.md`  
- Prior fills: `E22_PAYMENT_DATE_RESTORE_2026-09-10.md` · `E22_2891_CASH_PAYMENT_FILL_2010-08-23.md`

## Label

`E22_STOCK_WEB_SOURCE_SWEEP_2026-09-10__PAY_COMPLETE__0050_ANNOUNCE_RESIDUAL`
