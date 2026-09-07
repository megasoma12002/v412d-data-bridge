# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-07T17:20:35.871448+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.50, 0.95] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-07 | 11 | 15982908.911468128 |
| Paper BASE | 2012-12-04 | 2026-09-07 | 3352 | 80104557.33581781 |
| Overlap | | | **11** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-07`
- Live cum return: **6.5527%**
- Paper BASE cum return: **9.2591%**
- Gap (live − paper): **-2.7064%**
- Max |indexed NAV gap|: **2.7064%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=2.7064% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
