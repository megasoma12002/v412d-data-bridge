# E45 Sideways-Conditional Gate — Freeze (BEFORE metrics)

Date: 2026-09-08  
Status: **FROZEN FOR PAPER SCREEN**  
Ballot context: 「側盤怎麼辦」+「清 tip 犧牲長期分數」— experimentable residue after Soft_A grid  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **`M2_RELOC_BIL_FX_C35` unchanged**

## Thesis

Constant Sideways multipliers (0.15–0.50) are largely screened. Remaining lever is **conditional Sideways** — open Sideways defense only when an extra lag-1 condition says stress is still active — aiming for tip PASS **and** held-out > Soft_A (+0.83).

## Baselines (rebuild, not retuned)

| Book | Role |
|---|---|
| `M2_RELOC_BIL_FX_C35` | Ungated lock |
| `M2_C35_HARD_BEAR_CRISIS` | Tip hygiene floor |
| `M2_C35_SOFT_A` | Best prior tip-clean recover |

## Predeclared challengers (frozen)

Shared: Bull=0 · Bear=0.75 · Crisis=1.0 · cut c=0.35 · sensor M1 `s_{t-1}` · Soft-Frozen `regime_{t-1}`  
Sideways opens only if extra condition holds; else Sideways mult=0.

| Book | Sideways condition (all lag-honest) |
|---|---|
| `SIDE_CONT` | `regime_{t-2} ∈ {Bear,Crisis}` (stress continuation) |
| `SIDE_HIGH_S80` | `s_{t-1} ≥ Q80(s)` |
| `SIDE_DD05` | equal-weight sleeve proxy ≥5% below 60d peak (lag-1) |
| `SIDE_DD10` | same, ≥10% below 60d peak |
| `SIDE_MAX10` | Soft_A Sideways 0.25 but max **10** consecutive Sideways-on days, then 0 until leave Sideways |
| `SIDE_MAX20` | same, max **20** consecutive |

Sideways intensity when open: **0.25** (Soft_A level), except CONT/HIGH_S/DD which also use 0.25 when condition true.

## Pass read (informational)

Tip-clean **and** held-out > Soft_A → candidate for Soft_A successor ballot draft.  
Else: Sideways-conditional residue closed / autopsy; tip/score tradeoff remains Soft_A or dual-monitor.

## Explicit non-actions

No Soft-Frozen / stitch / live wire · no invent MDD · no silent lock flip · no tip-window look-ahead dampener.

Label: `E45_SIDEWAYS_CONDITIONAL_FROZEN_2026-09-08__PAPER_ONLY__STITCH_FORBIDDEN`
