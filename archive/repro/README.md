# archive/repro — physical home for ARCHIVE research dumps

**Policy:** 封存 = retain evidence, no new expansion, not a live decision driver.
Prefer `git mv repro/<track> → archive/repro/<track>` and leave a thin `POINTER.md`
at the old path. Do **not** delete irreplaceable manifests/reports.

## KEEP denylist (stay under `repro/`)

- `soft-assist-dual-paper-observe`
- `sleeve-tilt-dual-paper-observe`
- `fuse-additive-dual-paper-observe`
- `blend025-dual-paper` (**FINCAP** BLEND_025 — ≠ E45_BLEND025)
- `fin-priv-native-dual-paper-observe`
- `fin-within-sleeve-dual-paper-observe`
- `e45-defend-handoff-dual-paper-observe` · `e45-defend-handoff-stagea`
- `dh-observe-combo-nav-trial`
- `fincap50-dual-paper` · `l4-dd-path-dual-paper` · `e50a-dual-track`
- `kelly-exposure-stagea` · `live-leverage-combo-trial`
- tip Soft / LIVE_OVERRIDE / live-stack race observes (`tipsoft-ip3-*`)
- operating dual-paper observes still on month-end (`cool-c8-proxy-dual-paper-observe`, COMPOSITE / Path3, …)

## Batch D ARCHIVE moves (2026-10-01)

- `cool-t50-lev-rebound-stagea` · `fin-sell-new-mech-stagea`
- `etf0050-regime-detector-stagea` · `fin-sell-quality-stagea` · `fin-sell-quality-stageb`
- `tel-both-quality-stagea`

## Bulky dumps

`repro/.gitignore` ignores bulky `*fills*` / `*daily_nav*` CSVs under `outputs/`
(including nested `outputs/<sub>/`). Root `.gitignore` mirrors for `archive/repro/**/outputs/`.
Batch C + Batch D removed ignore-shaped force-tracked dumps from the git index; regenerate
from paired research notes + scripts when needed.

Hygiene: `research/ops/REPO_HYGIENE_REPRO_BATCH_C_2026-09-13.md` ·
`research/ops/REPO_HYGIENE_REPRO_BATCH_D_2026-10-01.md`.
