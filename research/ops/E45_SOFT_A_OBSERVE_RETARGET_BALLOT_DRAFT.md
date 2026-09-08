# E45 Soft_A Observe Retarget — OPEN Ballot **DRAFT**

Status: **DRAFT ONLY — NOT OPEN**  
Proposed ballot: `E45 OPEN M2 BIL_FX observe retarget C35 → Soft_A`  
Date: 2026-09-08  
Evidence: `research/ops/E45_FOUR_PATH_RECOVER_RESEARCH.md` · `E45_C35_SOFT_GATE_RESEARCH.md`

> Does **NOT** change the operating lock until separate human **ACCEPT**.  
> Current OPERATING observe stays **`M2_RELOC_BIL_FX_C35`**.

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**

## Proposal (if later ACCEPTed)

| Field | Value |
|---|---|
| Choice | Retarget M2 BIL_FX observe lock **ungated C35 → Soft_A** |
| New locked book | **`M2_C35_SOFT_A`** |
| Spec | Soft-Frozen `regime_{t-1}` mult Bull0 / Side0.25 / Bear0.75 / Crisis1.0 · `RELOC_BIL_FX` · c=0.35 |
| Prior lock | `M2_RELOC_BIL_FX_C35` (keep as long-score twin if Path2 also ACCEPT) |
| Why | Tip YTD/1y **PASS/PASS**; held-out **+0.83** (best tip-clean recover vs hard +0.72) |
| Cost vs ungated | Held-out drops **+1.81 → +0.83** (Path4 tradeoff) |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch? | **No** |

## Human choices

| Choice | Effect |
|---|---|
| **HOLD** (default) | Keep ungated C35 OPERATING |
| **ACCEPT OPEN Soft_A** | Swap observe lock to Soft_A (paper only); optional keep ungated as Path2 twin |
| **REJECT** | Archive Soft_A retarget |

## Explicit non-actions

1. Do not silent-swap lock without ACCEPT.  
2. Do not stitch / Soft-Frozen / DEFAULT flip.  
3. Do not invent MDD replacement.  
4. Do not treat Soft_A as live wire.

Label: `E45_SOFT_A_OBSERVE_RETARGET_BALLOT_DRAFT_2026-09-08__NOT_OPEN__STITCH_FORBIDDEN`
