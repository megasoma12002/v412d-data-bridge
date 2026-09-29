# FIN×SAT Path3 T0-decision × T1-fill hybrid Stage A (paper)

Date: 2026-09-28  
Status: **Stage A DONE — `T0_SAMEBAR_ONLY`** · Soft-Frozen **KEEP** · Exact T+1 fills **KEEP** · Path3 observe **KEEP** · live CONF α=0.10 **KEEP** · no live wire  
Parents: 0k9q `T0_ONLY_EDGE` · 0k9r Path3 observe OPEN · carve `T0_CARVE_FIN_SAT_SWITCH`

Human intent (normalized):

```
OPEN Stage A: backtest Path3 with T+0 switch decision but Exact T+1 fills (hybrid) vs same-bar P3_T0_STATE · Soft-Frozen KEEP · paper only
```

## Question

Live carve-out is **not** “all fills become T+0”.  
Realistic live Path3 = **same-day switch decision** (trail known at close) + **Exact T+1 fill** (weight first applies next session).  
Paper `P3_T0_STATE` observe is the stronger **same-bar NAV** counterfactual. This Stage A measures the hybrid gap.

## Books（finite）

| ID | definition | Soft-Frozen fill |
|---|---|---|
| `CTRL_LIVE_A10` | live base | Exact T+1 KEEP |
| `P3_T0_STATE` | `w_t = SAT_LEAD_t` on return `r_t`（same-bar） | ❌ leakage upper bound |
| `P3_HYBRID_T1_FILL` | `w_t = SAT_LEAD_{t-1}` on `r_t`（decision close t−1 → earn t） | ✅ Exact T+1 switch fill |
| `R_SAT_LEAD_L1` | alias of hybrid（0k9q ref） | ✅ |
| `P2_SAT_PURE` | always SAT | ✅ tip line |

`SAT_LEAD_t := trail_rel_63(COMP−SAT)_t ≤ −0.01`.

## Gates

Same HIT shape as 0k9q: tip-clean + held CAGR↑≥+0.10 + vsSAT+0.05 + held MDD near-flat/band.  
Hybrid is `sf_ok=true` (Exact T+1 fill). Same-bar T0 remains `sf_ok=false` counterfactual.

## Verdicts

`HYBRID_HIT` / `HYBRID_SOFT` / `HYBRID_TIP_BLOCK` / `T0_SAMEBAR_ONLY`

## Non-goals

- Soft-Frozen clip flip · live wire · expand carve-out · rebuild full sleeve simulator  
- Do not close Path3 observe from this Stage A alone

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/fin_sat_path3_t0_t1_hybrid_stagea.py
```

Register: **0k9s**
