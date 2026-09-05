# Live vs Paper Soft-Frozen Recon

Generated: `2026-09-05T06:42:59.256702+00:00`
Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.50, 0.95] unchanged**.

## Coverage

| Book | Start | End | N | Last NAV |
|---|---|---|---:|---:|
| Live `forward/e21` | 2026-08-24 | 2026-09-04 | 10 | 3194823.7981686974 |
| Paper BASE | 2012-12-04 | 2026-09-04 | 3351 | 16695201.766628468 |
| Overlap | | | **10** | |

## Overlap indexed returns (rebased to 1.0 on first overlap date)

- Window: `2026-08-24` → `2026-09-04`
- Live cum return: **6.4941%**
- Paper BASE cum return: **8.7262%**
- Gap (live − paper): **-2.2320%**
- Max |indexed NAV gap|: **2.2320%**

## Alerts

- `INDEX_DRIFT: max |live_idx-paper_idx|=2.2320% > 2% on overlap`

## Ops note

- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`
- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`
- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.
