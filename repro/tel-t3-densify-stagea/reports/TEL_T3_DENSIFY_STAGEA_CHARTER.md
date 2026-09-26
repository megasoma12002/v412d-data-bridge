# TEL within-sleeve — T3 densify / T2 half / near-flat (Stage A)

Date: 2026-09-26  
Status: **Stage A `TEL_NEARFLAT_READY`** · Soft-Frozen live **KEEP** · live wire **false**  
Human: 三路徑都研究 — (1) T3 densify (2) T2 sealed-MDD 半開 (3) near-flat floor +0.15

Parent: `TEL_WITHIN_SLEEVE_STAGEA` verdict **`TEL_WITHIN_SOFT`** · best `T3_COOL_INV_VOL20` held CAGR↑ +0.16pp  
Priors KEEP: Soft-Frozen · `KD_OPT` · `TEL_EQUAL` · no reopen TEL KD/async · no `00631L` in paper twin

Label: `TEL_T3_DENSIFY_STAGEA_CHARTER_2026-09-26__OPEN`

**Passing ≠ live · Path 3 near-flat is paper-policy readiness only (needs human ACCEPT).**

---

## Question

Can a **finite** densify of parent softs clear held CAGR≥**+0.20pp** with MDD/tip gates; alternatively clear near-flat ≥**+0.15pp**; or can T2 half-open repair sealed MDD while keeping CAGR lift?

## Tracks

### P1 — T3 densify (`INV_VOL20` base)

Finite grid on `TEL_RS_SOFT_TILT` + cool-gated scores:

| Axis | Values |
|---|---|
| amp | 0.50 · 1.00 · 1.50 |
| cool_lt | 1.00 (any defend) · 0.50 (deeper only) |
| blend λ DIST60 | 0.00 · 0.50 |

Id: `D3_A{amp}_C{cool}_B{blend}` · parent replay = `D3_A100_C100_B00`.

### P2 — T2 half-open (`INV_VOL20`)

| id | Mechanism |
|---|---|
| `T2_ALWAYS_A25/50/75/100` | Always-on weak→full amp (100 = parent T2) |
| `T2_PROP_A50/100` | Score × (1−cool) × amp (proportional defense) |

### P3 — Near-flat floor +0.15 (policy rescore)

Same books; secondary gate held CAGR↑ ≥ **+0.15pp** (offense near-flat precedent).  
Does **not** change live SSOT. READY ≠ ACCEPT ≠ live wire.

## Gates

| Gate | Rule |
|---|---|
| tip_clean / tip_mdd_ok | YTD+1y PASS · MDD↑ ≥ −0.5pp |
| held_mdd / sealed_mdd | ≥ −0.25pp / ≥ 0 |
| cagr_floor_hit | held CAGR↑ ≥ +0.20pp |
| cagr_floor_nearflat | held CAGR↑ ≥ +0.15pp |

| Verdict | Meaning |
|---|---|
| `TEL_DENSIFY_HIT` | ≥1 book clears HIT (+0.20) |
| `TEL_NEARFLAT_READY` | no HIT · ≥1 clears near-flat (+0.15) + MDD/tip |
| `TEL_DENSIFY_SOFT` | MDD/tip OK · CAGR short of +0.15 |
| `MDD_BLOCK` | tip OK · MDD fail |
| `NO_LIFT` | no tip-clean offense |

## Out of scope

- Soft-Frozen clip / tip rewrite / broker / live wire  
- Reopen TEL KD / async STOP  
- Retune COOL / FUSE / SELL_a75 / `00631L`  

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/tel_t3_densify_stagea.py
```

Artifacts: `research/ops/TEL_T3_DENSIFY_*` · `repro/tel-t3-densify-stagea/`
