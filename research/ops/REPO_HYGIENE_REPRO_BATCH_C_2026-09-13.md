# Repo hygiene Batch C — repro ARCHIVE slim (2026-09-13)

## Goal

Shrink git-tracked `repro/` without breaking KEEP / live month-end paths.
On-disk ignored CSVs stay local-regenerable; force-tracked ARCHIVE densify
fills/nav leave the index.

## Done

1. **`git rm --cached`** ARCHIVE densify `*fills*` / `*daily_nav*` CSVs under E45 densify /
   archived dual-paper trees (~125MB tracked content). Files remain gitignored;
   manifests/reports stay tracked.
2. **`archive/repro/`** convention + README KEEP denylist.
3. **Physical moves** (thin `POINTER.md` at old path):
   - `e45-sleeve-local-deep-dive`
   - `e45-cheap-protect-cost-data`
   - `e45-c35-soft-gate-20260908`
   - `e45-novel-strategy-20260908`
   - `e45-softa-c35-mix-20260908`
   - `e45-four-path-recover-20260908`
   - `e45-next-research-batch`
4. Research notes + regenerator scripts retargeted to `archive/repro/...`.
5. `POINTER_UNTRACKED_DUMPS.md` on densify trees that stayed under `repro/` after untrack.
6. Root `.gitignore` mirrors bulky dump ignores under `archive/repro/**/outputs/`.

## KEEP denylist (not touched)

See `archive/repro/README.md`. Includes FINCAP `blend025-dual-paper`, Soft/Sleeve/FUSE
observes, DH dual-paper, kelly (path still referenced by leverage trial), etc.

## Explicitly not done

- Git LFS / history rewrite (BFG) to reclaim blob history.
- Moving kelly / large m1–m3 relocate trees (path refs + residual tracked size).
- Deleting ignored local CSVs on disk (developer optional reclaim).

## Label

`REPO_HYGIENE_REPRO_BATCH_C_2026-09-13__UNTRACK_ARCHIVE_DENSIFY__ARCHIVE_REPRO_PILOT`
