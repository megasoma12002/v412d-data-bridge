# E45 Naming Consistency Fix — 2026-09-06

Status: **SCRIPT HYGIENE** — Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN

## Canon (source: `scripts/e45_paper_harness.py`)

| Concept | Canonical | Banned fork |
|---|---|---|
| Claim status const | `CLAIM_STATUS` | paper-script `CLAIMED_MDD_STATUS` (crisis_core may still own the source attr) |
| Profile const | `E45_PROFILE_DEFAULT` | local `E45_PROFILE = ...` |
| MDD delta key | `mdd_improve_pp` | `mdd_help_pp` |
| Sealed window key | `sealed_2023_plus` | `sealed_2023_latest` |
| Observe FIN sleeve book | `SLEEVE_FIN_ONLY_A10` | calling the *observe* sleeve `FIN_ONLY_A10` |
| Paper FIN densify book | `FIN_ONLY_A10` | (keep for paper sims) |

## What changed

- E45 paper ledgers/screens use `E45_PROFILE_DEFAULT` + `CLAIM_STATUS` from harness.
- Non-harness crisis_core consumers keep `e45.CLAIMED_MDD_STATUS` (source attr ownership).
- Five-research batch emits `mdd_improve_pp` (CSV column updated).
- Observe prose distinguishes `SLEEVE_FIN_ONLY_A10` vs paper `FIN_ONLY_A10`.
- Heldout/sealed decision writers use `sealed_2023_plus`; monitor keeps legacy-key read fallback.
- `check_e45_paper_hygiene.py` bans the forks above.

## Non-actions

- No Soft-Frozen / DEFAULT / stitch change.
- No retired-narrative reinvention.
- `oof_2012_2018` left intact where it is an intentional MDD-L1 window (not an E45 WINDOWS_STANDARD fork to silently rewrite).

Label: `E45_NAMING_CONSISTENCY_2026-09-06__STITCH_FORBIDDEN`
