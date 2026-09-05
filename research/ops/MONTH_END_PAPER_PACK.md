# Ops Month-End Paper Pack

Generated: `2026-09-05T07:03:55.015343+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen **[0.50, 0.95] unchanged**; no cutover.

- Refresh ledgers: **False**
- All steps OK: **True**

| Step | OK | Exit |
|---|---|---:|
| `l4_month_end` | True | 0 |
| `fincap50_month_end` | True | 0 |
| `track_a_s9a1` | True | 0 |
| `live_paper_recon` | True | 0 |
| `e22_data_quality_kpi` | True | 0 |
| `ops_alert_scan` | True | 0 |

## Hard rules

- No Soft-Frozen flip
- Dual-paper / held-out PASS ≠ cutover license
- Never rewrite `forward/e21` history

## Re-run

```bash
python3 scripts/ops_month_end_paper_pack.py
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow
```

Authority: `research/STRATEGY_DEBT_BOARD.md`
