# 民股 MDD V6 — Decision Pack

Date: 2026-09-19 · `2026-09-19T15:07:15.651328+00:00`  
Status: **STOP** (`STAGE_A_SCORE_POS_GATES_FAIL`) · Soft-Frozen **KEEP** · live wire **false**  
Frozen offense: `SF4_P60-90_V0-15_F10_KD` · δ=`0.05` · sensor shadow `DD_rel` · sealed **unchanged**

## Verdict

**No MDD coexist** under V6 shadow relative-NAV continuous FinPriv damp.

| Book | c/sink | MDD↑ held | MDD↑ sealed | tip | mean_u | coexist |
|---|---|---:|---:|---|---:|---|
| `V6_C100_CASH` (best score) | 1.0/CASH | +1.75 | **−0.40** | N | 0.153 | N |
| `V6_C50_CASH` (best tip-clean score) | 0.5/CASH | +1.47 | **−0.59** | Y | 0.153 | N |
| `V6_C100_PUB` (best tip-clean sealed) | 1.0/PUB | +0.97 | **−0.24** | Y | 0.153 | N |
| `SF4_L4_08_REF` | REF | +0.82 | −0.20 | Y | — | N |
| `N2_0050_LOCAL_08_REF` | REF | +0.44 | **−0.04** | N | — | N |

**0/8** V6 books clear sealed MDD↑ ≥ 0. Path coupling lifts heldout; sealed still binding. Best tip-clean sealed (−0.24) improves on V5 (−0.27) but does **not** beat prior closest sealed (−0.04 tip-fail).

## Binding — research stack summary

| Ladder | Status |
|---|---|
| N1–N3 FinPriv self-path | **STOP** |
| V2 S1–S2 sensors | **STOP** |
| V3 M1 proportional scale | **STOP** |
| V4 sealed-episode → calendar | **STOP** |
| V5 DH FinPriv window | **STOP** |
| V6 shadow relative-NAV damp | **STOP** |

1. Soft-Frozen stays **3-sleeve 公股**.  
2. Do **not** Class-D / merge `#257` / soften sealed / retune δ / N1–V5.  
3. Re-open only: human **sealed-gate** · or **other** new charter (≠ N1–V6 retune).

## Refs

- Charter: `PRIV_MDD_SHADOW_RELNAV_V6_CHARTER.md`  
- Stage A: `PRIV_MDD_SHADOW_RELNAV_V6_STAGE_A.md`  

Label: `PRIV_MDD_SHADOW_RELNAV_V6_DECISION_2026-09-19__STOP_NO_SEALED_MDD_COEXIST`
