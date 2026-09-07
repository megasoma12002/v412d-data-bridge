# E22 Gap #6 Fidelity KPI

Generated: `2026-09-07T17:20:36.440479+00:00`
Status: **OPS / RESEARCH** — Soft-Frozen unchanged; odd-lot default **PROMOTED** to E22_v2s_tw (forward-only).

## Code wire

- Default books: **`E22_v2s_tw`** (expect `E22_v2s_tw`)
- E21 imports/apply: **True** / **True**
- Formal status wired: **True**
- Code OK: **True**

## Live ledger evidence (`forward/e21`)

- asof: **2026-09-07**
- `e22_books_version` in portfolio_state: **True**
- `e22_manifest` in portfolio_state: **True**
- `e22_version` col in nav.csv: **True**
- `dividends_applied.csv`: **False** (n=0)
- Live evidence OK: **True**

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

- Status: **PROMOTED** — formal default `E22_v2s_tw`
- Promote checklist: `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`

## Flags

- None

Monitoring KPI OK (code **and** live evidence): **True**
- code_ok: **True**
- live_evidence_ok: **True**
- ci_smoke_ok (= code_ok): **True**

Re-run: `python3 scripts/e22_gap6_fidelity_kpi.py`
