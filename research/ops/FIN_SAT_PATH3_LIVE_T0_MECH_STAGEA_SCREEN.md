# FIN_SAT_PATH3_LIVE_T0_MECH_STAGEA_SCREEN

Date: 2026-09-29 · `2026-09-29T00:07:27Z` · Verdict: **`ORACLE_ONLY`**
Soft-Frozen KEEP · global Exact T+1 KEEP · Path3 observe KEEP · no live

## Live Exact T+1 guards (binding)

- `paper_open_fill` — `scripts/live_fill_core.py::PaperOpenFillPort`: fill prior pending at today's open
- `pending_signal_lt_latest` — `scripts/live_fill_core.py::_iter_pending`: signal_date < latest only (blocks same-bar pending)
- `exact_t1_stats` — `scripts/live_fill_core.py::_exact_t1_stats`: fill_date <= signal_date counts as same_bar
- `pipeline_raise` — `scripts/e21_forward_pipeline.py`: raises if exact_t1_ok is False
- `qc_exact_t1` — `scripts/e21_qc.py`: qc_status.exact_t1_ok fail-closed

## Head-to-head

| Book | sf_ok | held↑ | MDD↑ | tipY↑ | tip1y↑ | tipClean | shaped | score |
|---|---|---:|---:|---:|---:|---|---|---:|
| `CTRL_LIVE_A10` | True | -0.0 | 0.0 | 0.0 | 0.0 | True | False | 1.0 |
| `ORACLE_SAMEBAR` | False | 3.4758 | 0.0996 | 2.7325 | 1.7356 | True | True | 8.6243 |
| `T1_OPEN` | True | 1.2962 | 0.0996 | -8.4925 | -5.7336 | False | False | -5.154 |
| `MOC_F25` | True | 1.6566 | 0.0996 | -5.9784 | -4.0473 | False | False | -4.7936 |
| `MOC_F50` | True | 1.8244 | 0.0996 | -4.7113 | -3.2004 | False | False | -4.1928 |
| `MOC_F75` | True | 1.7178 | 0.0996 | -6.0186 | -4.0742 | False | False | -4.7324 |
| `P2_SAT_PURE` | True | 0.3343 | -0.3084 | 0.6801 | 0.7413 | True | False | 2.2002 |

Best MOC: `MOC_F50`

Repro: `repro/fin-sat-path3-live-t0-mech-stagea/`

