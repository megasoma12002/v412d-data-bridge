# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-19T05:47:29.614749+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.60, 0.90] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-16 | 18 | 556847465.5135857 |
| Paper BASE | 2012-12-04 | 2026-09-16 | 3359 | 2619084324.9136333 |
| Overlap | | | **18** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-16`
- Live cum return: **11.3695%**
- Paper BASE cum return: **14.7045%**
- Gap (live − paper): **-3.3350%**
- Max |indexed NAV gap|: **3.3350%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=3.3350% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
- **INDEX_DRIFT non-decision** (ACCEPT Ops residual 全修 2026-09-19): thin overlap ≪ ~60 sessions — ops note only; do not open cutover on thin drift.
