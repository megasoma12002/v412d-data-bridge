# E22 Gap #6 Fidelity KPI

Generated: `2026-09-19T10:32:11.349431+00:00`
Status: **OPS / RESEARCH** — Soft-Frozen Stage-B tax ACCEPT; live DEFAULT **`E22_v3_recv_pay_tax10`** (receivable + flat 10% withhold).

## Code wire

- Default books: **`E22_v3_recv_pay_tax10`** (expect `E22_v3_recv_pay_tax10`)
- E21 imports/apply: **True** / **True**
- Formal status wired: **True**
- Code OK: **True**

## Live ledger evidence (`forward/e21`)

- asof: **2026-09-16**
- `e22_books_version` in portfolio_state: **True**
- `e22_manifest` in portfolio_state: **True**
- `e22_version` col in nav.csv: **True**
- `dividends_applied.csv`: **False** (n=0)
- observed books version: **E22_v2s_tw_effex** (ops debt until next forward if still `E22_v2s_tw`)
- Live evidence OK: **True**

## Ex → pay lag (ledger completeness already green; this is timing fidelity)

- Cash median / p90 days: **28.0** / **36.0** (n=273)
- Stock median / p90 days: **36.0** / **48.8** (n=143)

## Receivable stub (universe, report-only)

- Open cash events with ex≤asof < pay: **0**
- Codes: `none`
- Formal books (live DEFAULT E22_v3_recv_pay_tax10, Stage-B) accrue receivable on effective_ex_trade and cash on effective_payment (Stage-E timing family), with flat 10% withhold. TAX0 sibling: E22_v3_recv_pay_effdelay. Preserved cash-on-ex path: E22_v2s_tw_effex. This count is universe-level timing exposure vs custody pay-date, not position-weighted PnL.

## Dividend tax sensitivity (report-only; live DEFAULT = tax10)

- No dividends_applied.csv yet — tax sensitivity deferred until live applies cash events.

## Odd-lot / D5 (`E22_v2s_tw` → `E22_v2s_tw_effex`)

- Status: **PROMOTED** — code DEFAULT `E22_v3_recv_pay_tax10` (odd-lot promote path `E22_v2s_tw_effex`; legacy TW `E22_v2s_tw`)
- Ballot: `ACCEPT promote 2026-09-05; D5 effex ACCEPT 2026-09-16; Stage-E recv ACCEPT 2026-09-16; Stage-B tax10 ACCEPT 2026-09-19`
- Promote checklist: `research/ops/ODD_LOT_PROMOTE_CHECKLIST.md`

## Flags

- None

Monitoring KPI OK (code **and** live evidence): **True**
- code_ok: **True**
- live_evidence_ok: **True**
- ci_smoke_ok (= code_ok): **True**

Re-run: `python3 scripts/e22_gap6_fidelity_kpi.py`
