# E45 Soft_A × Ungated C35 Mix — Freeze (BEFORE metrics)

Date: 2026-09-08  
Status: **FROZEN FOR PAPER SCREEN**  
Ballot: 「合成一檔 Soft_A×C35 混倉回測」  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **unchanged**

## Two mix definitions (both Exact T+1 honest)

### A — Schedule / intensity mix (one book)

Let `s` = M1 `s_{t-1}`, Soft_A scale `g∈{Bull:0, Side:0.25, Bear:0.75, Crisis:1}` on Soft-Frozen `regime_{t-1}`.

```
inten_λ = s · ((1−λ) · 1 + λ · g) = s · (1 − λ·(1−g))
```

`λ=0` → ungated C35 · `λ=1` → Soft_A · mid λ → one sleeve schedule, one fill path.  
Actuator: `RELOC_BIL_FX` · cut `c=0.35` (unchanged).

Grid: `λ ∈ {0.00, 0.25, 0.50, 0.75, 1.00}`

### B — Capital / NAV mix (two books, post-sim)

Independent Soft_A and ungated NAV paths; daily simple return blend:

```
r_mix = (1−λ)·r_ungated + λ·r_Soft_A
```

Same λ grid. Diagnostic only — not a single fill path (no netting).

## Scoreboard

Vs BASE: held-out score, sealed score, tip YTD/1y giveback gates, year MDD help {2015,2018,2020,2022}, days-on (schedule mix only).

## Pass read (informational)

Tip-clean **and** held-out > Soft_A → mix improves the Pareto frontier.  
Else: mix sits between poles; dual-monitor still preferred for honesty.

## Explicit non-actions

No Soft-Frozen / stitch / live wire · no invent MDD · no silent lock flip · no tip-window look-ahead.

Label: `E45_SOFTA_C35_MIX_FROZEN_2026-09-08__PAPER_ONLY__STITCH_FORBIDDEN`
