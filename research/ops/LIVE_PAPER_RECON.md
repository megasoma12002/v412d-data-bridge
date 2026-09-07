# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-07T17:02:55.325643+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.50, 0.95] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-07 | 11 | 16027790.182171628 |
| Paper BASE | 2012-12-04 | 2026-09-07 | 3352 | 87618970.90699138 |
| Overlap | | | **11** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-07`
- Live cum return: **6.8519%**
- Paper BASE cum return: **9.7731%**
- Gap (live − paper): **-2.9212%**
- Max |indexed NAV gap|: **2.9212%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=2.9212% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
