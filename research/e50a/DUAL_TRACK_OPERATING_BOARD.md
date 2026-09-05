# Dual-Track Operating Board — A Monitor + B Stress Engine

Date: 2026-09-05  
Governance: Option-2 accepted; Stage-8 saturated; **no live overlay**.

## Dual-track design

| Track | Role | Object | Live? |
|---|---|---|---|
| **A** | Paper / monitor baseline | **S9A1** (FREEZE_REB × COMBO_VOL70_VAL03) vs **REF_C4** | **No** |
| **B** | EXPERIMENTAL challenger | **E50-A3-S1** residual stress engine | **No** — **axis stopped** |

Adversarial selection picks the **paper/monitor successor**, not a live strategy.

## Predeclared winner rule (frozen — do not edit)

1. **OOF:** B must clear dual-gate (TO≤2.5% EXPERIMENTAL + boot≥0.70 EXPERIMENTAL) **and** stress-window mean excess ≥ REF_C4.  
2. **Adversarial-lite (OOF):** placebo util beat rate &lt; 50% **and** not falsified on year-split vs C4.  
3. **One held-out:** val **and** sealed both pass dual-gate **and** stress ≥ C4 → `PASS_HELDOUT`.  
4. **Outcomes:**  
   - B `PASS_HELDOUT` → B replaces A as paper/monitor (still not live).  
   - B `MIXED` / `FAIL` / adv falsified → **keep A**, stop that B axis.  
   - Both MIXED → **no promote**; live stays core-only.

## Track A — operate (KEEP)

- Runbook: `repro/e50a3r1-turnover-diagnosis-20260903/S9A1_PAPER_MONITOR_RUNBOOK.md`  
- Harness: `scripts/e50a_dual_track_s9a1_monitor.py`  
- Outputs: `repro/e50a-dual-track/track_a_s9a1_monitor/`  
- Cadence: month-end / research refresh; pause if stress edge vs C4 negative **two** consecutive reviews  
- Red lines: no cut retune; no PASS claim; no E45 edit  

## Track B — closed this axis

| Step | Decision | Artifact |
|---|---|---|
| OOF | `OOF_S1_DUAL_GATE_STRESS_WINNER_READY_FOR_ADV_LITE` — **S1-QRES / COMBO_VOL80_VAL00** | `E50A_S1_OOF_SCREEN.md` |
| Adv-lite | `ADV_LITE_PASS_READY_FOR_HELDOUT` (placebo util P≈0.25) | `E50A_S1_ADV_LITE.md` |
| Held-out | **`FAIL_HELDOUT` → `STOP_S1_HELDOUT_KEEP_TRACK_A`** | `E50A_S1_HELDOUT.md` |

Harnesses: `scripts/e50a_s1_stress_engine_oof.py`, `e50a_s1_adv_lite.py`, `e50a_s1_heldout.py`.  
No TECH2 family remix; no S1 cut retune after held-out.

## Explicit non-goals

- Live-wire overlay into `forward/e21`  
- Promote 2.5% / 0.70 to Frozen  
- Retune S9A1 / S1 cuts after held-out  
- Weighted A+B NAV as “official books”  
- Re-open S1 residual detector grid  

## Label

**`DUAL_TRACK_A_KEEP_B_S1_HELDOUT_STOP`**

Track A remains the paper/monitor. Track B S1 residual axis is closed. Next alpha work needs a **new charter** (e.g. MDD loss engine) or core-path research (e.g. FIN_CAP_50 promote proposal) — not another S1 cut pass.
