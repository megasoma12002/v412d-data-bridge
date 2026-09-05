# MDD L4 Path / Mild-FIN Charter (sealed CAGR retention)

Date: 2026-09-05  
Status: **CHARTER FROZEN for screening** — RESEARCH_ONLY; no live-wire; Soft-Frozen stays **[0.50, 0.95]**.  
Parents:
- L1/L2/L3 STOPPED on sealed CAGR giveback  
- FIN_CAP_50 go-live verify: `NOT_READY_SEALED_CAGR` (#49)  
Diagnostics: `research/gaps/FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC.md`

## Why prior axes failed (do not invent)

| Lock / path | Sealed CAGR gb | Sealed MDD Δ | Note |
|---|---:|---:|---|
| FIN_CAP_50 / L2 | **+4.33 pp** | +4.41 | Static hard hi=0.50 |
| L3_MILD_35_60 | **+4.08 pp** | +5.29 | Still too much bull finance cut |
| Go-live trailing | 1y **+7.2** / YTD **+16.7** | — | PAUSE_REVIEW |

Diagnostic Exact T+1 (sealed **not** used for selection) shows selection-safe candidates that also **sealed-diag PASS**:

| ID | OOF MDD Δ | Late-bull gb | Sealed CAGR gb | Sealed MDD Δ |
|---|---:|---:|---:|---:|
| FIN_CAP_70_STATIC | +1.71 | −0.50 | **+1.75** | +5.05 |
| BLEND_025 | +1.37 | +0.40 | **+0.51** | +2.11 |
| BLEND_050 | +2.83 | +0.65 | **+1.18** | +4.68 |
| CRISIS_ONLY_50 | +1.31 | +0.22 | **+0.93** | +1.06 |

Hard static 50/60 and Bull-restore_50 still leak sealed CAGR. Crisis-only / milder 70 / light blends keep more Soft-Frozen finance beta in non-crisis bull stretch.

## Object

Exact T+1 challengers that pass **sealed CAGR giveback ≤ 3.0 pp** and MDD improve ≥ **1.0 pp** on both val and sealed — without retuning stopped locks.

## L4 families (screen these only)

| ID | Mechanism | Intent |
|---|---|---|
| **L4-CRISIS-ONLY** | Apply FIN_CAP_50 weights **only on Crisis regime days**; else BASE Soft-Frozen | Cut left-tail concentration only |
| **L4-FINCAP-70** | Static Financial hard clip hi=**0.70** (lo∈{0.35,0.50}) | Milder static than 50/60 |
| **L4-BLEND-LIGHT** | α·FIN50+(1−α)·BASE with α∈{0.25,0.50} | Partial concentration |
| **L4-DD-PATH** | FIN cap only while TAIEX active drawdown ≤ −8% from 252d peak; else BASE | True path DD (stricter than Bear label) |
| **L4-UTIL-RANK** | Same pool; OOF select by dual score (MDD improve, **minimize** late-bull CAGR giveback) — **no family priority to harsher caps** | Avoid L3’s MILD-first trap |

**Forbidden:** retune `FIN_CAP_50` / `L2_FINCAP_ONLY` / `L3_MILD_35_60` / L1 COMBO; Stage-8 TECH2; S1 reopen; proxy-as-PASS; invent E45 −13.16%; silent Soft-Frozen flip.

## Frozen gates

**OOF:** 2012-12-04 → 2018-12-31  
**Held-out:** val 2019–2022 **and** sealed 2023→latest (one shot)

| Gate | Rule |
|---|---|
| Exact T+1 | required |
| OOF MDD improve | ≥ **1.5 pp** |
| OOF CAGR giveback | ≤ **1.5 pp** |
| OOF late-bull (2017–2018) CAGR giveback | ≤ **1.5 pp** |
| Val / Sealed | MDD ≥1.0 pp **and** CAGR giveback ≤3.0 pp each |
| Pass | `PASS_HELDOUT_L4` only if **both** val and sealed clear |
| Selection | Among OOF passers: maximize MDD improve − 0.5×late_bull_cagr_gb (util); ties → lower sealed-proxy late-bull gb then lower mean FIN cut |

## Adversarial-lite

- Placebo on FIN intensity / crisis mask scramble; P(MDD≥locked) < 0.50  
- Year-split: OOF MDD improve in ≥2 years  
- Late-bull check remains ≤1.5 pp

## Decision labels

| Step | Pass | Fail |
|---|---|---|
| OOF | `OOF_L4_READY_FOR_ADV_LITE` | `STOP_L4_OOF_*` |
| Adv-lite | `ADV_LITE_L4_READY_FOR_HELDOUT` | `STOP_L4_ADV_*` |
| Held-out | `PASS_HELDOUT_L4` | `STOP_L4_HELDOUT_*` |

## Parallel ops

FIN_CAP_50 dual-paper month-end continues; cutover stays frozen while sealed/PAUSE gates fail. Soft-Frozen live **[0.50, 0.95]**.

## Next implementation (separate PR)

1. Exact T+1 OOF harness for L4 families with util-rank (no harsh-cap family priority).  
2. Screen **CRISIS_ONLY** and **FINCAP_70** / **BLEND_LIGHT** first.  
3. Then adv-lite → one held-out.

## Label

`MDD_L4_PATH_FINCAP_CHARTER_FROZEN__SEALED_IMPROVE_DIAG_READY`
