# Stage-8 Stress-Sleeve Closeout (on main path)

Date: 2026-09-04  
Branch: `cursor/stage8-failure-stress-d049`  
Status: **STAGE-8 COMPLETE / SATURATED** — archived from diagnosis sandbox; not re-run.

**No live overlay. No E45 edit. No gate promotion. No sealed retune.**

## Why this PR (instead of re-running 8A→8C)

Debt board said “next = Stage-8 failure-signature / stress-sleeve.”  
That work **already finished** on `cursor/e50a3r1-turnover-diagnosis-d049` (closed #19) with held-out:

| Lock | OOF | Held-out |
|---|---|---|
| S8B1 high-vol cash | dual-gate win | **`MIXED_HELDOUT`** (val boot 0.35; over-fire 57%) |
| S8C1 multi-sleeve | dual-gate win | **`MIXED_HELDOUT`** (val boot 0.49; under-fire 4%) |

Re-running the same TECH2+C4 cash/sleeve grids would burn cycles without a new hypothesis.  
This PR **lands the evidence on main** and updates the operating next step.

## Stage-8 findings (short)

1. **8A:** 13 shared bad months ≠ EW crisis (coverage 0%). Failure ≈ RISK_ON + elevated XS vol / value IC works.
2. **8B:** Absolute OOF vol cut does not travel → chronic cash on held-out.
3. **8C:** Rolling multi-sleeve fixes over-fire but stress window too thin; stress PnL still loses on val.
4. **Implication:** TECH2+C4 = **bull / risk-on sleeve** with documented alpha-stress failure — not “高獲利+壞月也賺” as one object.

## Already beyond Stage-8 (pointer)

On the same diagnosis lineage (also archived here):

| Stage | Result |
|---|---|
| **9A S9A1** | Freeze-reb × rolling vol/val; **first stress transfer win vs C4** on val; still **`MIXED_HELDOUT`** (boot 0.623 &lt; 0.70) |
| **Option 2** | Accepted: **C4 research baseline** + **S9A1 paper/monitor**; E45 unchanged |
| Auto-iterate causal S9A1C | **STOPPED** at adversarial-lite |

## Decision labels

- `STAGE8_STRESS_SLEEVE_SATURATED`
- `DO_NOT_RERUN_TECH2_CASH_SLEEVE_GRIDS`
- `LIVE_OVERLAY_STILL_NO`

## What to do next (only productive moves)

1. **Operate Option-2 paper monitor** (runbook: `S9A1_PAPER_MONITOR_RUNBOOK.md`) — research feed, not live capital.  
2. **New return engine** for stress months (not TECH2 family remix) under a new EXPERIMENTAL version id — or stop A3-R1 controller grids (Stage-9A stop rule).  
3. Optional: explicit promote `E22_v2s_tw` default (separate PR; cutover-only).

## What not to do

- Retune S8B1 / S8C1 / S9A1 cuts after held-out  
- More cash / DEF/VAL/QUAL / freeze grids on TECH2  
- Promote 2.5% / 0.70 gates  
- Live-wire overlay  
- Invent E45 −13.16%

## Artifacts (this PR)

Under `repro/e50a3r1-turnover-diagnosis-20260903/`:

- `E50-A3-R1_STAGE8_SUMMARY.md` (+ 8A/8B/8C reports)
- `reports/stage8*_*.json`
- `E50-A3-R1_STAGE9A_SUMMARY.md`, Option-2 governance + S9A1 runbook
- Scripts: `scripts/e50a3r1_stage8*.py` (repro tooling)

Debt board: `research/STRATEGY_DEBT_BOARD.md` (updated).
