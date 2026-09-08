# E45 Soft_A × C35 Mix — Decision Pack

Date: 2026-09-08  
Status: **RESEARCH DONE — mix interpolates poles; no tip-clean Soft_A beater**  
Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged

## Question

Synthesize Soft_A and ungated C35 into **one** mixed book (schedule intensity mix and NAV capital mix).

## Result (λ = Soft_A weight)

| λ | Schedule held / tip | NAV mix held / tip |
|---:|---|---|
| 0.00 (ungated) | +1.81 / dirty | +1.81 / dirty |
| 0.25 | +1.59 / dirty | +1.56 / dirty |
| 0.50 | +1.18 / dirty | +1.32 / dirty |
| 0.75 | +0.82 / dirty | +1.07 / dirty |
| 1.00 (Soft_A) | **+0.83 / PASS** | **+0.83 / PASS** |

Only pure Soft_A is tip-clean. Mid mixes buy held-out by re-dirtying tip — **no Pareto improve** vs Soft_A under tip binding.

## Binding read

1. Mix is a **smooth interpolation**, not a new frontier point.  
2. Dual-monitor (Soft_A tip twin + ungated long-score twin) remains cleaner for honesty than a single mid-λ book.  
3. Do not retarget observe to MIX_SCHED_L50/L75.

Artifacts: `E45_SOFTA_C35_MIX_RESEARCH.md` · freeze · `scripts/e45_softa_c35_mix_paper.py`
