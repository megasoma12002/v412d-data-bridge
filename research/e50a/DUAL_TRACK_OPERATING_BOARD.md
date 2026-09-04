# Dual-Track Operating Board — A Monitor + B Stress Engine

Date: 2026-09-04  
Branch: `cursor/dual-track-monitor-stress-d049`  
Governance: Option-2 accepted; Stage-8 saturated; **no live overlay**.

## Dual-track design

| Track | Role | Object | Live? |
|---|---|---|---|
| **A** | Paper / monitor baseline | **S9A1** (FREEZE_REB × COMBO_VOL70_VAL03) vs **REF_C4** | **No** |
| **B** | EXPERIMENTAL challenger | **E50-A3-S1** new stress return engine (charter) | **No** |

Adversarial selection picks the **paper/monitor successor**, not a live strategy.

## Predeclared winner rule (do not edit after B starts screening)

1. **OOF:** B must clear dual-gate (TO≤2.5% EXPERIMENTAL + boot≥0.70 EXPERIMENTAL) **and** stress-window mean excess ≥ REF_C4 (and ≥ Track A on same OOF stress days if A flags available).  
2. **Adversarial-lite (OOF):** placebo util beat rate &lt; 50% **and** not falsified on year-split vs C4 (same spirit as S9A1C axis stop).  
3. **One held-out:** val **and** sealed both pass dual-gate → `PASS_HELDOUT`.  
4. **Outcomes:**  
   - B `PASS_HELDOUT` → B replaces A as paper/monitor (still not live).  
   - B `MIXED` / `FAIL` / adv falsified → **keep A**, stop that B axis.  
   - Both MIXED → **no promote**; live stays core-only.

## Track A — operate

- Runbook: `repro/e50a3r1-turnover-diagnosis-20260903/S9A1_PAPER_MONITOR_RUNBOOK.md`  
- Harness: `scripts/e50a_dual_track_s9a1_monitor.py`  
- Outputs: `repro/e50a-dual-track/track_a_s9a1_monitor/`  
- Cadence: month-end / research refresh; pause if stress edge vs C4 negative **two** consecutive reviews  
- Red lines: no cut retune; no PASS claim; no E45 edit  

## Track B — charter first

- Charter: `research/e50a/E50A_S1_STRESS_ENGINE_CHARTER.md`  
- Frozen gates JSON: `research/e50a/E50A_S1_STRESS_ENGINE_GATES.json`  
- Screening starts **only after** charter merge; no TECH2 family remix  

## Explicit non-goals

- Live-wire overlay into `forward/e21`  
- Promote 2.5% / 0.70 to Frozen  
- Retune S9A1 / S1 cuts after held-out  
- Weighted A+B NAV as “official books”  

## Label

`DUAL_TRACK_A_MONITOR_B_S1_CHARTER_OPEN`
