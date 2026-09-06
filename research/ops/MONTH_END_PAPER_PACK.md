# Ops Month-End Paper Pack

Generated: `2026-09-06T10:05:41.416055+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen **[0.50, 0.95] unchanged**; no cutover.

- Refresh ledgers: **False**
- All steps OK: **False**

| Step | OK | Exit |
|---|---|---:|
| `l4_month_end` | True | 0 |
| `fincap50_month_end` | True | 0 |
| `blend025_month_end` | True | 0 |
| `e45_month_end` | True | 0 |
| `e45_blend025_month_end` | True | 0 |
| `e45_blend005_month_end` | True | 0 |
| `e45_sleeve_local_month_end` | True | 0 |
| `track_a_s9a1` | True | 0 |
| `live_paper_recon` | True | 0 |
| `e22_data_quality_kpi` | True | 0 |
| `e22_gap6_fidelity_kpi` | False | 2 |

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
