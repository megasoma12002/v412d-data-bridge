# Held-MDD band −14%～−13% · CAGR giveback → 0 — Paper Charter (R2)

Date: 2026-09-25  
Status: **PAPER CHARTER OPEN** · Stage A **DONE** (`BAND_ONLY`)  
Parent: `HELD_MDD17_TARGET_PAPER_CHARTER` (R1 verdict `MDD17_HIT_CAGR_OK`)  
Soft-Frozen tip: **KEEP** · live clip / FUSE / DH: **KEEP** (no live wire)

Label: `HELD_MDD17_R2_CAGR0_PAPER_CHARTER_2026-09-25__PAPER_OPEN__NO_LIVE_WIRE`

## Why R2

R1 found **PROXY_CIRCUIT** can hit |MDD|≤17% on current Stage-E data.  
Best CAGR among R1 winners: **`PROXY_x08_f50`** ≈ held **14.45% / −14.34%** vs LIVE **15.56% / −25.27%** → **giveback ≈ +1.11 pp**.

R1.5 densify of the same PROXY knobs (floor↑ / cooldown / hysteresis / soft scale) showed:

- Holding MDD in **≈−14%～−13%** still costs **≈+1.0～+1.3 pp** CAGR  
- Softer recipes that cut giveback toward **+0.8 pp** push MDD to **≈−16%** (out of band)

Ask: can a **new finite role** (not same-knob PROXY densify) keep held MDD in **[−14%, −13%]** while driving CAGR giveback **toward 0** (primary: ≤ **0.5 pp**; stretch: ≤ **0.3 pp**)?

## Target (held-out 2019+)

| Metric | Target |
|---|---|
| MDD band | `−0.14 ≤ max_drawdown ≤ −0.13` |
| CAGR giveback vs LIVE_STACK | primary ≤ **0.5 pp** · stretch ≤ **0.3 pp** · report if ≤ **1.0 pp** (beats R1 ref) |
| Tip hygiene (paper end YTD / 1y) | `mdd_improve_pp >= 0` |

Notation: band is on signed MDD (shallower than −14% and not shallower than −13%).

## Non-actions (hard)

- No Soft-Frozen tip rewrite / ledger revert to fake old −17%  
- No live clip / FUSE / DH / broker flip from this charter  
- No open search; no E45 stitch reopen  
- R1.5 PROXY densify alone is **exhausted** as the R2 mechanism (may remain **control** only)

## Stage A tracks (new roles)

Offense = paper `LIVE_STACK` twin · Stage-E DEFAULT books · current ledger.

| Track | Role (Exact T+1, causal) | Why it might save CAGR |
|---|---|---|
| `DUAL_CONFIRM` | Enter floor only if **0050 MDD63 ≤ −x AND book MDD63 ≤ −b** | Cut false PROXY triggers in calm |
| `FAST_REBOUND` | PROXY enter + **short max-dwell / rebound exit** (proxy recovers above −exit) | Miss fewer post-crisis rebounds |
| `SOFT_THEN_HARD` | Soft scale in shallow stress; hard floor only if proxy ≤ −(x+δ) | Avoid full cut on mild dips |
| `TIMEBOX` | PROXY floor with **max defense sessions** hard cap | Force handoff back to offense |
| Controls | `BASE_LIVE` · `REF_PROXY_x08_f50` · best R1.5 near-band | Anchor giveback ≈1.1 pp |

Finite grids freeze in `scripts/held_mdd17_r2_cagr0_stagea_screen.py` (no open search).

## Verdicts

| Verdict | Meaning |
|---|---|
| `BAND_CAGR_STRETCH` | In MDD band + giveback ≤ 0.3 pp + tip hygiene |
| `BAND_CAGR_PRIMARY` | In MDD band + giveback ≤ 0.5 pp + tip hygiene |
| `BAND_BEATS_R1_REF` | In MDD band + giveback ≤ 1.0 pp + tip hygiene (beats ~1.11) |
| `BAND_ONLY` | In band but giveback > 1.0 pp or tip fail |
| `NO_BAND` | No recipe in MDD band |

Even stretch/primary → **paper observe ballot only**; never live wire from Stage A.

## Explicit non-goal this stage

Improving offense alpha (clip / sleeve / FUSE retune) is **out of Stage A** (Soft-Frozen KEEP). May open Stage B only if Stage A `NO_BAND` / no giveback lift.

## Artifacts

- Charter: `research/ops/HELD_MDD17_R2_CAGR0_PAPER_CHARTER.md`  
- ZH: `research/ops/HELD_MDD17_R2_CAGR0_PAPER_CHARTER.zh-TW.md`  
- Screen: `scripts/held_mdd17_r2_cagr0_stagea_screen.py`  
- Report: `research/ops/HELD_MDD17_R2_CAGR0_STAGEA_SCREEN.md` · `repro/held-mdd17-r2-cagr0-stagea/`

## Stage A result (2026-09-25)

Verdict: **`BAND_ONLY`**.

- Strict band [−14%, −13%] hits: `STH_x08_d04_s70_h40` (gb **+1.29 pp**), `STH_x08_d06_s70_h35` (gb **+1.75 pp**) — do **not** beat R1 ref giveback.
- Near-band signal (just outside −14%): `FAST_x08_ex06_f50_d21` → MDD **−14.45%** · gb **+0.56 pp** (closest to primary 0.5).
- `DUAL_CONFIRM` lowers giveback (~0.5–0.9 pp) but MDD stays ~−19%～−25% (**no band**).

Stretch/primary **not** cleared. Next: Stage B only if human opens (e.g. widen band to include −14.5%, or new offense-side charter) — still no live wire.
