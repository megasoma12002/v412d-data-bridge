# MDD L3 Sealed-CAGR Charter

Date: 2026-09-05  
Status: **CHARTER FROZEN for screening** — RESEARCH_ONLY; no live-wire; no Soft-Frozen rewrite.  
Parents:
- L1 stopped (`STOP_L1_HELDOUT_MIXED`) — COMBO timing over-fire  
- L2 stopped (`STOP_L2_HELDOUT_MIXED_KEEP_BASE`) — static FIN_CAP_50 concentration  

Attribution: `research/gaps/MDD_L2_SEALED_CAGR_ATTRIBUTION.md`

## Why L2 failed (do not invent)

Locked `L2_FINCAP_ONLY` cleared OOF + adv-lite, then:

| Window | MDD Δ | CAGR giveback | Outcome |
|---|---:|---:|---|
| Val 2019–2022 | **+3.06 pp** | **−0.75 pp** (L2 better) | PASS |
| Sealed 2023+ | **+4.41 pp** | **+4.33 pp** | **FAIL** (gate ≤3.0) |

Anchors (Exact T+1 NAV):

1. Mechanism is **concentration**, not timing: no COMBO / no gross scale; Financial hard clip `[0.35, 0.50]`.  
2. Sealed mean Financial weight **78.9% → 50.0%** (residual → Telecom / 0050).  
3. Giveback by year: 2023 **−3.86** (L2 better); 2024 **+4.86**; 2025 **+5.18**; 2026 **+16.73**.  
4. Soft-Frozen live clip stays **[0.50, 0.95]**; FIN_CAP_50 dual-paper month-end continues as ops only.

L1 vs L2 failure modes are **different** — L3 must not restack L1 COMBO×0.50 or reopen L2_FINCAP_ONLY as a live cut.

## Object

Exact T+1 challengers that keep **sealed CAGR giveback ≤ 3.0 pp** while still improving MDD ≥ **1.0 pp** on both val and sealed.  
Measure on E16→E18→E22_v2s paper books. L1/L2 locks remain frozen-stopped.

## L3 families (screen these only)

| ID | Mechanism | Design intent vs L2 failure |
|---|---|---|
| **L3-FINCAP-MILD** | Financial hard hi ∈ {0.60, 0.70, 0.80}; lo ∈ {0.35, 0.50} | Milder concentration than FIN50 |
| **L3-FINCAP-BLEND** | Day-weight blend `α·FIN50 + (1−α)·BASE`, α ∈ {0.25, 0.50, 0.75} | Partial clip; keep some Soft-Frozen finance beta |
| **L3-FINCAP-BULL-RESTORE** | Clip only outside Bull; in Bull restore toward BASE Soft-Frozen finance | Cut concentration drag in sealed bull years |
| **L3-FINCAP-DD-ONLY** | Apply FIN hi-cap only while TAIEX (or book) in active DD from peak; else BASE | Path-conditional concentration |
| **L3-UTIL-RANK** | Same candidate pool; OOF **select** by dual score (MDD improve, CAGR giveback) — not MDD-only | Avoid locking a sealed-fragile winner |

**Forbidden:** retuning `L1_FINCAP50_COMBO_50`; reopening `L2_FINCAP_ONLY` as locked live cut; Stage-8 TECH2 remix; S1 residual cut retune; proxy-as-PASS; inventing E45 −13.16%; silent Soft-Frozen flip.

## Frozen gates (EXPERIMENTAL paper books)

**OOF:** 2012-12-04 → 2018-12-31  
**Held-out:** validation 2019–2022 **and** sealed 2023→latest (one shot; no cut retune)

| Gate | Rule |
|---|---|
| Exact T+1 | `same_bar_fills == 0` |
| OOF MDD improve vs BASE | ≥ **2.0 pp** (slightly softer than L2’s 3.0 — sealed CAGR is primary) |
| OOF CAGR giveback vs BASE | ≤ **1.5 pp** (**tighter** than L2’s 2.5) |
| OOF late-bull proxy | Within OOF calendar years **2017–2018**, CAGR giveback ≤ **1.5 pp** |
| Val held-out | MDD improve ≥1.0 pp **and** CAGR giveback ≤3.0 pp |
| Sealed held-out | MDD improve ≥1.0 pp **and** CAGR giveback ≤3.0 pp |
| Pass label | `PASS_HELDOUT_L3` only if **both** val and sealed clear |
| Fail | `STOP_L3_*` — no cut retune on that family |

Dual paper ledgers on any later promote: **BASE** + **L3**. Live stays BASE until explicit cutover PR.

## Adversarial-lite (before held-out)

- Placebo: scramble / nullify FIN-cap intensity; P(MDD improve ≥ locked) **&lt; 0.50**  
- Year-split: OOF MDD improve not from a single calendar year  
- Late-bull check: locked candidate’s 2017–2018 CAGR giveback remains ≤1.5 pp

## Decision labels

| Step | Pass | Fail |
|---|---|---|
| OOF | `OOF_L3_*_READY_FOR_ADV_LITE` | `STOP_L3_OOF_*` |
| Adv-lite | `ADV_LITE_L3_READY_FOR_HELDOUT` | `STOP_L3_ADV_*` |
| Held-out | `PASS_HELDOUT_L3` | `STOP_L3_HELDOUT_*` |

## Parallel track (not L3)

FIN_CAP_50 dual-paper month-end monitor (#44 lineage) continues — Soft-Frozen clip stays [0.50, 0.95] until a separate human cutover PR.

## Next implementation (separate PR)

1. Exact T+1 OOF harness for L3 families with tightened CAGR + late-bull gates.  
2. Screen L3-FINCAP-MILD and L3-FINCAP-BLEND first.  
3. Only then adv-lite → one held-out.

## Label

`MDD_L3_SEALED_CAGR_CHARTER_FROZEN__L2_ATTRIBUTION_READY`
