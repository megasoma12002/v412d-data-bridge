# Stage-8C Summary — Multi-Sleeve / E45-Class Challenger

Date: 2026-09-04  
Branch: `cursor/e50a3r1-turnover-diagnosis-d049` (draft PR #19)  
**Not an in-place E45 edit. No retune of prior locks. Gates remain EXPERIMENTAL.**

## Hypothesis

After S8B1 failed (absolute-vol cash over-fires), a **separate stress return engine** (DEF/VAL/QUAL) switched by **rolling-percentile** detectors can improve OOF stress PnL under dual gates and transfer to held-out.

## OOF result

**`OOF_NEW_MULTISLEEVE_DUAL_GATE_WINNER`** — 2 candidates, both on narrow `COMBO_VOL80_VAL05` (~8% OOF days).

| Lock | Spec |
|---|---|
| **S8C1** | `SLEEVE_VAL_CASH085` × `COMBO_VOL80_VAL05` |
| Detector | non-crisis ∧ rolling-252d vol ≥ p80 ∧ val_ic_lag21 ≥ 0.05 (hys 2/5) |
| OOF stress | excess +9.4e-5 vs BASE −9.4e-5; compound −4.6% vs BASE −7.6% |
| OOF util | −0.0505 (BASE −0.0456; within −0.005 slack) |
| OOF boot | 0.760 |

Most DEF/QUAL sleeves failed bootstrap. Broader detectors (share 25–39%) destroyed boot.

## Held-out — S8C1 one shot

**`MIXED_HELDOUT`**

| Metric | S8C1 Val | C4 Val | S8C1 Sealed | C4 Sealed |
|---|---:|---:|---:|---:|
| CAGR | 20.3% | 21.7% | 50.0% | 47.7% |
| MDD | −31.9% | −31.9% | −23.5% | −21.0% |
| Bootstrap | **0.493** | 0.559 | 0.998 | 0.998 |
| Stress flag share | **4.0%** | — | 12.5% | — |
| Stress mean excess | **−0.00053** | −0.00044 | 0.00250 | 0.00137 |

### Failure mode (vs S8B1)

| | S8B1 (absolute vol) | S8C1 (rolling combo) |
|---|---|---|
| Val flag share | **57%** (over-fire) | **4%** (under-fire) |
| Val stress vs C4 | worse | worse |
| Val boot | 0.35 | 0.49 |
| Pattern | `MIXED_HELDOUT` | `MIXED_HELDOUT` |

Rolling percentiles fixed over-firing but the OOF winner was a **tiny stress window**; it does not cover the 2021–22 bad-month mass, and when it fires it still loses stress excess vs C4.

## Saturation (Stages 1–8C)

Within this sandbox, the following are saturated for “高獲利 + 低風險 + 壞月也賺” as **one** object:

- Portfolio C2/C4/C8 tilts
- TECH2/PRICE8 / atomic F1
- Horizon / blend
- Static / crisis / alpha-stress **cash**
- Multi-sleeve DEF/VAL/QUAL switches on causal stress detectors

Repeated outcome: OOF dual-gate (near-)wins → **`MIXED_HELDOUT`**; stress PnL does not transfer.

## Implication

**TECH2+C4 remains the bull / risk-on reference sleeve** with a documented alpha-stress failure mode.  
Further cash/sleeve grids on the same score families are not the next productive move.

## Stage-9 direction (next)

Open a **named E45-C1 track** under the governance higher process bar (`SOFT_FROZEN_CRITICAL`), separate from A3-R1 turnover repair:

1. Preserve E45 readable; challenger is additive documentation + side-by-side
2. Require crisis/stress **drawdown-protection** evidence (MC/block-bootstrap of MDD), not only dual-gate CAGR
3. Stress alpha must be a **new return engine** (not TECH2 family remix) or an explicit hedge sleeve with its own held-out
4. Stop promoting 2.5%/0.70 gates inside this PR

Artifacts: `E50-A3-R1_STAGE8C_PLAN.md`, `E50-A3-R1_STAGE8C_MULTISLEEVE_OOF.md`, `E50-A3-R1_STAGE8C_S8C1_HELDOUT.md`, `reports/stage8c_*`.
