# E45 Novel Strategy Screen — Freeze (BEFORE metrics)

Date: 2026-09-08  
Status: **FROZEN FOR PAPER SCREEN**  
Ballot: 「請想新的策略」— outside exhausted C35×Soft-Frozen-regime soft-mult / Sideways / mid-λ mix  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **unchanged**

## What is explicitly NOT in this screen

- Soft_A / HARD Sideways mult grids  
- Soft_A×C35 mid-λ mix  
- M3 fixed-u discrete retune  
- E45 mild-α densify as primary

## Novel challengers (frozen)

Shared actuator unless noted: `RELOC_BIL_FX` · c=0.35 · Exact T+1.  
Baselines rebuild: ungated C35 · Soft_A · BASE.

| ID | Idea |
|---|---|
| `DD05_FULL_ELSE_SOFT` | Lag-1 EW-market DD≤−5% → full M1 `s` (ungated C35); else Soft_A scale `g` on `s` |
| `DD05_FULL_ELSE_OFF` | DD≤−5% → full `s`; else intensity 0 (drawdown-armed only) |
| `FXZ_RELOC_C35` | Intensity = USDTWD 60d return z risk map (TWD weak↑ → risk-off); **no** M1 `s` |
| `FXZ_GATE_SOFT_A` | Soft_A `s·g`, but only on when FX risk map ≥ 0.5 (FX confirms) |
| `FINONLY_SOFT_A` | Soft_A timing `s·g`, relocate **Financial only** → BIL_FX (0050/TEL untouched) |
| `SOFT_A_NEST_A05` | Soft_A relocate schedule **plus** whole-book blend-α=0.05 exposure nest |

### FX risk map (frozen)

`x_t = log(USDTWD_mid_t / USDTWD_mid_{t-1})`  
`z_t = (x_t − mean_60(x)) / std_60(x)`  
`fx_t = clip(max(0, z_t) / 2, 0, 1)` · action uses `fx_{t-1}`

### Soft_A scale `g` (unchanged)

Bull 0 / Sideways 0.25 / Bear 0.75 / Crisis 1.0 on Soft-Frozen `regime_{t-1}`.

## Scoreboard

Held-out score · sealed · tip YTD/1y · year MDD help · vs Soft_A tip-clean beat.

## Pass read

Tip-clean **and** held-out > Soft_A → novel candidate for ballot draft.  
Else: autopsy; dual-monitor Soft_A+ungated remains operational stack.

## Explicit non-actions

No Soft-Frozen / stitch / live · no invent MDD · no silent lock flip.

Label: `E45_NOVEL_STRATEGY_SCREEN_FROZEN_2026-09-08__PAPER_ONLY__STITCH_FORBIDDEN`
