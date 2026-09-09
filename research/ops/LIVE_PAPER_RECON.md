# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-09T12:52:49.234681+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.60, 0.90] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-08 | 12 | 541417221.781057 |
| Paper BASE | 2012-12-04 | 2026-09-08 | 3353 | 2848172500.2237167 |
| Overlap | | | **12** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-08`
- Live cum return: **8.2834%**
- Paper BASE cum return: **11.1479%**
- Gap (live − paper): **-2.8645%**
- Max |indexed NAV gap|: **2.8645%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=2.8645% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
