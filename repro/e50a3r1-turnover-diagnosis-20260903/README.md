# E50-A3-R1 Turnover / Dual-Gate Research Sandbox

## Current governance status (2026-09-04)

**Option 2 accepted:** paper/monitor **S9A1**; research baseline **C4**; official E16/E18/E22/E45 unchanged.

- Decision: `GOVERNANCE_DECISION_OPTION2_S9A1_PAPER_MONITOR.md`
- Runbook: `S9A1_PAPER_MONITOR_RUNBOOK.md`
- Machine record: `reports/governance_decision_option2.json`
- PR #19 stays **draft** — not a production promotion

### Stage-13 adversarial review (same day)

10-round red-team: **Option-2 kept with caveats** (worst round `WOUNDED`, not falsified).

- Summary: `E50-A3-R1_STAGE13_ADVERSARIAL_10ROUNDS.md`
- Caveats: `GOVERNANCE_OPTION2_ADVERSARIAL_CAVEATS.md`
- JSON: `reports/stage13_adversarial_10rounds_summary.json`
- Live monitor must use **causal** value-IC (`shift >= 21`); detector ≠ E45 crash overlay; still MIXED

---

# Earlier notes (Stage-2 era)

Draft only. **No retune of C2/C4/C8. No promotion. No E45. PR #19 stays draft.**

## 1. References retained
- **C2** / **C4** / **C8** — only val-turnover-pass cluster; C4 had best val bootstrap (~0.56)

## 2. Validation excess diagnosis (no retune)

Common weak years for **all three** references vs PIT proxy:
- **2021** and especially **2022** (negative excess; 2022 also higher turnover / lower hit rate)

Other notes:
- Crowding is moderate (top10 name gross ~19%; top industry ~18%) — not an extreme single-name blowup story
- For C4/C8, mean excess in deep drawdown (≤-10%) is worse than in mild DD — excess failure is partly regime/DD-linked
- Cost alone does not explain bootstrap failure (C4/C8 already lower turnover than many fails)

Artifact: `E50-A3-R1_STAGE2_VAL_EXCESS_DIAGNOSIS.md`

## 3. Alpha/model OOF screen (C4 portfolio wrapper fixed)

Axes: `TECH2|PRICE8` × `GLOBAL|BREADTH_REGIME` × λ∈{0.1,1,10,100}

**Decision: `OOF_NO_NEW_MODEL_DUAL_GATE_WINNER`**

| Finding | Detail |
|---|---|
| Dual-gate survivors | Only **TECH2 + BREADTH_REGIME** (λ almost inert) |
| GLOBAL | IC≈0.06, bootstrap≈0.13–0.15 — collapse |
| PRICE8 + BREADTH | IC≈0.112 (close to TECH2) but OOF bootstrap **≈0.51–0.53 FAIL** |
| λ-only TECH2/BREADTH twins | Not treated as a new model hypothesis |

Artifact: `E50-A3-R1_STAGE2_MODEL_OOF.md`

## 4. Stage-2 implication / next stage

Portfolio rules **and** the existing TECH2/PRICE8 × regime × λ grid are both saturated under experimental gates.

Next research should be one of:
1. **New feature families** beyond TECH2/PRICE8 (still OOF-selected), or
2. **New regime definition** (not just GLOBAL vs current BREADTH cut), or
3. Deeper **2021–2022 excess failure autopsy** without retuning locks

Do not promote 2.5% / 0.70. Do not merge PR #19 yet.
