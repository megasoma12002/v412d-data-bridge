# Stage-8 Summary — Alpha-Stress Controllers

Date: 2026-09-04  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049` (draft PR #19)  
Frozen stack unchanged. **E45 untouched. No gate promotion. No retune after held-out.**

## Goal of this stage

Stage-7 showed EW-crisis flags cover **0%** of the 13 shared C2/C4/C8 bad months.  
Stage-8 asked: can a **non-crisis / high-XS-vol** detector + mild/aggressive cash or value sleeve improve OOF stress PnL under dual gates, and survive one held-out?

## 8A — Failure signature (diagnosis)

Shared bad-month days vs other validation:

| signal | finding |
|---|---|
| `crisis_vote2` | **0.00** on bad months |
| `mkt_vol_60d` | elevated vs other val |
| trailing `val_ic` | elevated (value works) |
| market regime | mostly still RISK_ON |

Initial `ALPHA_STRESS_V1` (weak mom IC) was a weak discriminator.  
Operational detector for 8B: **non-crisis + high cross-sectional vol** (and/or high trailing value IC).

## 8B — OOF screen

Detectors (OOF quantiles only): `HIGH_VOL_NONCRISIS`, `VAL_WORKS_NONCRISIS`, `COMBO_VOL_VAL_NONCRISIS`.  
Controllers on frozen TECH2+C4: `CASH_090/085/070`, `SLEEVE_VALUE`, `SLEEVE_VALUE_CASH085`.

**Decision:** `OOF_NEW_ALPHA_STRESS_CONTROLLER_DUAL_GATE_WINNER`

| lock | value |
|---|---|
| S8B1 | `CASH_070` × `HIGH_VOL_NONCRISIS` with `vol_min = OOF p80 ≈ 0.4384` |
| OOF util | −0.026 (vs BASE −0.046) |
| OOF boot | 0.796 |
| OOF stress_ex | 0.000561 (vs BASE 0.000512) |
| OOF stress share | **12.4%** |

Seven dual-gate stress candidates; winner ranked by stress compound then utility.  
Value sleeves mostly failed bootstrap on OOF.

## 8B held-out — S8B1 one shot

**Decision: `MIXED_HELDOUT`** (same pattern as C2/C4/C8/F1/R6B1)

| Metric | S8B1 Val | C4 Val | S8B1 Sealed | C4 Sealed |
|---|---:|---:|---:|---:|
| CAGR | 18.0% | 21.7% | 38.7% | 47.7% |
| MDD | −26.3% | −31.9% | −15.0% | −21.0% |
| Bootstrap | **0.348** | 0.559 | 0.991 | 0.998 |
| Stress mean excess | **−0.00035** | −0.00022 | 0.00083 | 0.00109 |
| Stress flag share | **57.3%** | — | **70.2%** | — |

### What broke

1. **Absolute OOF p80 vol cut does not travel** — fires on ~12% of OOF days but **57–70%** of held-out days → chronic cash, CAGR↓, bootstrap collapses on validation.
2. **Stress PnL goal fails on validation** — S8B1 stress excess/compound **worse** than C4 full.
3. Sealed still looks fine (boot gate pass, MDD↓) → classic **MIXED_HELDOUT**, not a production lock.

No retune. S8B1 is a documented OOF lock that failed held-out transfer.

## Saturation map (Stages 1–8)

| Layer | Outcome |
|---|---|
| C2/C4/C8 portfolio | `MIXED_HELDOUT` |
| TECH2/PRICE8 / F1 atomic | no lasting held-out win |
| Horizon / blend / orth | no dual-gate winner |
| Static / mild cash (R6B1) | `MIXED_HELDOUT` |
| EW-crisis cash / sleeve (S7) | no crisis-profit dual-gate winner |
| Alpha-stress cash (S8B1) | OOF win → **`MIXED_HELDOUT`**; stress worse on val |

## Implication for user goals

| Goal | Status after Stage-8 |
|---|---|
| 高獲利 | TECH2+C4 remains the risk-on engine; cash overlays dilute CAGR |
| 低風險 | Cash can cut MDD, but destroys val bootstrap |
| 即時換手 | Still deferred — conflicts with turnover/boot tradeoff |
| 壞月／股災也賺 | EW-crisis *and* high-vol-noncrisis cash both fail to improve bad-window PnL on held-out |

**E50-A TECH2+C4 should be treated as a bull / risk-on sleeve with a documented failure mode**, not a single object that also earns in alpha-stress months.

## Stage-8C (next architecture — not started here)

Per prior plan, only after 8B fails:

1. Keep TECH2+C4 as **bull-sleeve** reference (no more cash-grid on this sleeve expecting bad-month alpha).
2. Open a **separate multi-sleeve / E45-class portfolio challenger** under a higher process bar (not in-place E45 edit).
3. Optional EXPERIMENTAL fast-execution track only after a stress sleeve exists as its own hypothesis.

Do **not**: retune S8B1 vol cut on held-out; promote gates; merge PR #19 as production.

## Artifacts

- `E50-A3-R1_STAGE8A_FAILURE_SIGNATURE.md`
- `E50-A3-R1_STAGE8B_ALPHA_STRESS_OOF.md`
- `E50-A3-R1_STAGE8B_S8B1_HELDOUT.md`
- `reports/stage8a_failure_signature.json`
- `reports/stage8b_alpha_stress_oof_summary.json`
- `reports/stage8b_s8b1_heldout_decision.json`
