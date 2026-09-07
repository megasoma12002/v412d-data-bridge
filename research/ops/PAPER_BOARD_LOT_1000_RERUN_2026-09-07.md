# Paper dual-ledger re-run — board-lot 1000 (2026-09-07)

Human: **「請重跑回測數據」** after paper default → 一張=1000 (#116).  
Soft-Frozen: **[0.50, 0.95] KEEP** · stitch **FORBIDDEN** · no `forward/e21` rewrite

## Command

```bash
python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers --continue-on-error
```

`all_ok: true` · `refresh_ledgers: true` · generated `2026-09-07T15:50:55Z`

## Regenerated observe ledgers

| Pack | Path |
|---|---|
| L4 | `repro/l4-dd-path-dual-paper/` |
| FIN50 | `repro/fincap50-dual-paper/` |
| BLEND_025 | `repro/blend025-dual-paper/` |
| E45 FULL | `repro/e45-dual-paper-observe/` |
| E45 A25 | `repro/e45-blend025-dual-paper-observe/` |
| E45 A05 | `repro/e45-blend005-dual-paper-observe/` |
| E45 sleeve-local | `repro/e45-sleeve-local-dual-paper-observe/` |
| E45 M2 BIL_FX C35 | `repro/e45-m2-bil-fx-dual-paper-observe/` |

All active observe fills: **qty multiples of 1000** (min 1000). Month-end monitors + live↔paper recon refreshed.

## Spot metrics (E45 dual-paper, full window)

| Book | CAGR | MDD |
|---|---:|---:|
| BASE_E16_E18_E22_v2s | ≈13.81% | ≈−22.39% |
| CHAL_E45_E3 | ≈11.84% | ≈−21.64% |

Tip NAV end `2026-09-07` (BASE) ≈ **16.76M** on 3M start capital.

## Hygiene

Removed supersession residue `m2_reloc_bil_fx_c50_*` under M2 observe outputs (locked challenger is **C35**; stale 1-share C50 fills would mislead).

Historical research trees outside this pack (e.g. true-DEF grids) were **not** re-run — still 1-share until explicitly regenerated.

## Definitions

`research/ops/TW_SHARE_LOT_DEFINITIONS.md` — 一張=1000 / 零股=1–999 / 畸零股=0.x→面額.
