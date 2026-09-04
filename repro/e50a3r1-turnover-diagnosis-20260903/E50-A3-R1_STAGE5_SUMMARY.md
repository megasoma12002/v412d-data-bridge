# Stage-5 Research Summary

Draft only. **No retune of C2/C4/C8/F1. No promotion. No E45. PR #19 stays draft.**

## 1. Stage-5A — Horizon + structure OOF

**Decision: `OOF_NO_NEW_HORIZON_STRUCTURE_DUAL_GATE_WINNER`**

| Finding | Detail |
|---|---|
| TECH2_H21 baseline | IC 0.1147, turn 2.05%, boot **0.8066** PASS |
| Horizon 63 | IC rises (TECH2_DEF_H63 IC **0.159**) but bootstrap collapses (~0.17–0.53) |
| Defensive structure | DEF4 / DEF_ONLY / TECH2_DEF fail boot (0.50–0.59) |
| Orth / interaction | MOM_ORTH_DEF best near-miss boot **0.6596**; INTER / ORTH_VAL fail |

Artifact: `E50-A3-R1_STAGE5_HORIZON_STRUCTURE_OOF.md`

## 2. Stage-5B — Score blend + regime pick OOF

**Decision: `OOF_NO_NEW_BLEND_REGIME_DUAL_GATE_WINNER`**

| Cell | boot | both |
|---|---:|---|
| BLEND_TECH2_30_DEF4_70 | **0.6972** (near miss &lt; 0.70) | False |
| BLEND_TECH2_70_DEF4_30 | 0.642 | False |
| REGIME_PICK_TECH2_ON_DEF4_OFF | 0.604 | False |
| Other blends / picks | ≤0.58 | False |

Do **not** round 0.6972 to a pass. Do **not** held-out near-misses.

Artifact: `E50-A3-R1_STAGE5B_BLEND_REGIME_OOF.md`

## 3. Saturation map (experimental gates)

| Layer | Outcome |
|---|---|
| Portfolio rules C2/C4/C8 | MIXED_HELDOUT |
| TECH2/PRICE8 × regime × λ | no new OOF winner |
| Family × regime cuts | no new OOF winner |
| Atomic TECH2_VALUE F1 | MIXED_HELDOUT (val worse) |
| Horizon / orth / def structure | no new OOF winner |
| Score blend / regime pick | no new OOF winner (0.697 near miss) |

## 4. Implication

Under current experimental 2.5% / 0.70 gates, incremental alpha packing around TECH2+defensive is exhausted. Meaningful next work needs a **genuinely new OOF hypothesis class** (e.g. different execution/outcome definition, multi-name interaction with explicit degeneracy checks, or a non-breadth regime that both partitions and clears dual gates) — still OOF-selected; no gate promotion; no merge of #19.
