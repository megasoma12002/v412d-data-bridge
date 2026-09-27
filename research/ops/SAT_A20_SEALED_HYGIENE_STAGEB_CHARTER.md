# SAT_A20_H5 sealed-hygiene Stage B — STOP overlay only (paper)

Date: 2026-09-27  
Status: **Stage B OPEN** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · L1=0.05 **KEEP** · no live wire  
Parent: next-mech Stage A **`MECH_HIT`** champion `SAT_A20_H5`  
Human: `SAT_A20_H5 還有辦法優化嗎`

Label: `SAT_A20_SEALED_HYGIENE_STAGEB_CHARTER_2026-09-27__OPEN__NO_LIVE_WIRE`

## Context

Stage A densified CONF α→0.20 H=5 vs live `CONF_RET3_A10_H5`:

| book | held CAGR↑ | held MDD↑ | sealed MDD↑ |
|---|---:|---:|---:|
| `SAT_A20_H5` | **+0.33** | **−0.31** | **−0.10** (hygiene soft) |
| `SAT_A15_H5` | +0.10 | −0.10 | −0.05 |
| prior short-assist `CONF_RET3_A25_*` | CAGR↑ large | held MDD fail | — |

Binding soft for promotion is **sealed MDD**, not CAGR.  
α／H densify **OUT** (peek + A25 already failed held MDD in parent short-assist).  
This Stage B tests **one** residual lever: STOP overlay on the locked champion cell.

## Question

On locked recipe `CONF_RET3 · α=0.20 · H=5 · OFF=00631L`, does a pulse stop recover sealed MDD ≥ **0.00pp** vs `BASE_LIVE_CONF` while keeping held CAGR ≥ **+0.20pp** and held MDD ≥ **−0.50pp**?

## Non-actions

- α densify beyond 0.20 · H densify · confirm rewrite (RET1/RET1_PX)  
- Exact T+1 · tip rewrite · live clip / L1 · broker · FinPriv / E16 reopen  

## Base / parent

| ID | Spec |
|---|---|
| `BASE_LIVE_CONF` | live twin CONF_RET3 α=**0.10** H=5 |
| `SAT_A20_H5` | parent champion α=**0.20** H=5 · **no stop** |

## Grid (finite)

| ID | Spec |
|---|---|
| `A20_STOP_S02` | SAT_A20_H5 + stop **2%** from entry close |
| `A20_STOP_S03` | stop **3%** |
| `A20_STOP_S05` | stop **5%** |

## Gates (vs `BASE_LIVE_CONF`)

| Gate | Pass |
|---|---|
| CAGR | heldout lift ≥ **+0.20pp** |
| MDD | heldout MDD improve ≥ **−0.50pp** |
| Sealed hygiene | sealed MDD improve ≥ **0.00pp** |

## Verdicts

`HYGIENE_HIT` · `PARENT_KEEP` · `NO_LIFT`

- **HYGIENE_HIT**: STOP clears all three gates (better sealed than parent soft).  
- **PARENT_KEEP**: no STOP clears sealed≥0 without killing CAGR/MDD → keep `SAT_A20_H5` as-is for ACCEPT discussion.  
- Even HIT → paper only; no live wire.

## Reproduce

```bash
PYTHONPATH=scripts python3 scripts/sat_a20_sealed_hygiene_stageb.py
```

Artifacts: `research/ops/SAT_A20_SEALED_HYGIENE_*` · `repro/sat-a20-sealed-hygiene-stageb/`
