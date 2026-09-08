# E45 M3 — Frozen Three-State Risk Machine v1 (BIL_FX) — BEFORE metrics

Date: 2026-09-08  
Status: **FROZEN FOR PAPER SCREEN** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**  
Parent: `E45_NEW_MECHANISM_CHARTER.md` · v0 autopsy `E45_M3_THREE_STATE_V0_FROZEN.md`  
Why v1: v0 used `RELOC_TEL` (equity proxy DEF) and **FAIL_AUTOPSY**. M2 §2 winners use **`RELOC_BIL_FX`**.  
Ballot context: leave C35×regime soft-mult; continue ladder with true-DEF discrete machine.

Sensor: `E45_M1_STATE_VECTOR_V0_FROZEN` intensity `s_t` (**do not retune**)  
Enter/exit hysteresis: **identical to v0** (do not retune thresholds)  
Actuator: M2 v1 **`RELOC_BIL_FX`** (`BIL×USDTWD` mid — FX risk; mid optimistic; not TWD cash)  
Claimed MDD: **`RETIRED_HISTORICAL_NARRATIVE`**

## Honesty bound

- Discrete states are paper risk regimes — not Soft-Frozen / stitch authority.  
- `BIL_FX` is USD T-bill × USDTWD mid — FX risk; mid optimistic; **not** merged into `live_market`.  
- Continuous ungated `M2_RELOC_BIL_FX_C35` is the M2 reference (current paper observe lock).  
- This is **not** a Soft-Frozen `regime_{t-1}` soft-gate on continuous C35.

## States / enter-exit

Same as v0 (`NORMAL` / `SLOW_BEAR` / `CRASH` + confirm streaks). Action lag: `state_{t-1}`.

## Per-state action table (frozen v1)

| State | Action |
|---|---|
| `NORMAL` | identity Soft-Frozen weights (no continuous C35 tax) |
| `SLOW_BEAR` | `RELOC_BIL_FX(u=0.40)` |
| `CRASH` | `RELOC_BIL_FX(u=0.75)` |

## Books

| Book | Role |
|---|---|
| `M3_BIL_FX_V1` | Primary discrete machine (this freeze) |
| `M2_RELOC_BIL_FX_C35` | Continuous M2 reference (observe lock rebuild) |
| `M3_STATE_V0` | Prior TEL discrete autopsy rebuild |
| `BASE_E16_E18_E22_v2s` | BASE |
| `BLEND_E45_A05` / `SLEEVE_FIN_ONLY_A10` | E45 tax-control refs |

## Qualification

Charter §2 rules 1–6.  
**M3 v1 pass:** `M3_BIL_FX_V1` clears full §2 **and** COVID-ex held-out score ≥ continuous `M2_RELOC_BIL_FX_C35`.  
Else: fail closed / autopsy — do **not** densify C35×regime soft-mult as substitute.

Tip YTD/1y giveback vs BASE are **diagnostics only** (non-binding).

## Explicit non-actions

No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot · no invent MDD · no retune enter/exit after sealed · no silent observe-lock flip · no label BIL_FX as TWD cash.

Label: `E45_M3_THREE_STATE_BIL_FX_V1_FROZEN_2026-09-08__PAPER_ONLY__STITCH_FORBIDDEN`
