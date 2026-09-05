# E22 Data-Quality KPI

Generated: `2026-09-05T07:03:54.948015+00:00`
Status: **OPS / RESEARCH** — Soft-Frozen unchanged; E22_v2s remains formal books.

- Events: **150** (cash rows 144, stock rows 52)
- Cash payment-date blank rate: **0.00%**
- Cash ex-date blank rate: **0.00%**
- Stock payment-date blank rate: **0.00%**
- Stock ex-date blank rate: **0.00%**
- KPI OK: **True**

## Flags

- None

## Note

- Timing policy for formal books remains ex-date based (see `e22_v2s_formal_status.json`).
- Payment-date completeness is an ops completeness KPI, not a Soft-Frozen gate.
- Re-run: `python3 scripts/e22_data_quality_kpi.py`
