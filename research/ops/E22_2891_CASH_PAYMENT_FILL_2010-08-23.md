# E22 fill — 2891 cash payment date 2010-08-23

Date: 2026-09-10  
Status: **FILLED** (research ledger) · Soft-Frozen unchanged · live wire false

## Gap

| Field | Value |
|---|---|
| Code | `2891` 中信金 |
| Fiscal | `98年` (belonging 2009) |
| Cash ex | `2010-07-29` |
| Cash amount | `0.64` |
| Prior `cash_payment_date` | blank (Yahoo / Wantgoo / MOPS t108sb27 / FinMind all empty) |

## Source (verified)

CNYES market announcement reprint:

- URL: https://news.cnyes.com/news/id/3283475
- Title: 中信金：中國信託金融控股股份有限公司99年度分派普通股現金股利暨私募乙種特別股股息公告。
- Quote: 「(二)特別股現金股息暨普通股現金股利發放日期：99年8月23日。」
- Cross-check amount: 「普通股現金股利計5,950,915,422元，每股配發0.64元」
- Companion ex-date notice: https://news.cnyes.com/news/id/3196226 (`除息交易日:99/07/29`)

ROC `99/08/23` → ISO **`2010-08-23`**.

## Non-confusion

`2010-08-31` is the **stock ex-rights** date (股票股利 0.64), **not** cash payment. Stock payment remains `2010-10-08`.

## Action

Wrote `cash_payment_date=2010-08-23` into `data/dividend_events/e22_dividend_events.csv` for the matching cash row only.

## Label

`E22_2891_CASH_PAYMENT_FILL_2010-08-23__CNYES_3283475`
