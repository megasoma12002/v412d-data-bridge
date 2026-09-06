# MDD_1316 residue cleanup (engineering only)

Date: 2026-09-06  
Governance: **unchanged** (Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN)

## Intent

The unmatched handoff MDD narrative is already **`RETIRED_HISTORICAL_NARRATIVE`** (human path A, 2026-09-05).  
This PR removes **residual spellings** of that numeric claim from active constants, emitters, banners, and frozen prose — **without inventing a replacement**.

## Keep (retirement / verification pack only)

| Path | Role |
|---|---|
| `research/ops/E45_MDD_1316_NARRATIVE_RETIREMENT.md` | Binding retirement wording |
| `research/e45/E45_MDD_1316_VERIFICATION.{md,json}` | Artifact scan that justified retirement |
| `scripts/e45_verify_mdd_1316.py` | Verifier that still searches for the retired digit |
| `research/ops/E45_ARTIFACT_VERIFICATION_2026-09-05.*` | Dated audit trail |
| `repro/e45-mdd-verify/` | Verifier outputs |

## Cleared

- `scripts/e45_crisis_core.py`: `CLAIMED_MDD = None` (no float claim on module surface)
- Paper emitters / dual-paper boilerplate: status-only wording (“retired MDD narrative”)
- Frozen / debt-board banners: point at retirement pack; no numeric restatement
- Hygiene: `check_project_coding_hygiene.py` bans `13.16%` / `-0.1316` outside the pack above

## Comparable numbers (unchanged policy)

Use dated lineage / challenger MDDs only (`VERIFIED_LINEAGE_MDD` / `PRIMARY_COMPARABLE_MDD`).
