# TIPSOFT_IP3_CRISIS_CLIFF_VS_GRIND_STAGEA_SCREEN

Date: 2026-10-04 · Register **0kbk** · Verdict **`CLIFF_GRIND_SPLIT_HIT`**
Tip SHA: `28efb54200aab10dafbd88343f987b17ba3226af`

## Shape (primary L4)

- CLIFF: n=2 · med_depth=0.1319 · med_ttm=19.5d · med_vel=0.6768pp/d · med_rec=17.0 · shapes={'V': 1, 'L': 1, 'U_partial': 0}
- GRIND: n=2 · med_depth=0.0561 · med_ttm=29.0d · med_vel=0.2612pp/d · med_rec=0.0 · shapes={'V': 1, 'L': 1, 'U_partial': 0}
- OTHER: n=3 · med_depth=0.0695 · med_ttm=17.0d · med_vel=0.409pp/d · med_rec=6.0 · shapes={'V': 1, 'L': 2, 'U_partial': 0}

## Ref window coverage

- `MAR2020_CLIFF`: n=2 labels=['CLIFF'] expect=CLIFF
- `TW_CN_2015`: n=1 labels=['OTHER'] expect=CLIFF_OR_GRIND
- `Q4_2018`: n=1 labels=['OTHER'] expect=GRIND_OR_CLIFF
- `MID2020_RESIDUAL`: n=1 labels=['GRIND'] expect=GRIND
- `LATE2020_RESIDUAL`: n=1 labels=['OTHER'] expect=GRIND_OR_OTHER

## Detector lift (CLIFF vs GRIND)

| arm | specialize | cliff IC/hit/R | grind IC/hit/R | ΔIC |
|---|---|---|---|---|
| `and::rvol63_l4&fuse_prem_neg5` | GRIND_SPECIALIST | -0.2842/0.7714/0.4286 | 0.4586/0.6619/0.0 | -0.7428 |
| `base::consec_down_mkt` | GRIND_SPECIALIST | -0.6061/0.8082/0.5238 | 0.1362/0.7291/0.3167 | -0.7423 |
| `base::cool_defend_l1` | GRIND_SPECIALIST | -0.5172/0.4041/0.2381 | 0.1324/0.5255/0.7 | -0.6496 |
| `base::rvol63_l4` | GRIND_SPECIALIST | -0.0357/0.6531/0.0 | 0.5607/0.6497/0.0 | -0.5964 |
| `base::rvol20_mkt` | MILD_SPLIT | -0.8516/0.8163/0.0 | -0.1033/0.8024/0.2333 | -0.7483 |
| `or::rvol20_l4|fuse_prem_neg5` | MILD_SPLIT | -0.7632/0.8/0.6667 | -0.0943/0.6945/0.2 | -0.6689 |
| `base::atr_like_20` | MILD_SPLIT | -0.8074/0.7918/0.1905 | -0.3037/0.7617/0.0167 | -0.5037 |
| `base::rvol20_l4` | MILD_SPLIT | -0.7639/0.702/0.3333 | -0.2753/0.6456/0.0 | -0.4886 |
| `base::fuse_prem_neg5` | MILD_SPLIT | -0.2954/0.8163/0.3333 | 0.0444/0.7515/0.2833 | -0.3398 |
| `base::fuse_neg_flag` | MILD_SPLIT | -0.3671/0.7837/0.3333 | -0.0435/0.7332/0.3167 | -0.3236 |
| `or::rvol20_l4|atr_like_20` | MILD_SPLIT | -0.8951/0.7551/0.4762 | -0.666/0.666/0.0 | -0.2291 |
| `base::proxy_mdd63_soft` | MILD_SPLIT | -0.0619/0.5673/0.0952 | -0.2377/0.6864/0.9667 | 0.1758 |

## Counterfactual (illustrative only)

- full champ cash-gate held **-2.3008** · sealedMDD↑ **-1.4756**
- cliff-only held **1.6895** · MarMDD↑ **9.8236**
- grind-only held **-0.0** · windowMDD↑ **0.0**
- held Δ(cliff−grind) **1.6895**

## Parents

- 0kbj: Hist OOS overfit 2020 — this pack tests if that is cliff-specific.
- 0kbi: AND champ `and::rvol63_l4&fuse_prem_neg5` reused for regime lift.
- 0kbh: Singles (rvol/atr/dd/fuse) reused as baseline arms.
- 0kbf: Soak freeze unchanged — cliff/grind Stage A does not unlock SOAK_PASS.
- 0kb4: Defend residual mid/late 2020 tagged as grind-like reference windows.

## Optimize / disposition

- Objective: cliff(急殺) vs grind(長期跌) regime taxonomy + detector lift + illustrative CF
- Primary taxonomy depth≥0.08 cliff_n≤20 grind_min≥40 on l4_nav
- Shape: cliff n=2 med_depth=0.1319 med_ttm=19.5 · grind n=2 med_depth=0.0561 med_ttm=29.0
- Champ `and::rvol63_l4&fuse_prem_neg5` specialize=GRIND_SPECIALIST cliffIC=-0.2842 grindIC=0.4586
- Specialists: cliff=0 · grind=4 · mild=10 · none=1
- Illustrative CF held cliff=1.6895 grind=-0.0 Δ=1.6895 (NOT promote)
- Implication: Detectors specialize more on GRIND than CLIFF in-regime; 0kbj OVERFIT_2020 Mar-window HIT is not the same as within-cliff IC — grind still needs different tools (0kb4 defend residual).
- Disposition: signal≠apply · soak freeze unchanged · no LIVE · no tip Soft · no year-oracle
- Soft KEEP · Path4 OFF · broker false · Exact T+1
