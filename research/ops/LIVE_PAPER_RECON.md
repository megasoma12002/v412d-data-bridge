# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-10T10:15:00.625147+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.60, 0.90] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-09 | 13 | 538570722.172183 |
| Paper BASE | 2012-12-04 | 2026-09-09 | 3354 | 2809761941.485194 |
| Overlap | | | **13** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-09`
- Live cum return: **7.7141%**
- Paper BASE cum return: **9.6490%**
- Gap (live − paper): **-1.9348%**
- Max |indexed NAV gap|: **2.8645%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=2.8645% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
