# MDD Loss-Engine Charter (L1)

Date: 2026-09-05  
Status: **CHARTER FROZEN for screening** — RESEARCH_ONLY; no live-wire; no Soft-Frozen rewrite.  
Diagnosis: `research/gaps/MDD_LOSS_ENGINE_DIAGNOSIS.md`

## Why this exists

| Closed / insufficient path | Evidence |
|---|---|
| Stage-8 TECH2 stress remix | Saturated (`STAGE8_STRESS_SLEEVE_CLOSEOUT`) |
| Track B S1 residual stress | Adv-lite PASS → held-out **FAIL** (`STOP_S1_HELDOUT_KEEP_TRACK_A`, PR #40) |
| FIN_CAP_50 alone | Held-out PASS but MDD still **~−19.6%** (PR #39) |
| Formal E22_v2s core | **13.78% CAGR / −22.64% MDD** — ~8 pp too deep vs ≤15% |

Return engines and loss engines are **separate**. This charter is only the **loss engine**.

## Diagnosis anchors (do not invent)

1. Top episode (2020-01-20 → 2020-03-19): **−22.6%**, mean finance **84.7%**, Crisis-regime share only **13.9%** → E16 Crisis label **misses** much of the worst path.  
2. Formal recompute `e45_equity_scale` mean/min in episodes = **1.000** → existing E45 scaler is **inert** on these books (not delivering loss control).  
3. Crisis days mean daily ret **negative**; Crisis & fin≥80% rare but worse; Crisis & fin≤60% less bad (descriptive only).  
4. Return-path **proxies** (not Exact T+1) suggest crisis equity scales can move MDD toward −15% with limited CAGR giveback — **hypothesis only** until Exact rebuild.

## Object

Build Exact T+1 challengers that **cut gross exposure and/or finance concentration under stress**, measured on the **E16→E18→E22_v2s** core path (paper ledgers), not TECH2 overlay remix.

## L1 families (screen these only)

| ID | Mechanism | Notes |
|---|---|---|
| **L1-CRISIS-EQ** | On stress flag, scale equity weight (cash up) | Rebuild E45-like scaler that is currently inert |
| **L1-STRESS-DET** | Stress flag ≠ E16 Crisis alone (vol / breadth / drawdown path) | Needed because COVID episode is mostly non-Crisis labeled |
| **L1-FINCAP-STACK** | FIN_CAP_50 **plus** L1 exposure cut | Cap alone insufficient for ≤15% |
| **L1-GROSS-FLOOR** | Hard max equity weight under flag | Simple alternative to continuous scale |

Do **not** screen: Stage-8 TECH2 controllers, S1 residual cut retunes, overlay weight grids, inventing E45 −13.16%.

## Frozen gates (EXPERIMENTAL paper books)

**OOF window:** 2012-12-04 → 2018-12-31 (aligned to formal NAV start).  
**Held-out:** validation 2019–2022 + sealed 2023→latest (one shot; no cut retune).

| Gate | Rule |
|---|---|
| Exact T+1 | `same_bar_fills == 0` |
| MDD improve vs BASE_E22_v2s | OOF MDD improve **≥ 3.0 pp** |
| CAGR giveback vs BASE | OOF giveback **≤ 2.5 pp** |
| Stress coverage | Flag must be on ≥40% of days inside the formal top-1 DD episode (2020 path) when evaluated in-sample **description only**; promotion still needs held-out |
| Held-out | Val **and** sealed each improve MDD ≥1.0 pp vs BASE with CAGR giveback ≤3.0 pp |
| Pass label | `PASS_HELDOUT_L1` only if both windows clear |
| Fail | `STOP_L1_*` — no cut retune on that family |

Dual paper ledgers required on any promote: **BASE** + **L1**. Default live stays BASE until explicit cutover PR.

## Adversarial-lite (before held-out)

- Placebo: scramble stress flags; P(MDD improve ≥ locked challenger) must be **&lt; 0.50**.  
- Year-split: not entirely driven by a single OOF year.

## Non-goals

- Live-wire into `forward/e21` from this charter  
- Silent E16 prior / clip change  
- Claiming target CAGR≥20% from loss engine alone  
- Using proxy return-path scales as PASS evidence  

## Decision labels

| Step | Pass | Fail |
|---|---|---|
| OOF | `OOF_L1_*_READY_FOR_ADV_LITE` | `STOP_L1_OOF_*` |
| Adv-lite | `ADV_LITE_L1_READY_FOR_HELDOUT` | `STOP_L1_ADV_*` |
| Held-out | `PASS_HELDOUT_L1` | `STOP_L1_HELDOUT_*` |

## Screen outcome (2026-09-05)

| Step | Result |
|---|---|
| OOF | **PASS** — locked `L1_FINCAP50_COMBO_50` (9 passers; best MDD +8.3pp / CAGR giveback 1.4pp) |
| Adv-lite | **PASS** — placebo P(MDD≥locked)=**0.0**; year-split OK |
| Held-out | **`STOP_L1_HELDOUT_MIXED`** — val PASS (MDD +10.0pp, CAGR better); sealed FAIL (MDD +7.7pp but CAGR giveback **8.9pp** > 3.0pp) |

**Keep BASE / Track A.** No L1 cut retune. No live-wire.  
Artifacts: `research/gaps/MDD_L1_OOF.md`, `MDD_L1_ADV_LITE.md`, `MDD_L1_HELDOUT.md`.

## Label

`MDD_LOSS_ENGINE_L1_HELDOUT_MIXED_STOP__KEEP_BASE`
