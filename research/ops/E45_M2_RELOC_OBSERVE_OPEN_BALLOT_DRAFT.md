# E45 M2 Relocate Observe — OPEN Ballot **DRAFT**

Status: **DRAFT ONLY — NOT OPEN**  
Proposed ballot name: `E45 OPEN M2 BIL_FX relocate observe`  
Date: 2026-09-06  
Chinese mirror (non-binding): `research/ops/E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.zh-TW.md`

> **Does NOT** OPEN an observe sleeve, wire month-end, flip Soft-Frozen / DEFAULT, or authorize stitch.  
> Remains **PAPER ONLY** until a separate human **ACCEPT**.  
> §2 PASS is **not** auto-OPEN.

Soft-Frozen: **[0.50, 0.95] KEEP**  
Live DEFAULT books: **`E22_v2s_tw` KEEP**  
Live stitch: **still FORBIDDEN**  
Parent sleeves still OPERATING: FULL + A25 + A05 + `SLEEVE_FIN_ONLY_A10`  
HIGH_BETA: **DRAFT / NOT OPEN** (separate ballot)

**Locked book (default):** `M2_RELOC_BIL_FX_C50` — true DEF (`BIL × USDTWD`).  
`M2_RELOC_TEL_C50` is **not** the default (v0 equity proxy only; weaker COVID-ex).

## Proposal (if later ACCEPTed)

| Field | Value |
|---|---|
| Choice | OPEN **M2 BIL_FX relocate** paper observe (parallel) |
| Locked book (default) | **`M2_RELOC_BIL_FX_C50`** |
| Alternate (explicit human switch only) | `M2_RELOC_BIL_FX_C75` · or legacy `M2_RELOC_TEL_C50` (not recommended) |
| Sensor / actuator | M1 intensity `s_{t-1}` · `RELOC_BIL_FX` · cut `c=0.50` |
| DEF honesty | **`BIL_FX` = USD T-bill ETF × USDTWD mid** — FX risk; mid is optimistic; **not** local TWD cash |
| Baseline refs | `BASE_E16_E18_E22_v2s` · `SLEEVE_FIN_ONLY_A10` (do not retire) |
| Cadence (if ACCEPT) | Month-end parallel paper ledger + monitor (owner TBD in ACCEPT PR) |
| Live wire? | **No** |
| Soft-Frozen flip? | **No** |
| Stitch authorized? | **No** |
| Retire FULL / A25 / A05 / FIN_A10? | **No** |
| Merge DEF into `live_market.csv`? | **No** (research proxies under `data/def_proxies/` only) |

## Evidence pointers

- M2 v1 true DEF paper: `research/e45/E45_M2_TRUE_DEF_RELOCATE.md` (**§2 PASS** — `M2_RELOC_BIL_FX_C50/C75`)
- M2 v1 freeze: `research/e45/E45_M2_DEF_SLEEVE_V1_FROZEN.md`
- Repro: `repro/e45-m2-true-def-relocate/`
- DEF ingest: `research/e45/E45_M2_TRUE_DEF_DATA_INGEST.md` · `data/def_proxies/`
- v0 TEL pack (legacy ref only): `research/e45/E45_M2_DEF_SLEEVE_RELOCATE.md`
- M3 autopsy (does not unlock stitch): `research/e45/E45_M3_THREE_STATE_RISK.md`

## Why BIL_FX, not TEL

| Book | COVID-ex held-out @1x | §2 | Role |
|---|---:|:---:|---|
| `M2_RELOC_BIL_FX_C50` | **+3.20** | PASS | **Default lock** |
| `M2_RELOC_BIL_FX_C75` | **+3.41** | PASS | Alternate (higher cut) |
| `M2_RELOC_TEL_C50` | +0.16 | PASS | Legacy equity-DEF; **not default** |

## Why this is ballot-gated

1. Actuator is new vs operating E45 observe sleeves (different mechanism family).  
2. Destination has **FX / mid-price honesty** — must not be sold as local TWD cash.  
3. Register rules: observe OPEN needs explicit human ACCEPT; pack green ≠ OPEN.  
4. Soft-Frozen / DEFAULT / stitch stay out of scope for this ballot.

## Human choices

| Choice | Effect |
|---|---|
| **HOLD DRAFT** (default) | No OPEN; paper only |
| **ACCEPT OPEN** | Separate PR to promote DRAFT→OPERATING observe for **`M2_RELOC_BIL_FX_C50`** (not this file alone) |
| **ACCEPT OPEN (C75)** | Same, but lock `M2_RELOC_BIL_FX_C75` — must say so explicitly |
| **REJECT** | Archive; keep sleeve-local / blend observe path |

## Pre-ACCEPT checklist (must all be YES in the ACCEPT PR)

| # | Item | Required |
|---|---|---|
| 1 | Soft-Frozen live clip remains [0.50, 0.95] | YES |
| 2 | Live DEFAULT books remain `E22_v2s_tw` | YES |
| 3 | M2 v1 §2 PASS artifact present for locked BIL_FX book | YES |
| 4 | Retired MDD narrative still RETIRED | YES |
| 5 | No stitch / Soft-Frozen / DEFAULT flip bundled | YES |
| 6 | BIL_FX honesty on observe monitor banner (FX + mid optimistic; not TWD cash) | YES |
| 7 | Parent observe sleeves left operating in parallel | YES |
| 8 | Explicit human ACCEPT recorded | YES |
| 9 | Locked book is BIL_FX (not silent TEL fallback) | YES |

## Explicit non-actions

1. Do **not** live-stitch E45 / rewrite `forward/e21` history.  
2. Do **not** flip Soft-Frozen or DEFAULT books.  
3. Do **not** treat M2 observe clean prints as stitch license.  
4. Do **not** auto-OPEN from this draft file alone.  
5. Do **not** invent a replacement for the retired MDD narrative.  
6. Do **not** label `BIL_FX` as local TWD cash / risk-free.  
7. Do **not** default back to `M2_RELOC_TEL_C50` without an explicit human switch.

Label: `E45_M2_BIL_FX_OBSERVE_OPEN_BALLOT_DRAFT_2026-09-06__AWAITING_HUMAN_ACCEPT__NOT_OPEN__STITCH_FORBIDDEN`

## Improve pack cross-link

- FX sensitivity + TWD twin paper: `research/e45/E45_M2_BIL_FX_IMPROVE.md`
- Observe OPEN prep (await ACCEPT): `research/ops/E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md`
- Status: **DRAFT / NOT OPEN** unchanged until human ACCEPT

