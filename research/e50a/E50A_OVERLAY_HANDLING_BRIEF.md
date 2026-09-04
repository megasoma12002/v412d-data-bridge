# E50-A Overlay Integration — Handling Brief (#5)

Date: 2026-09-04  
Companion: `research/gaps/E50A_AND_EXEC_GAP_HANDLING.md`

## One-line status

**Live: not connected (correct). Research: A3-R1 = `RESEARCH_ONLY`. Do not wire into E21.**

## Evidence

| Check | Value |
|---|---|
| QC decision | `RESEARCH_ONLY` |
| Turnover feasible candidates | **0** |
| Val CAGR / proxy | **14.95% / 20.97%** |
| Val MDD | **−33.5%** |
| Combined E16+overlay engine on main | **Absent** |
| Overlay→E45 handoff | **Not approved** |

Source: `repro/e50a3r1-audit-20260903/outputs/a3r1/qc_status.json`, `E50_HANDOFF_VERIFICATION.md`.

## How to handle

1. **Honesty:** Published live strategy = E16(+E18/E22 books). Do not imply ≥20% from core.
2. **No live-wire** until a successor clears gates + promotion path.
3. **Research order:** turnover/held-out diagnosis → failure signature → paper stitch with **predeclared** overlay weight → only then promotion review.
4. **E45:** separate critical challenger; do not invent handoff cuts; −13.16% MDD remains NOT_VERIFIED.

## Anti-patterns

- “Temporary” overlay allocation in `forward/e21`
- Tuning on sealed 2023+ to clear gates
- Mixing overlay PnL into core NAV without separate ledger
