# L4 MDD Path/FINCAP — Held-out

Generated: `2026-09-05T03:39:55.597752+00:00`
Status: **RESEARCH_ONLY** — no live-wire, Soft-Frozen unchanged.

## Decision: `PASS_HELDOUT_L4`

- Locked: **L4_DD_PATH_08_50** (TAIEX DD≤-8% → FIN[0.35,0.50])
- As-of: `2026-09-04`
- Gates: Exact T+1; MDD ≥**1.0pp**; CAGR giveback ≤**3.0pp** (each window)

| Window | BASE CAGR | L4 CAGR | CAGR gb pp | BASE MDD | L4 MDD | MDD Δpp | PASS |
|---|---:|---:|---:|---:|---:|---:|---|
| validation 2019-01-01→2022-12-31 | 12.33% | 11.13% | +1.20 | -22.64% | -21.01% | +1.63 | Y |
| sealed 2023-01-01→2026-09-04 | 24.93% | 22.27% | +2.66 | -14.46% | -12.99% | +1.47 | Y |

## Aftermath

- Held-out PASS — still **no auto live-wire**.
- Dual-paper observation only; Soft-Frozen stays **[0.50, 0.95]** until human PR.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l4_heldout/reports/l4_heldout_summary.json`
