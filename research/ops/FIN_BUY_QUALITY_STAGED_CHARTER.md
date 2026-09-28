# FIN buy-quality Stage D — Composite regime decision (paper)

Date: 2026-09-28  
Status: **Stage D DONE — `PARENT_KEEP_B`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `COOL_c8` **KEEP** · no live wire  
Parents: Stage C `C_OR_K9_AND_BELOW_MA60` (full-sample Pareto) · Stage B `P_B_OR_K9` (2020 crisis MDD)  
Human intent:

```
OPEN Stage D: FIN buy-quality · composite regime · C normal / B crisis · paper only
```

Label: `FIN_BUY_QUALITY_STAGED_CHARTER_2026-09-28__OPEN__NO_LIVE_WIRE`

## Why Stage D

| Book | Full-sample | 2020 COVID MDD vs CTRL |
|---|---|---|
| C hybrid | **HYBRID_PARETO** (CAGR+WR) | ~flat (+0.06pp) |
| B `MA120∨K9` | HIT but lower CAGR | **strong** (~+2.0pp) |

Stage D tests **finite regime switches**: use C buy-gate in calm; switch to B buy-gate under crisis signals — aiming to keep C's full-sample edge **and** recover B's crash MDD.

## Question

On `BASE_LIVE_FUSE_COOL`, does ≥1 composite:

1. clear full-sample HIT (CAGR≥+0.15 · MDD near-flat · tip≥0 · WR↑≥+1.0pp), **and**
2. improve 2020 COVID-window MDD vs CTRL by ≥ **+1.0pp**?

Optional Pareto: full HIT + stress≥+1.0 **and** held CAGR within **0.30pp** of parent C.

## Non-actions

- Soft-Frozen / Exact T+1 / tip rewrite · live wire · broker  
- Sell-side overlays · unbounded signal search  

## Grid (finite)

| ID | Calm gate | Crisis gate | Crisis fire |
|---|---|---|---|
| `CTRL_BASE` | live | — | — |
| `P_C` | C always | — | — |
| `P_B` | B always | — | — |
| `D_C_B_COOL` | C | B | cool exposure &lt; 1 |
| `D_C_B_MDD8` | C | B | proxy MDD63 ≤ **−8%** |
| `D_C_B_MDD10` | C | B | proxy MDD63 ≤ **−10%** |
| `D_C_B_COOL_OR_MDD8` | C | B | cool&lt;1 **or** MDD63≤−8% |
| `D_C_B_RET21_N5` | C | B | 0050 21d ret ≤ **−5%** |
| `D_C_B_MDD8_H5` | C | B | MDD63≤−8% with **5-day** hold once fired |

C = `BELOW_MA120 ∨ (K9∧BELOW_MA60)` · B = `BELOW_MA120 ∨ K9`

## Verdicts

| Verdict | Meaning |
|---|---|
| `COMPOSITE_PARETO` | HIT + stress≥+1.0pp + CAGR within 0.30pp of `P_C` |
| `COMPOSITE_HIT` | HIT + stress≥+1.0pp |
| `COMPOSITE_SOFT` | stress helps vs `P_C` but short of HIT/stress floor |
| `PARENT_KEEP_C` | no composite beats keeping C |
| `PARENT_KEEP_B` | only always-B clears stress; full-sample prefers B |
| `MDD_BLOCK` / `NO_LIFT` | fail |

Even HIT → **paper observe ballot only**.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_buy_quality_staged.py
```

Artifacts: `research/ops/FIN_BUY_QUALITY_STAGED_*` · `repro/fin-buy-quality-staged/`
