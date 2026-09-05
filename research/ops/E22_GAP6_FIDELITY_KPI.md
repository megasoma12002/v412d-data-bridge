# E22 Gap #6 Fidelity KPI

Generated: `2026-09-05T08:01:13.742609+00:00`
Status: **OPS / RESEARCH** — Soft-Frozen unchanged; no cutover; no odd-lot promote.

## Code wire

- Default books: **`E22_v2s`** (expect `E22_v2s`)
- E21 imports/apply: **True** / **True**
- Formal status wired: **True**
- Code OK: **True**

## Live ledger evidence (`forward/e21`)

- asof: **2026-09-04**
- `e22_books_version` in portfolio_state: **False**
- `e22_manifest` in portfolio_state: **False**
- `e22_version` col in nav.csv: **False**
- `dividends_applied.csv`: **False** (n=0)
- Live evidence OK: **False**

> Live ledger artifacts predate E22 field persistence (code path is wired; next forward run should write e22_* fields). Do not rewrite history.

## Ex → pay lag (ledger completeness already green; this is timing fidelity)

- Cash median / p90 days: **27.0** / **36.0** (n=144)
- Stock median / p90 days: **40.0** / **50.0** (n=52)

## Receivable stub (universe, report-only)

- Open cash events with ex≤asof < pay: **1**
- Codes: `5880`
- Formal books credit cash on cash_ex_date (no receivable asset). This count is universe-level timing exposure vs custody pay-date, not position-weighted PnL.

## Dividend tax sensitivity (report-only; formal = TAX0)

- No dividends_applied.csv yet — tax sensitivity deferred until live applies cash events.

## Odd-lot (`E22_v2s_tw`)

- Status: **DEFERRED** — default remains `E22_v2s`
- Promote checklist: `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`

## Flags

- `LIVE_LEDGER_E22_FIELDS_MISSING`

Monitoring KPI OK (code path): **True**

Re-run: `python3 scripts/e22_gap6_fidelity_kpi.py`
