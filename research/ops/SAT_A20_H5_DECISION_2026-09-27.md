# SAT_A20_H5 — Decision (2026-09-27)

Status: **DECISION_LANDED** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · L1=0.05 **KEEP** · **no live wire**  
Calendar: next tip session **2026-09-29** (9/25–28 holiday/weekend closed)

## Verdict

| Item | Call |
|---|---|
| Parent Stage A | **`MECH_HIT`** `SAT_A20_H5` (CONF densify α=0.20 H=5) |
| Stage B STOP hygiene | **`PARENT_KEEP`** (sealed MDD↑ −0.10 soft; STOP S02/S03/S05 no lift) |
| FIN-share levers | **`SAT_REF_ONLY`** (CLIP/COND/SKEW/CASH miss) |
| **This decision** | **Recommend OPEN paper observe** · live cutover **BLOCKED** |
| α/H densify further | **OUT** (Stage B) |

Binding numbers (vs `BASE_LIVE_CONF`): held CAGR↑ **+0.33pp** · held MDD↑ **−0.31pp** · sealed MDD↑ **−0.10pp** · tip OK.

## Why observe (not live)

1. Sealed hygiene is soft (−0.10pp) — STOP overlays did not clear ≥0.  
2. Live already wires `CONF_RET3_A10_H5` (α=0.10); A20 is densify of the same satellite.  
3. Human must OPEN observe before dual-paper month-end wire; separate ACCEPT for any live α flip.

## Human ballot (DRAFT — not executed)

```
OPEN paper observe: SAT_A20_H5 (00631L CONF densify α=0.20 H=5 under COOL)
```

After human OPEN: wire dual-paper `BASE_LIVE_CONF` ∥ `SAT_A20_H5` · cutover checklist stays **BLOCKED**.

## Explicit non-goals

- Live α 0.10→0.20 without observe trail  
- Soft-Frozen clip / L1 / Exact T+1 change  
- Broker / SendAlgo  

## Refs

- `NEXT_MECH_STAGEA_DECISION_PACK.md` · `SAT_A20_SEALED_HYGIENE_DECISION_PACK.md`  
- Ballot draft: `SAT_A20_H5_OBSERVE_BALLOT_DRAFT.md`  
- Cutover: `CUTOVER_CHECKLIST_SAT_A20_H5.md` (**BLOCKED**)

Label: `SAT_A20_H5_DECISION_2026-09-27__OPEN_OBSERVE_RECOMMENDED__NO_LIVE`
