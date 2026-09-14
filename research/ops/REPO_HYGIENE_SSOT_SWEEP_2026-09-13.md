# Repo hygiene — SSOT sweep (2026-09-13)

## Why

Entry docs (`README` / `HANDOFF` / `OPS_STATUS` / debt-board header / FROZEN live blurbs) still described
pre-FINBAND / pre-500M / pre-DH+FUSE live. Code SSOT was already correct after PR #227.

## Done (this sweep)

1. Synced entry SSOT to live: FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
2. Rewrote FUSE / DH postures to **LIVE WIRED** (+ paper shadow OK).
3. Cleaned portfolio KEEP binding lines post-cutover.
4. `.gitignore` for local `repro/live-stack-5m-trade-count/` scratch.

## Batch B / C (same hygiene PR, 2026-09-13)

- **B:** `REPO_HYGIENE_SSOT_BATCH_B_2026-09-13.md` — historical clip banners + binding SSOT fix.
- **C:** `REPO_HYGIENE_REPRO_BATCH_C_2026-09-13.md` — untrack ARCHIVE densify fills/nav; `archive/repro/` pilot moves.

## Follow-up (2026-09-14)

- **MD dedupe / POINTER:** `REPO_HYGIENE_MD_DEDUPE_POINTER_2026-09-14.md` (identical copies only; no historical number rewrite).

## Explicitly not done (needs separate ballot / careful PR)

- Git LFS / history rewrite to reclaim old repro blobs.
- Move kelly / large m1–m3 relocate trees.
- Touch `LIVE_*` flags in `e21_forward_pipeline.py`.

## SSOT pointers

| Need | Path |
|---|---|
| Live one-pager | `research/ops/OPS_STATUS.md` |
| Portfolio KEEP/ARCHIVE | `research/ops/RESEARCH_PORTFOLIO_KEEP_ARCHIVE.md` |
| DH+FUSE ACCEPT | `research/ops/LIVE_DH_FUSE_CUTOVER_BALLOT_EXECUTED_ACCEPT.md` |
| Live code | `scripts/e21_forward_pipeline.py` |

## Label

`REPO_HYGIENE_SSOT_SWEEP_2026-09-13__ENTRY_DOCS_FUSE_DH_POSTURE`
