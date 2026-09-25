# Held-MDD ≤ 17% magnitude — Paper Research Charter (R1)

Date: 2026-09-25  
Status: **PAPER CHARTER OPEN** · Stage R1 screen **DONE** (`MDD17_HIT_CAGR_OK`)  
Soft-Frozen tip: **KEEP** · live clip / FUSE / DH: **KEEP** (no live wire from this charter)  
Books: **current Stage-E DEFAULT** `E22_v3_recv_pay_effdelay` + current dividend ledger + `forward/e21/live_market.csv`

Label: `HELD_MDD17_TARGET_PAPER_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## Why

Sealed 2026-09-13 paper `MENU3_DH_FUSE` held MDD **−17.2%** is **stale** under current Stage-E data (~−24% paper).  
Retuning live `DH_dd06` knobs on current data does **not** recover magnitude ≤ 17%.  
Ask: on **現行資料**, does any **finite new** risk actuator hit held-out MDD magnitude ≤ **17%** (`max_drawdown >= -0.17`)?

Clarify notation: human target 「held MDD ≤ −17%」 here means **|MDD| ≤ 17%** (shallower-or-equal), i.e. `max_drawdown >= -0.17`.

## Non-actions (hard)

- No Soft-Frozen tip rewrite / history invent  
- No flip live clip / FUSE / DH / `API_WIRED`  
- No revert dividend ledger to “recover” the old −17% claim  
- No open-ended hyperparameter search  
- No E45 live stitch reopen  

## Stage R1 question

Offense book = paper `LIVE_STACK` twin (Soft-Frozen FIN[0.60,0.90] + KD_OPT + TEL_EQUAL), Stage-E books.  
Does any finite R1 actuator clear:

1. held-out 2019+ `max_drawdown >= -0.17`  
2. tip-window hygiene on paper end: YTD and trailing-1y MDD not worse than base (`mdd_improve_pp >= 0`)  
3. held-out CAGR giveback ≤ **3.0 pp** vs LIVE_STACK  

| Verdict | Meaning |
|---|---|
| `MDD17_HIT_CAGR_OK` | Hits |MDD|≤17% + tip hygiene + giveback≤3pp |
| `MDD17_HIT_CAGR_FAIL` | Hits |MDD|≤17% but giveback or tip fails |
| `NO_HIT` | No recipe hits |MDD|≤17% |

Even `MDD17_HIT_CAGR_OK` → **paper observe ballot only**; never live wire from R1 alone.

## Finite R1 tracks (new role — not DH_dd06 densify)

| Track | Mechanism (Exact T+1, causal) | Grid |
|---|---|---|
| `HARD_FLOOR` | Book peak DD ≤ −trigger → exposure=`floor` until recover | trigger {8,10,12,15}% × floor {0,0.25,0.50} × recover 97% |
| `PROXY_CIRCUIT` | 0050 MDD63 ≤ −X → exposure=`floor` | X {8,10,12,15}% × floor {0,0.25,0.50} |
| `STEP_SCALE` | `exposure = max(floor, 1 + dd_peak/scale)` | scale {0.20,0.25,0.30} × floor {0,0.25} |
| Controls | `BASE_LIVE` · `CTRL_DH_dd06` | expected miss on |MDD|≤17% |

## Artifacts

- Charter: `research/ops/HELD_MDD17_TARGET_PAPER_CHARTER.md`  
- ZH: `research/ops/HELD_MDD17_TARGET_PAPER_CHARTER.zh-TW.md`  
- Screen: `scripts/held_mdd17_target_r1_screen.py`  
- Report: `research/ops/HELD_MDD17_TARGET_R1_SCREEN.md` · `repro/held-mdd17-target-r1/`

## Reading prior art

- Stale −17%: `DH_OBSERVE_COMBO_NAV_TRIAL.md` (2026-09-13; then DEFAULT=`E22_v2s_tw`)  
- Live DH: `E45_DEFEND_HANDOFF_PAPER_CHARTER.md` / `live_dh_fuse_cutover.py`  
- Dual clock: tip Stage-E vs FUSE offense preserved cash-on-ex — this charter uses **Stage-E** for honesty vs tip books

## Stage R1 result (2026-09-25)

Verdict: **`MDD17_HIT_CAGR_OK`**.

Winners (paper only): `PROXY_x08_f50` · `PROXY_x10_f25` · `PROXY_x10_f50` · `PROXY_x12_f25`.

Best CAGR among winners: `PROXY_x08_f50` (held ~14.45% / MDD ~−14.34%, giveback ~1.11pp).

`HARD_FLOOR` and live `DH_dd06` control: **NO_HIT**. `STEP_SCALE` hits |MDD|≤17% but fails giveback cap.

Next: paper-observe ballot only if human opens; **no** live wire from R1.
