# E22 Data-Quality KPI

Generated: `2026-09-23T13:49:09.574092+00:00`
Status: **OPS / RESEARCH** — Soft-Frozen unchanged; E22_v2s remains formal books.

- Events: **150** (cash rows 144, stock rows 52)
- Cash payment-date blank rate: **20.14%**
- Cash ex-date blank rate: **0.00%**
- Stock payment-date blank rate: **100.00%**
- Stock ex-date blank rate: **0.00%**
- KPI OK: **False**

## Flags

- cash_payment_date_blank_rate>2%

## Note

- Timing policy for formal books remains ex-date based (see `e22_v2s_formal_status.json`).
- Payment-date completeness is an ops completeness KPI, not a Soft-Frozen gate.
- Re-run: `python3 scripts/e22_data_quality_kpi.py`
