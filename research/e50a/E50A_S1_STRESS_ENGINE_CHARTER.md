# E50-A3-S1 — Stress Return Engine Charter (Track B)

Date: 2026-09-04  
Status: **CHARTER FROZEN FOR SCREENING** — EXPERIMENTAL. Not live. Not E45.

## Why a new engine

Stage-8/9 showed TECH2+C4 controllers (cash / VAL-DEF-QUAL switch / freeze) can win OOF dual-gate but transfer as **`MIXED_HELDOUT`**.  
S9A1 is the best *directional* stress transfer on the old stack and stays **Track A paper/monitor**.  
Track B needs a **new return engine** for alpha-stress months — not another TECH2 remix.

## Version id

`E50-A3-S1` (Stress engine, generation 1)

## Hypothesis (one sentence)

In non-EW-crisis / high cross-sectional stress states, a **defensive-quality residual book** (orthogonal to TECH2 momentum) can earn positive OOF stress excess vs REF_C4 without destroying dual gates, and transfer to held-out.

## Allowed candidate families (predeclared)

| ID | Idea | Notes |
|---|---|---|
| S1-QRES | Quality residual long (orth vs TECH2 mom) | Primary |
| S1-DEFRES | Defensive residual long (orth vs TECH2 mom) | Secondary |
| S1-VALRES | Value residual long (orth vs TECH2 mom) | Secondary; prior VAL sleeves failed boot — keep residual, not raw sleeve switch |

All use Exact T+1, PIT panel only, OOF 2011–2018 for selection.

## Forbidden

- TECH2 / PRICE8 / atomic F1 **score remix** as the stress engine  
- Re-using S8B1/S8C1/S9A1 detector **cut retunes** after any held-out peek  
- EW-crisis-only cash grids (Stage-7 saturated)  
- Absolute OOF vol percentile cuts that do not use rolling windows (S8B1 failure mode)  
- Live-wire / E45 in-place edit / gate promotion  

## Detector (predeclared class — cuts chosen on OOF only)

Rolling-window class only (same spirit as S9A1 travel):

- `not crisis_vote2`
- AND rolling-252d `mkt_vol_60d` ≥ OOF-chosen rolling percentile ∈ {0.70, 0.80}
- AND optional `val_ic_lag21` ≥ OOF-chosen ∈ {0.00, 0.03} (causal lag ≥ label horizon for live feed)

Controller while flag on: **switch to S1 stress book** (not freeze-of-TECH2, not cash-only).  
While flag off: stay in REF_C4 bull book (or flat stress book weight 0).

## Portfolio shell (EXPERIMENTAL, OOF-chosen within grid)

Reuse C4-like friction shell unless OOF dual-gate forces slower reb:

- `top_k` ∈ {20, 22, 30}  
- `rebalance_every` ∈ {42, 63}  
- `exit_multiple` ∈ {2.0, 2.25}  
- `industry_cap` = 5  
- `liquidity_floor` = 20e6  

No `rebalance_every=5` (TO known fail on R1).

## Adversarial / promotion gates (predeclared — dual-track board)

Mirror `research/e50a/DUAL_TRACK_OPERATING_BOARD.md`:

1. OOF dual-gate + stress excess ≥ C4  
2. Adversarial-lite not falsified  
3. **One** held-out; no retune  
4. Only `PASS_HELDOUT` replaces Track A as paper/monitor  

## Stop rules

- If no OOF dual-gate stress winner → `STOP_S1_OOF`  
- If adv-lite falsifies → `STOP_S1_ADV`  
- If held-out MIXED/FAIL → `STOP_S1_HELDOUT` — **keep Track A**  
- Do not open S1-QRES cut retune after held-out  

## Relation to E45

Separate track. Does not edit `e45_crisis_core.py`. Crisis handoff remains unapproved.

## Artifacts to produce (later screening PR)

- OOF grid summary JSON  
- Adv-lite ledger  
- One held-out decision JSON  
- Decision label on dual-track board  

## Label

`E50A_S1_STRESS_ENGINE_CHARTER_FROZEN`
