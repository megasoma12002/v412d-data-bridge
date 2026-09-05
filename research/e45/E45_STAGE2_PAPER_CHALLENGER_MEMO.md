# E45 Stage-2 Paper Challenger Memo (Exact T+1)

Date: 2026-09-05  
Status: **PAPER / RESEARCH ONLY** — not a promote; live stitch **FORBIDDEN**  
Charter: **ACCEPT** → Stage 1–2 OPEN (`research/ops/E45_STAGE12_STATUS.md`)  
Soft-Frozen clip: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**

Source refresh: `scripts/e45_verify_mdd_1316.py` →  
`research/e45/E45_MDD_1316_VERIFICATION.json` · `repro/e45-mdd-verify/`  
Generated: `2026-09-05T18:10:35Z`

## Honest claim label

| Claim | Status |
|---|---|
| Handoff/spec MDD ≈ **−13.16%** (−0.1316) | **`NOT_VERIFIED`** — `exact_artifact_match=false` |
| Invented replacement MDD | **Forbidden** |
| Use instead | Dated **verified lineage** + **early-stack challenger** MDDs below |

## Verified lineage (validation gates)

| Source | Closest / best MDD | |err| vs −13.16% |
|---|---:|---:|
| E1.1 validation | **−15.81%** | 2.65 pp |
| E1 validation | −17.12% | 3.96 pp |
| E2.1 validation | −17.88% | 4.72 pp |
| E3 locked winner validation | **−18.49%** | 5.33 pp |
| E2 validation | −21.68% | 8.52 pp |

## Early-stack Exact T+1 challengers (recomputed)

| Variant | CAGR | MDD | |err| vs claim |
|---|---:|---:|---:|
| E16+E18+E22_v2 | 11.25% | −22.11% | 8.95 pp |
| E16+E18+E22_v2s | 13.78% | −22.64% | 9.48 pp |
| **E16+E18+E22_v2s+E45_E3** | **10.79%** | **−20.76%** | 7.60 pp |
| E16+E18+E22_v2s+E45_E1 | 13.14% | −22.64% | 9.48 pp |
| E16+E18+E22_v2s+E45_LEGACY0.7 | 12.79% | −20.62% | 7.46 pp |

Interpretation for paper observe: E45_E3 overlay **reduces** early-stack CAGR and leaves MDD near **−21%**, still far from narrative −13.16%. This is a **challenger observation**, not a Soft-Frozen or live authorization.

## V-bar implications

- **V1 FAIL** (no artifact match for −13.16%) ⇒ stitch blocked  
- **V2 PASS (labeled)** — this memo is the honest label surface  
- **V3 PASS** on shared Exact T+1 path  
- **V4/V5 PARTIAL** — cost / multi-crisis seal packs still open  
- **V6 PASS** — Soft-Frozen untouched  

## Explicit non-actions

- No live-wire into `forward/e21`  
- No Soft-Frozen flip  
- No history rewrite  
- No claim that Soft-Frozen_CRITICAL proves −13.16%  

## Next

1. Optional Stage 3: dual-paper observe sleeve design checklist  
2. Cost/stress pack to close V4  
3. **Do not** open stitch PR until V1–V6 all PASS + second human ACCEPT  

## Label

`E45_STAGE2_PAPER_CHALLENGER_MEMO_2026-09-05__NOT_VERIFIED_CLAIM__STITCH_FORBIDDEN`
