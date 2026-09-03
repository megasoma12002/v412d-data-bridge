# START_CURSOR.md

Paste this into Cursor Agent after all files are in the repo.

---

Read these files completely, in this order:

1. `FROZEN_STRATEGY_SPEC.md`
2. `FROZEN_GOVERNANCE.md`
3. `E50_RESEARCH_HISTORY.md`
4. `CURSOR_RULES.md`
5. `HANDOFF.md`
6. `E50-A3-R1_TODO.md`

This is a continuation of an existing quantitative research project.

DO NOT redesign the portfolio from scratch.
DO NOT treat E50-A as the whole portfolio.
DO NOT modify frozen baselines.
DO NOT rebuild E50-A0/A1/A2 unless you identify a reproducible upstream defect.
DO NOT relax HARD_FROZEN rules for performance.
DO NOT overwrite or delete a prior frozen baseline.
DO NOT auto-promote EXPERIMENTAL thresholds, weights, bootstrap cutoffs, rebalance rules, model rules, or router rules.

The frozen portfolio architecture is:

E16 Core Allocation
+
E18/E22 Execution Layer
+
E50-A Alpha Overlay
+
E45 Crisis Protection Core

Operational logic:

Normal market:
- Keep the core portfolio running.
- Allocate only part of capital to E50-A Alpha.

Alpha weakening:
- Reduce Alpha first.
- Do not automatically exit the core portfolio.

Risk transmission:
- Shut down or strongly reduce Alpha.
- Reduce core risk.

Crisis:
- Hand risk control to E45.

Current research stage:
**E50-A3-R1**

FIRST TASK:
Perform a READ-ONLY repository audit.

Locate and classify:
- E16
- E18
- E22
- E44
- E45
- E50-A0
- E50-A1
- E50-A2
- E50-A3
- E50-A3-R1
- Financial Router
- Telecom Router
- 0050 modules
- Cash/Short Bond modules
- Crisis modules
- datasets
- manifests
- hashes
- QC
- training code
- backtest engine
- execution engine
- latest experiment outputs

Classify each:
FOUND
INCOMPLETE
MISSING
SUSPICIOUS

Then audit:
1. dataset state
2. PIT correctness
3. universe construction
4. announcement timing
5. feature timing
6. label timing
7. corporate actions
8. Exact T+1 implementation
9. frozen portfolio architecture
10. leakage risks

Trace at least several sample trades:

Information(T)
-> Feature(T)
-> Signal(T)
-> Order
-> Next Trading Day Open
-> Fill
-> Position
-> PnL

At the end produce:

# E50-A3-R1 Full Handoff Audit

## Frozen Architecture Verification
## Confirmed Components
## Missing Components
## Suspicious Components
## Dataset Findings
## Exact T+1 Findings
## Leakage Findings
## Current R1 Checkpoint
## Smallest Safe Next Experiment

Do not optimize performance yet.

Long-term target:
- CAGR >= 20%
- MDD approximately 10–15%

But causal correctness, frozen baseline preservation, Exact T+1, OOS robustness, transaction-cost survival and reproducibility have priority over performance.
