# FIN_SAT_PATH3_WRONG_STAY_CENSUS_STAGEA_CHARTER

Date: 2026-09-29
Status: **Stage A — Path3 wrong-stay census** · Soft-Frozen **KEEP** · Path3 observe θ=0.01 **KEEP** · fill/emit **OFF** · no live
Parents: 0k9x `COMP_STAY_MISS` · 0k9v yearly 14–1 · θ paper challenger 0.005 (0ka3/0ka4)
Register: **0ka5**

## Question

各曆年 Path3 **站錯**（held ≠ episode-best COMP/SAT）次數與嚴重度如何分布？2022 是否唯一 SEVERE COMP_WRONG 年？θ=0.005 是否減少站錯？

## Method (pre-registered)

- Reuse **0k9x** episode definition (year-clipped contiguous book runs)
- Wrong when `book != argmax(episode COMP ret, SAT ret)`
- Severity: **SEVERE** = wrong ∧ P3−BASE≤-0.5 ∧ days≥10; **MODERATE** = wrong ∧ (P3−BASE≤-0.1 ∨ P3−best≤-0.3); else **MILD**
- θ grid: `[0.01, 0.005]` (observe 0.01 · challenger 0.005)
- No live / Soft-Frozen KEEP / fill/emit OFF / no severity expand after peek

Label: `FIN_SAT_PATH3_WRONG_STAY_CENSUS_STAGEA_CHARTER_2026-09-29__WRONG_STAY_CENSUS__NO_LIVE`
