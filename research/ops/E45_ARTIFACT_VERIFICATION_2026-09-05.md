# E45 Artifact-Level Verification Report (Read-Only)

Date: 2026-09-05  
Ballot context: Register #6 Item 3 — **DEFER stitch path** (not REJECT)  
Soft-Frozen class: **SOFT_FROZEN_CRITICAL KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP** (unchanged)  
E45 implementation: **NOT MODIFIED** during this verification

## Human ballot recorded

| Field | Value |
|---|---|
| Ballot | **E45 DEFER stitch path** |
| Keep class | **SOFT_FROZEN_CRITICAL** |
| Preserve lineage | **E38 → E43 → E44 → E45** research lineage retained |
| Reject E45? | **No** — research/orphan path stays open |
| Authorize live/stitch? | **No** while historical performance claims (incl. ~−13.16% validation MDD) remain **NOT_VERIFIED** |
| Default path | **Unchanged** |

## Final verdict

# `E45_NOT_VERIFIED`

Rationale: dated research artifacts do **not** contain MDD == −0.1316; closest lineage validation MDDs are **more severe**; early-stack+E45 challenger MDDs remain ~−21% to −23%; content-hash manifests for E45 NAV are missing; E38/E43/E44 are documented lineage, not separate importable packages. Module existence + Exact T+1 on the shared early-stack path are insufficient for stitch authorization.

Not chosen:
- `E45_VERIFIED_FOR_STITCH` — stitch gates fail (claim MDD unmatched; live attach forbidden)
- `E45_VERIFIED_WITH_WARNINGS` — primary stitch-relevant claim fails hard, not a soft warning
- `E45_REJECTED` — ballot explicitly keeps E45; Soft-Frozen CRITICAL class preserved

---

## Checklist results (artifact-level)

| Check | Result | Evidence |
|---|---|---|
| Exact implementation path | **PASS (located)** | `scripts/e45_crisis_core.py` (`CHALLENGER_CANDIDATE_NOT_PROMOTED`); packages E1/E1.1/E3 controllers; **not** live-wired into `forward/e21` |
| Exact T+1 integrity | **PASS on shared exec path** | Fills live in E18 / `scripts/e50_early_stack_combined_nav.py`; early-stack recompute reports `exact_t1_ok` / zero same-bar fills; E45 module emits exposure only |
| Crisis state transitions | **PARTIAL** | Documented E38→E43→E44→E45 narrative preserved; **code lineage** is E1 / E1.1 / E2 / E2.1 / E3 + E45 wrapper. **No** `e38`/`e43`/`e44` packages |
| Validation / OOS periods | **PASS (dated)** | E1/E1.1 val 2012–2014; E2 val 2015–2017; E2.1 val 2018–2020; E3 val 2021–2022 (pass, not promoted); E3 blind 2023–2025; final 2026 window opened after E3 val |
| MDD (~−13.16% claim) | **FAIL / NOT_VERIFIED** | `research/e45/E45_MDD_1316_VERIFICATION.json` — `exact_artifact_match=false`; closest E1.1 val **−15.81%**; E3 winner val **−18.49%** |
| CAGR | **PARTIAL** | Early-stack `E16+E18+E22_v2s+E45_E3` dated challenger CAGR **~10.79%**; no sealed E45-named frozen NAV baseline for handoff “~10%” as hash-pinned artifact |
| Turnover | **PARTIAL** | E3 train grid reports turnover (e.g. winner train_turnover present in lineage CSVs); no dedicated E45 stitch turnover KPI pack |
| Costs | **PARTIAL** | E3 cost sensitivity dated (fee multiples drag Blind returns materially); early-stack fees in fills; no E45-named sealed cost report for stitch |
| Recovery behavior | **PARTIAL** | Documented: E1 too defensive; E1.1 10/20-day ramp; E3 `up_days=20`, `min_hold=42`; exposure stats on early-stack path — not a sealed recovery KPI for −13.16% claim |
| Hashes / manifests / reproducibility | **FAIL for stitch** | Module has status manifest **without content hashes**; `repro/e45-mdd-verify/` summary exists; **no** sha256 pin of E45 NAV; logic recompute reproduces dated MDD table but is not hash-locked |

---

## Key numbers (from dated artifacts — not invented)

| Metric | Value | Source |
|---|---:|---|
| Claimed validation MDD | −13.16% (−0.1316) | Narrative / module constant — **NOT_VERIFIED** |
| Closest lineage val MDD | −15.81% | E1.1 validation gate |
| E3 locked winner val MDD | −18.49% | E3 validation |
| Early-stack + E45_E3 MDD | −20.76% | `repro/e45-mdd-verify` / verification JSON |
| Early-stack + E45_E3 CAGR | ~10.79% | same |
| DEFAULT books (live) | `E22_v2s_tw` | `scripts/e22_dividend_accounting.py` — unchanged |

---

## Artifacts consulted (read-only)

- `scripts/e45_crisis_core.py`
- `scripts/e45_verify_mdd_1316.py` (not re-run write mode; dated outputs reused)
- `scripts/e50_early_stack_combined_nav.py`
- `scripts/v412e1_crisis_buffer.py`, `v412e11_graduated_crisis.py`, `v412e2_e3_three_rounds.py`
- `research/e45/E45_MDD_1316_VERIFICATION.{md,json}`
- `repro/e45-mdd-verify/summary.json` + `outputs/`
- `FROZEN_GOVERNANCE.md` (SOFT_FROZEN_CRITICAL)
- `research/ops/E45_LIVE_STITCH_CHARTER.md` · `E45_LIVE_STITCH_DECISION_PACK.md`

---

## Explicit non-actions (this verification)

- Did **not** modify E45 parameters, thresholds, or live wiring  
- Did **not** Soft-Frozen flip  
- Did **not** change `DEFAULT_BOOKS_VERSION`  
- Did **not** invent a replacement −13.16%  
- Did **not** authorize stitch / live integration  
- Did **not** REJECT E45 as a research/crisis class  

## Next (only if humans reopen)

1. Produce hash-pinned E45-named NAV + period table that either matches a claim or replaces narrative claims with verified lineage MDDs  
2. Map documented E38/E43/E44 roles onto dated code/artifacts explicitly  
3. New ballot required before any live/stitch PR  

## Label

`E45_ARTIFACT_VERIFICATION_2026-09-05__E45_NOT_VERIFIED__DEFER_STITCH`
