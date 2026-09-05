# E45 Official Status (Authoritative)

Date: 2026-09-05  
Authority: artifact verification `research/ops/E45_ARTIFACT_VERIFICATION_2026-09-05.md`  
             + MDD scan `research/e45/E45_MDD_1316_VERIFICATION.md`  
             + ballot Register #6 Item 3 **DEFER stitch path**

## Official status constants

```
E45_ARTIFACT_STATUS     = NOT_VERIFIED
E45_STITCH_STATUS       = DEFERRED
E45_GOVERNANCE_CLASS    = SOFT_FROZEN_CRITICAL
E45_LIVE_AUTHORIZATION  = NO
```

Live DEFAULT books (unchanged): **`E22_v2s_tw`**  
E45 strategy logic / parameters: **unchanged**  
Promote / reject: **neither** — Soft-Frozen CRITICAL kept; stitch deferred

## Historical narrative claim (preserved, not deleted)

| Field | Value |
|---|---|
| Historical handoff/spec figure | validation MDD ≈ **−13.16%** (−0.1316) |
| Corrected label | **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** |
| Why | No dated research CSV/JSON MDD equals −0.1316 (scan 2026-09-04; reconfirmed 2026-09-05) |
| Rule for agents | **Do not** treat −13.16% as a verified baseline, PASS evidence, or stitch gate |

## Currently verified dated-artifact values

| Metric | Value | Notes |
|---|---:|---|
| Closest lineage validation MDD | **−15.81%** | E1.1 validation gate |
| E3 locked winner validation MDD | **−18.49%** | E3 validation (pass, not promoted) |
| Early-stack + E45_E3 MDD | **−20.76%** | Challenger path; not a frozen baseline |
| Early-stack + E45_E3 CAGR | **~10.79%** | Challenger path; not a frozen baseline |

Prefer these dated figures over any narrative −13.16%.

## Lineage distinction (mandatory)

### DOCUMENTED RESEARCH LINEAGE

```
E38 → E43 → E44 → E45
```

Crisis classification → state handoff → Exact T+1 clock audit → single executable crisis core.  
This is the **documented research narrative**. It is preserved.

### IMPORTABLE CODE LINEAGE (observed in repo)

```
E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper
```

Scripts: `v412e1_*`, `v412e11_*`, `v412e2_e3_*`, `e45_crisis_core.py`.  
There is **no** separate importable `e38` / `e43` / `e44` package.

Agents must not conflate the two lineages.

## What future agents must not do

- Treat −13.16% as verified fact  
- Soft-Frozen flip or live-wire E45 without a new human ballot + PASS evidence  
- Invent a replacement MDD  
- Modify E45 parameters in place  
- Change `DEFAULT_BOOKS_VERSION` / live DEFAULT as part of E45 work  

## Pointers

- Artifact verification: `research/ops/E45_ARTIFACT_VERIFICATION_2026-09-05.md`  
- MDD scan: `research/e45/E45_MDD_1316_VERIFICATION.md`  
- Stitch ballot: `research/ops/E45_LIVE_STITCH_DECISION_PACK.md` (DEFER)  
- Governance: `FROZEN_GOVERNANCE.md` §E45  
- Spec: `FROZEN_STRATEGY_SPEC.md` Layer 4  

## Label

`E45_OFFICIAL_STATUS_2026-09-05__NOT_VERIFIED__DEFERRED__SOFT_FROZEN_CRITICAL`
