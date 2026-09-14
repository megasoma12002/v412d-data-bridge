# L3 MDD Sealed-CAGR — Held-out


> **HISTORICAL / SSOT:** Soft-Frozen FIN was **[0.50, 0.95]** when this note was written.
> **Live today (2026-09-13+):** FIN **[0.60, 0.90]** · **KD_OPT** · **TEL_EQUAL** · **FUSE_ADDITIVE** · **DH_dd06** · **500M**.
> See `research/ops/OPS_STATUS.md`. Do not treat `[0.50, 0.95]` below as current live.

Generated: `2026-09-05T02:26:45.730428+00:00`
Locked: `L3_MILD_35_60` (FIN [0.35, 0.60]; no retune)
Label: `STOP_L3_HELDOUT_MIXED`
Research decision: `STOP_L3_HELDOUT_MIXED_KEEP_BASE`
Status: **RESEARCH_ONLY** — no live-wire; Soft-Frozen at writing was [0.50, 0.95] (live today [0.60, 0.90]).

| Window | BASE CAGR | BASE MDD | L3 CAGR | L3 MDD | MDD Δpp | CAGR giveback pp | PASS |
|---|---:|---:|---:|---:|---:|---:|---|
| val 2019–2022 | 12.33% | -22.64% | 12.94% | -20.73% | +1.91 | -0.61 | Y |
| sealed 2023+ | 24.93% | -14.46% | 20.84% | -9.17% | +5.29 | +4.08 | N |

No cut retune. No live-wire.

Aftermath: keep BASE; L3 axis stops under this lock; new charter required to continue.

Artifacts:
- `/workspace/repro/mdd-loss-engine/l3_heldout/reports/l3_heldout_decision.json`
