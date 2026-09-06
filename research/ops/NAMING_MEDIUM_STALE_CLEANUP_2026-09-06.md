# Naming Medium + Stale Artifact Cleanup — 2026-09-06

Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · E45 stitch **FORBIDDEN** · claimed −13.16% **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)

Label: `NAMING_MEDIUM_STALE_CLEANUP_2026-09-06__STITCH_FORBIDDEN`

## Scope

Follow-up to PR #87 (High script emitters) + PR #88 (review). This pass clears **Medium script forks** and **stale research/repro teaching** of old schema.

## Script Medium fixes

| Fork | Canon applied |
|---|---|
| Local `WINDOWS = { date(...) }` copies | `WINDOWS = WINDOWS_STANDARD` (or subset dict-comp from it) |
| `SOFT_FROZEN_CLIP = [LO, HI]` alias | import / use `SOFT_FROZEN_FIN_CLIP` |
| JSON emit `claim_mdd_status` | `claim_status` |

Hygiene bans added in `scripts/check_project_coding_hygiene.py` for the three forks above.

**Intentional keep:** `v412e0_historical_stress.py` non-E45 stress window map; monitor read fallback `sealed_2023_plus or sealed_2023_latest`; paper densify book id `FIN_ONLY_A10` ≠ observe `SLEEVE_FIN_ONLY_A10`.

## Non-script stale fixes

- Decision / monitor JSON: `sealed_2023_latest` → `sealed_2023_plus` (keys + window values)
- Claim teaching packs / briefs: claim status **`RETIRED_HISTORICAL_NARRATIVE`** (scan unmatched language may remain where it is a verification verdict, e.g. `FAIL_NOT_VERIFIED` / package id `E45_NOT_VERIFIED`)
- Observe OPERATING prose: `FIN_ONLY_A10 observe` → `SLEEVE_FIN_ONLY_A10`
- Review docs (`REPO_NAMING_*`, landmine reviews) left as historical findings (not rewritten)

## Non-actions

- No Soft-Frozen / DEFAULT / stitch ballot
- No −13.16% reinvention
- No live observe book flip
