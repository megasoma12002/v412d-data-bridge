# L4 MDD Path/FINCAP — Held-out


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

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
- Dual-paper observation opened: `research/gaps/L4_DD_PATH_PROMOTE_PROPOSAL.md`
  + month-end runbook `research/gaps/L4_DD_PATH_MONTH_END_RUNBOOK.md`.
- Soft-Frozen at writing was **[0.50, 0.95]** (live today **[0.60, 0.90]**) until human PR.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l4_heldout/reports/l4_heldout_summary.json`
