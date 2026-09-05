# v412d-data-bridge

Research continuation of the V4.12 / E50 program.

## Start here

| Need | Open |
|---|---|
| **Ops / what is live** | `research/ops/OPS_STATUS.md` |
| **Ops convergence plan** | `research/ops/OPS_CONVERGENCE_CHARTER.md` |
| **Now / Next / cutover matrix** | `research/STRATEGY_DEBT_BOARD.md` |
| Governance (class ≠ live) | `FROZEN_GOVERNANCE.md` |
| Role architecture (not live wiring) | `FROZEN_STRATEGY_SPEC.md` |
| Research rules | `E50_RESEARCH_OPERATING_RULES.md`, `CURSOR_RULES.md` |

**Live today:** E16 + Exact T+1 E18 + E22_v2s only. Soft-Frozen Financial clip **[0.50, 0.95]**. No overlay auto-wire. Dual-paper ≠ cutover.

HARD_FROZEN is the research-correctness floor. SOFT_FROZEN is the current official E16 / E18 / E22 / E45 strategy **class** (not proof of live wiring). E45 is also SOFT_FROZEN_CRITICAL. New models, thresholds, weights, routers, rebalancing, bootstrap cutoffs, model-selection rules, and acceptance gates are EXPERIMENTAL. Do not overwrite prior frozen baselines.

Formal handoff verification (2026-09-03): `E50_HANDOFF_VERIFICATION.md`.  
Decision: **HANDOFF_COMPLETE_WITH_WARNINGS**. Do not start unconstrained performance tuning. Do not modify frozen baselines without a human cutover PR.
