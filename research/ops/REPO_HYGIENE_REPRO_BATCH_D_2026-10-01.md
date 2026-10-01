# Repo hygiene Batch D — repro slim (safe) (2026-10-01)

## Goal

Shrink git-tracked `repro/` **without** breaking KEEP / live / tipsoft / dual-paper observe paths.
No history rewrite (BFG). Soft-Frozen / Exact T+1 / broker **untouched**.

Priors: Batch C `REPO_HYGIENE_REPRO_BATCH_C_2026-09-13.md` · `REPRO_DEDUPE_HYGIENE.md` · `archive/repro/README.md`

## Done

### Phase A — untrack ignore-shaped force-adds (~30 MB)

`git rm --cached` on **54** files that already matched `repro/.gitignore` bulky patterns
(`*fills*` / `*daily_nav*` / `fill_extreme_detail`) but were still in the index.

| Tree | Files | ~MB |
|---|---:|---:|
| `mdd-loss-engine/` | 21 | 14.0 |
| `e22-v2s-cil-historical-recompute/` | 6 | 3.7 |
| `e22-v2s-historical-recompute/` | 6 | 3.6 |
| `e22-stock-div-research/` | 5 | 3.2 |
| `e22-tw-odd-lot-apply/` | 3 | 2.2 |
| `fincap50-go-live-verify/` | 2 | 1.5 |
| `gap5-6-continuation/` | 5 | 1.3 |
| `e50a3r1-audit-20260903/` (nested `outputs/a3*/daily_nav.csv`) | 2 | 0.4 |
| `e50a3r1-turnover-diagnosis-20260903/` | 2 | 0.2 |
| `live-fill-extreme-audit/` | 2 | 0.1 |

Files remain on local disk (gitignored). Each tree got `POINTER_UNTRACKED_DUMPS.md`.

**gitignore fix:** nested `**/outputs/**/*daily_nav*.csv` (and fills / fill_extreme) so
`outputs/<sub>/daily_nav.csv` stays ignored after uncache. Root `.gitignore` mirrors for
`archive/repro/`.

### Phase B — ARCHIVE closed Stage A trees (~77 MB tracked)

`git mv` → `archive/repro/<tree>/` + thin `repro/<tree>/POINTER.md`. Script `REPRO` retargeted.

| Tree | Verdict | Script |
|---|---|---|
| `cool-t50-lev-rebound-stagea` | `MDD_BLOCK` | `cool_t50_lev_rebound_stagea.py` |
| `fin-sell-new-mech-stagea` | `MDD_BLOCK` | `fin_sell_new_mech_stagea.py` |
| `etf0050-regime-detector-stagea` | `NO_EDGE` | `etf0050_regime_detector_stagea.py` |
| `fin-sell-quality-stageb` | `NO_EDGE` | `fin_sell_quality_stageb.py` |
| `fin-sell-quality-stagea` | `MDD_BLOCK` | `fin_sell_quality_stagea.py` |
| `tel-both-quality-stagea` | `NO_EDGE` | `tel_both_quality_stagea.py` |

No month-end / ACCEPT / cutover / live refs. Charter artifact paths updated to `archive/repro/…`.

## KEEP denylist (not touched)

See `archive/repro/README.md`. Also protected this pass: tipsoft LIVE_OVERRIDE /
live-stack race, `cool-c8-proxy-dual-paper-observe`, and other `*-dual-paper-observe`
operating ledgers whose `*daily_nav*` remain force-tracked for month-end.

## Explicitly not done

- Mass untrack of `outputs/nav_*.csv` SSOT (~462 MB) — would break `test_repro_dedupe_hygiene` / fresh-clone month-end samples without policy redesign.
- Git LFS / history rewrite to reclaim packfile blobs.
- Moving KEEP denylist / tipsoft / Path3 observe trees.

## Estimated tracked savings

- **Phase A:** ≈ **~30 MB** off the git index (files stay local-ignored on disk).
- **Phase B:** relocates ≈ **~77 MB** into `archive/repro/` (still tracked — organizational ARCHIVE, not byte deletion).
- `.git` pack size unchanged until (disallowed) history rewrite.

Working-tree tracked content after this pass: ≈ **659 MB** (was ≈ **689 MB**).

## Safety / rollback

| Risk | Mitigation |
|---|---|
| Need an uncached dump | Local file still present if not deleted; or regenerate from paired script; or `git show <pre-D>:<path>` |
| Archive path missing | Thin `POINTER.md` at old `repro/<tree>/`; scripts use `archive/repro/…` |
| Soft-Frozen / tip / broker | Untouched |
| Undo | `git revert` (no filter-repo / force-push) |

## Label

`REPO_HYGIENE_REPRO_BATCH_D_2026-10-01__UNTRACK_IGNORE_SHAPED__ARCHIVE_CLOSED_STAGEA`
