# Governance Decision — Option 2 (S9A1 Paper / Monitor)

Date: 2026-09-04  
Decision maker: user (explicit “方案2”)  
Branch / PR: `cursor/e50a3r1-turnover-diagnosis-d049` / draft [#19](https://github.com/megasoma12002/v412d-data-bridge/pull/19)

## Decision

**Adopt Option 2:**

| Role | Object | Status |
|---|---|---|
| Research / bull reference | **C4** = TECH2 + C4 portfolio rules | EXPERIMENTAL reference sleeve |
| Paper / monitor overlay | **S9A1** = FREEZE_REB × `COMBO_VOL70_VAL03` | **MIXED** — monitor only |
| Official crisis core | **E45** | `SOFT_FROZEN_CRITICAL` — **unchanged** |
| Official stack | E16 / E18 / E22 | `SOFT_FROZEN` — **unchanged** |

## Explicit non-decisions

- **Do not** promote S9A1 to frozen / production  
- **Do not** replace or edit E45 in place  
- **Do not** promote EXPERIMENTAL gates (2.5% turnover / 0.70 bootstrap)  
- **Do not** merge PR #19 as a production strategy claim  
- **Do not** retune S9A1 detector cuts after held-out  

## Why this option

- Stage-11 MC: on validation, S9A1 beats C4 on stress mean/compound with P≈0.94–0.95  
- Held-out remains `MIXED_HELDOUT` (val boot≈0.62 &lt; 0.70)  
- Stages 10–12 open options did not produce a better transferable challenger  

## Operating mode

1. Keep C4 as the baseline NAV for research comparisons  
2. Run S9A1 in parallel as a **paper monitor** account  
3. Review KPIs in `S9A1_PAPER_MONITOR_RUNBOOK.md` on a fixed cadence  
4. Escalate only if monitor KPIs systematically beat C4 *and* a separate promotion review is opened  

## Label

`GOVERNANCE_OPTION2_S9A1_PAPER_MONITOR_ACCEPTED`
