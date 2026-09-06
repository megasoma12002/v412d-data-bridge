# E45 MDD ≈ −13.16% Verification

Generated: `2026-09-05T18:10:35.778629+00:00`  
**Follow-on (2026-09-05):** human **RETIRE narrative (path A)** — see `research/ops/E45_MDD_1316_NARRATIVE_RETIREMENT.md`

**Scan verdict: `NOT_VERIFIED` (no exact artifact match)**  
**Claim policy after retirement: `RETIRED_HISTORICAL_NARRATIVE` / `EARLY_NON_RIGOROUS_RESEARCH_RESULT`**

Do **not** cite −13.16% as a verified E45 baseline, Soft-Frozen proof, live badge, or stitch gate.  
Comparable figures: dated lineage (primary **E1.1 −15.81%**) and/or dated challenger MDDs only — **no invented replacement**.

## Claim

Handoff / `FROZEN_STRATEGY_SPEC.md`: E45 crisis core MDD ≈ **-13.16%** (`-0.1316`) — **retired narrative**.

## Method

1. Scan research CSV/JSON MDD fields for exact `-0.1316`
2. Summarize crisis lineage validation gates (E1 / E1.1 / E2 / E2.1 / E3)
3. Recompute early-stack NAV with named E45 profiles (challenger; not a promotion)

## Artifact scan

- Exact MDD match in research artifacts: **none**
- Claim text locations only: spec, governance, prior handoff audit, `e45_crisis_core.py` constant

## Lineage validation MDDs

| Source | Best MDD | Median | Closest to claim | |err| |
|---|---:|---:|---:|---:|
| E1_validation | -17.12% | -17.35% | -17.12% | 3.96 pp |
| E1_1_validation | -15.81% | -16.28% | -15.81% | 2.65 pp |
| E2_validation | -21.68% | -23.78% | -21.68% | 8.52 pp |
| E2_1_validation | -17.88% | -19.66% | -17.88% | 4.72 pp |
| E3_validation | -18.49% | -19.43% | -18.49% | 5.33 pp |

- E3 locked winner validation MDD: **-18.49%** (|err| to claim = 5.33 pp)

## Early-stack + E45 challenger (this repo path)

| Variant | CAGR | MDD | |err| to claim |
|---|---:|---:|---:|
| E16_E18_E22_v2 | 11.25% | -22.11% | 8.95 pp |
| E16_E18_E22_v2s | 13.78% | -22.64% | 9.48 pp |
| E16_E18_E22_v2s_E45_E3 | 10.79% | -20.76% | 7.60 pp |
| E16_E18_E22_v2s_E45_E1 | 13.14% | -22.64% | 9.48 pp |
| E16_E18_E22_v2s_E45_LEGACY0.7 | 12.79% | -20.62% | 7.46 pp |

## Decision

- Accept claim as verified baseline: `False`
- Invent replacement number: `False`
- Use instead: VERIFIED_LINEAGE_MDD from dated artifacts; keep claim labeled NOT_VERIFIED
- Promotion impact: E45 remains CHALLENGER_CANDIDATE; SOFT_FROZEN_CRITICAL is a process class, not a verified -13.16% number

Conclusion: No research CSV/JSON contains MDD == -0.1316. Claim appears only in narrative spec/handoff text. Closest crisis-lineage validation MDDs are more severe than the claim. Early-stack+E45 challenger MDDs remain near -21% to -23%. Do not treat -13.16% as a verified E45 baseline.

## Artifacts

- `research/e45/E45_MDD_1316_VERIFICATION.json`
- `repro/e45-mdd-verify/summary.json`
- `repro/e45-mdd-verify/outputs/`
- Script: `scripts/e45_verify_mdd_1316.py`

