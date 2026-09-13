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

## Bulky dumps

`repro/.gitignore` ignores bulky `*fills*` / `*daily_nav*` CSVs under `outputs/`.
Root `.gitignore` mirrors the same for `archive/repro/**/outputs/`.
Batch C removed force-tracked ARCHIVE densify dumps from the git index; regenerate
from paired research notes + scripts when needed.

Hygiene note: `research/ops/REPO_HYGIENE_REPRO_BATCH_C_2026-09-13.md`.
