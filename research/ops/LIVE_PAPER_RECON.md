# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-07T15:50:28.917527+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.50, 0.95] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-07 | 11 | 3163015.0756295016 |
| Paper BASE | 2012-12-04 | 2026-09-07 | 3352 | 16692847.711478008 |
| Overlap | | | **11** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-07`
- Live cum return: **5.4338%**
- Paper BASE cum return: **9.3666%**
- Gap (live − paper): **-3.9328%**
- Max |indexed NAV gap|: **3.9328%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=3.9328% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
