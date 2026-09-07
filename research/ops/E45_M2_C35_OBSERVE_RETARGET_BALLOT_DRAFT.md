# E45 M2 BIL_FX Observe Retarget C35 — OPEN Ballot **DRAFT**

Status: **DRAFT ONLY — NOT OPEN**  
Proposed ballot name: `E45 OPEN M2 BIL_FX relocate observe retarget C35`  
Date: 2026-09-07  
Chinese mirror: `research/ops/E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT.zh-TW.md`  
Evidence: `research/e45/E45_M2_C35_RETARGET_BALLOT.md`

> Does **NOT** change the operating lock. Remains paper-only until separate human **ACCEPT OPEN C35**.  
> Current OPERATING observe stays **`M2_RELOC_BIL_FX_C50`**.

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Parent sleeves OPERATING: FULL + A25 + A05 + FIN_A10 + **BIL_FX_C50**

## Proposal (if later ACCEPTed)

| Field | Value |
|---|---|
| Choice | Retarget M2 BIL_FX observe lock **C50 → C35** |
| New locked book | **`M2_RELOC_BIL_FX_C35`** |
| Prior lock | `M2_RELOC_BIL_FX_C50` (do not retire evidence; swap monitor lock only) |
| Sensor / actuator | M1 `s_{t-1}` · `RELOC_BIL_FX` · cut `c=0.35` |
| Why | Optimize giveback-min among §2 PASS cuts (held giveback ~+2.23 vs C50 ~+3.43) |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch? | **No** |
| Auto-OPEN C75? | **No** |

## Human choices

| Choice | Effect |
|---|---|
| **HOLD DRAFT** (default) | Keep C50 OPERATING |
| **ACCEPT OPEN C35** | Separate PR: update OPEN docs + dual-ledger + month-end pack lock |
| **REJECT** | Archive; keep C50 |

## Explicit non-actions

1. Do not silent-swap C50→C35 without ACCEPT.  
2. Do not stitch / Soft-Frozen / DEFAULT flip.  
3. Do not invent MDD replacement.  
4. Do not label BIL_FX as TWD cash.

Label: `E45_M2_C35_OBSERVE_RETARGET_BALLOT_DRAFT_2026-09-07__NOT_OPEN__STITCH_FORBIDDEN`
