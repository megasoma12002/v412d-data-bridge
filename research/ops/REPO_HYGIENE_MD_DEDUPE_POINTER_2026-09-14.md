# Repo hygiene — MD dedupe / POINTER (2026-09-14)

## Goal

Remove byte-identical Markdown copies. Leave one canonical body; replace duplicates
with a thin `POINTER` stub. **Do not rewrite historical clip numbers.**

## Policy

| Role | Location |
|---|---|
| **Canonical (E45 research)** | `research/e45/<NAME>.md` |
| **Ops stub** | Keep short ops-only stubs that already say `Primary:` / run commands |
| **Duplicate → POINTER** | Identical copies under `research/ops/`, `repro/**/reports/`, `archive/repro/**` |

## Done

- Replaced **57** byte-identical copies with `# POINTER` → canonical path.
- Left **distinct** ops stubs (ballot / repro path / regenerate commands) alone.
- Left near-duplicates with different hashes alone (no silent content merge).
- Machine manifest: `REPO_HYGIENE_MD_DEDUPE_POINTER_2026-09-14.json`.

## Not done

- Merging near-duplicate files that differ only by banners or prose drift.
- Collapsing rich ops stubs into bare POINTERs (would lose regenerate commands).
- Moving kelly / large repro trees; LFS / history rewrite.
- Any `LIVE_*` / historical `[0.50, 0.95]` decision-record edits.

## Label

`REPO_HYGIENE_MD_DEDUPE_POINTER_2026-09-14__IDENTICAL_COPIES_ONLY`
