# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-12T13:42:14.145537+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.60, 0.90] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-11 | 15 | 550396672.172183 |
| Paper BASE | 2012-12-04 | 2026-09-11 | 3356 | 2886305146.0471025 |
| Overlap | | | **15** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-11`
- Live cum return: **10.0793%**
- Paper BASE cum return: **12.6360%**
- Gap (live − paper): **-2.5567%**
- Max |indexed NAV gap|: **2.8645%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=2.8645% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
