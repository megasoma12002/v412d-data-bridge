# MDD L2 Loss-Engine Charter

Date: 2026-09-05  
Status: **CHARTER FROZEN for screening** — RESEARCH_ONLY; no live-wire; no Soft-Frozen rewrite.  
Parent: L1 stopped (`STOP_L1_HELDOUT_MIXED`) — attribution `research/gaps/MDD_L1_SEALED_ATTRIBUTION.md`

## Why L1 failed (do not invent)

Locked `L1_FINCAP50_COMBO_50` cleared OOF + adv-lite, then:

| Window | MDD Δ | CAGR giveback | Outcome |
|---|---:|---:|---|
| Val 2019–2022 | **+10.0 pp** | **−0.65 pp** (L1 better) | PASS |
| Sealed 2023+ | **+7.7 pp** | **+8.9 pp** | **FAIL** (gate ≤3.0) |

Attribution anchors:

1. Sealed COMBO flag share **~38%** while CRISIS share only **~13.5%** — gross-cut over-fires in bull years.  
2. Sealed BASE mean daily ret on flag-on ≈ flag-off (**both positive**) → cutting equity on COMBO days truncates upside without avoiding losses.  
3. Giveback concentrated in **2024 (+10.4 pp)** and **2026 YTD (+33.3 pp)**; 2023 was fine.  
4. FIN_CAP_50 alone remains a **separate** promote path (#43); L2 must not silently restack L1’s COMBO×0.50.

## Object

Exact T+1 challengers that improve MDD **without** sealed CAGR giveback > gate.  
Measure on E16→E18→E22_v2s paper books. L1 cuts are **frozen-stopped** (no retune).

## L2 families (screen these only)

| ID | Mechanism | Design intent vs L1 failure |
|---|---|---|
| **L2-FINCAP-ONLY** | FIN_CAP_50 weights, **no** gross equity scale | Concentration without timing cut |
| **L2-DD-PATH** | Scale only while strategy/index is in active drawdown from peak (path-dependent) | Avoid bull-year COMBO false positives |
| **L2-SPIKE-SHORT** | Vol/DD spike with short half-life + fast restore | Limit flag dwell time |
| **L2-ASYM-SCALE** | Hard cut on stress; slower/partial restore only after clear | Asymmetric: save left tail, release upside |
| **L2-FINCAP+DD** | FIN_CAP_50 **plus** DD-PATH only (not COMBO) | Stack concentration with path cut, not L1 COMBO |

**Forbidden:** retuning `L1_FINCAP50_COMBO_50`; Stage-8 TECH2 remix; S1 residual cut retune; proxy-as-PASS; inventing E45 −13.16%.

## Frozen gates (EXPERIMENTAL paper books)

**OOF:** 2012-12-04 → 2018-12-31  
**Held-out:** validation 2019–2022 **and** sealed 2023→latest (one shot; no cut retune)

| Gate | Rule |
|---|---|
| Exact T+1 | `same_bar_fills == 0` |
| OOF MDD improve vs BASE | ≥ **3.0 pp** |
| OOF CAGR giveback vs BASE | ≤ **2.5 pp** |
| **Sealed-aware OOF proxy** | Within OOF, CAGR giveback on **bull-regime days** (E16 Bull) ≤ **1.5 pp** vs BASE (blocks L1-style upside truncation) |
| Flag dwell | Candidate mean flag share on OOF Bull days ≤ **20%** |
| Val held-out | MDD improve ≥1.0 pp **and** CAGR giveback ≤3.0 pp |
| Sealed held-out | MDD improve ≥1.0 pp **and** CAGR giveback ≤3.0 pp |
| Pass label | `PASS_HELDOUT_L2` only if **both** val and sealed clear |
| Fail | `STOP_L2_*` — no cut retune on that family |

Dual paper ledgers on any later promote: **BASE** + **L2**. Live stays BASE until explicit cutover PR.

## Adversarial-lite (before held-out)

- Placebo: scramble stress/DD flags; P(MDD improve ≥ locked) **&lt; 0.50**  
- Year-split: OOF MDD improve not from a single calendar year  
- **Bull-day check:** locked candidate’s OOF Bull-day CAGR giveback must remain ≤1.5 pp (same as gate)

## Decision labels

| Step | Pass | Fail |
|---|---|---|
| OOF | `OOF_L2_*_READY_FOR_ADV_LITE` | `STOP_L2_OOF_*` |
| Adv-lite | `ADV_LITE_L2_READY_FOR_HELDOUT` | `STOP_L2_ADV_*` |
| Held-out | `PASS_HELDOUT_L2` | `STOP_L2_HELDOUT_*` |

## Parallel track (not L2)

FIN_CAP_50 dual-paper promote proposal (#43) continues as **ops month-end monitor** — Soft-Frozen clip stays [0.50, 0.95] until a separate human cutover PR.

## Next implementation (separate PR)

1. Exact T+1 OOF harness for L2 families with sealed-aware / bull-day gates.  
2. Screen L2-FINCAP-ONLY and L2-DD-PATH first.  
3. Only then adv-lite → one held-out.

## Label

`MDD_L2_LOSS_ENGINE_CHARTER_FROZEN__L1_SEALED_ATTRIBUTION_READY`
