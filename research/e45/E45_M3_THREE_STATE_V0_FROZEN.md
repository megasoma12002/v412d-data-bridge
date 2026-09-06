# E45 M3 — Frozen Three-State Risk Machine v0 (BEFORE any sealed metrics)

Date: 2026-09-06  
Status: **FROZEN FOR PAPER SCREEN** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_NEW_MECHANISM_CHARTER.md` (M3 discrete state-machine stage)  
Sensor: `E45_M1_STATE_VECTOR_V0_FROZEN.md` intensity `s_t`  
Actuator vocabulary: `E45_M2_DEF_SLEEVE_V0_FROZEN.md` (`RELOC_TEL` / identity)  
Claimed MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** — do not invent a replacement

## Honesty bound

- State labels are **paper risk regimes**, not live Soft-Frozen / stitch authority.  
- DEF destination remains **`DEF_TEL`** (Telecom equity proxy). Still equity beta; not cash/duration.  
- Continuous M1/M2 overlays are **references**, not retuned inside this pack.

## States (v0)

| State | Intent |
|---|---|
| `NORMAL` | Earn equity risk premium — full Soft-Frozen BASE weights |
| `SLOW_BEAR` | Grind / elevated stress — partial relocate FIN+0050 → Telecom |
| `CRASH` | Shock / deep drawdown stress — strong relocate FIN+0050 → Telecom |

## Enter / exit (hysteresis — frozen)

Sensor: M1 equal-weight intensity `s_t ∈ [0,1]` (same freeze as M1; **do not retune features**).  
State is marked on close `t` using `s_t`. **Action lag:** schedule on date `t` applies `state_{t-1}` (Exact T+1 honesty).

| Transition | Rule (must hold for `N` consecutive closes) |
|---|---|
| `NORMAL → SLOW_BEAR` | `s_t ≥ 0.45` for **5** days |
| `NORMAL → CRASH` | `s_t ≥ 0.70` for **3** days (may skip SLOW_BEAR) |
| `SLOW_BEAR → CRASH` | `s_t ≥ 0.70` for **3** days |
| `SLOW_BEAR → NORMAL` | `s_t ≤ 0.32` for **5** days |
| `CRASH → SLOW_BEAR` | `s_t ≤ 0.52` for **5** days |
| `CRASH → NORMAL` | `s_t ≤ 0.30` for **5** days |

Initial state before first confirm: `NORMAL`.  
No single-day flicker: all transitions require the confirm streak above.

## Per-state action table (frozen)

Let Soft-Frozen targets be `w = (w_FIN, w_TEL, w_0050)`.  
`RELOC_TEL(u)` is the M2 relocate operator with fixed intensity `u` (not continuous `c·s`).

| State | Action |
|---|---|
| `NORMAL` | `w' = w` (identity; no E45 tax) |
| `SLOW_BEAR` | `w' = RELOC_TEL(u=0.40)` |
| `CRASH` | `w' = RELOC_TEL(u=0.75)` |

## Book IDs

| Book | Role |
|---|---|
| `M3_STATE_V0` | Primary discrete three-state machine (this freeze) |
| `M2_RELOC_TEL_C50` | Continuous M2 challenger reference (rebuild; not retuned) |
| `M1_EQW_C75` | Continuous M1 shrink reference (rebuild; not retuned) |
| `BASE_E16_E18_E22_v2s` | BASE reference |
| `BLEND_E45_A05` | E45 mild blend reference |
| `SLEEVE_FIN_ONLY_A10` | Observe OPERATING id — reference only |

## Diagnostics (non-binding)

Trailing YTD / 1y CAGR giveback vs BASE and state occupancy shares are **diagnostics only** — they do **not** open Soft-Frozen, DEFAULT, stitch, or HIGH_BETA ballots.

## Explicit non-actions

- Do **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots  
- Do **not** densify E45 mild-α as a substitute for M3  
- Do **not** retune enter/exit thresholds after seeing sealed scores (amendment = new `v1` freeze)  
- Do **not** invent a replacement for the retired MDD narrative  
- Do **not** treat `DEF_TEL` as cash or duration hedge  

## Qualification

Inherit charter §2 rules 1–6.  
**M3 pass:** `M3_STATE_V0` clears full §2 **and** COVID-ex held-out score ≥ continuous `M2_RELOC_TEL_C50`; else fail closed / autopsy.

Label: `E45_M3_THREE_STATE_V0_FROZEN_2026-09-06__PAPER_ONLY__STITCH_FORBIDDEN`
