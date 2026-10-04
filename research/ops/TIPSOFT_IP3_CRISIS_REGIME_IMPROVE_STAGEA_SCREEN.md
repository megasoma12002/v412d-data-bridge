# TIPSOFT_IP3_CRISIS_REGIME_IMPROVE_STAGEA_SCREEN

Date: 2026-10-04 · Verdict: **`CRISIS_REGIME_IMPROVE_OVERFIT`** · champion=**`R_RC_C00_G05`**
Register: **0kbm** · **CRISIS_REGIME_IMPROVE_PARALLEL** · mech=35 · HIT=0 · MDD_ONLY=0 · OVERFIT=9 · HELD_BLOCK=0 · NO_EDGE=0
Tip SHA: `8a29d7d674831f5fe733dd7bccfdd3ef781de41a`

## Base

- `L4_LIVE_P3_WITHIN` path `repro/research-live-align-gap-stagea/outputs/nav_L4_LIVE_P3_WITHIN.csv`
- y2020 MDD **-0.14431069977736088** · Mar2020 MDD **-0.1300110855317218** (2020-02-20→2020-03-23)
- era MDD base: 2015=-0.06977644054259868 · 2018=-0.06952301651514403 · 2022=-0.10827104372008856
- floors: held≥**0.1** · y2020/Mar MDD↑≥**0.5** · sealed≥**-0.25** · tipY≥**-1.0**
- router RA pct: {'CLIFF_RISK': 1.19, 'GRIND_RISK': 0.36, 'NORMAL': 98.46}

## Prior chain

- 0kbl: `MAJOR_DD_ATLAS_PARTIAL` — fuse_prem only partial cross-era; signal≠apply
- 0kbk: `CLIFF_GRIND_SPLIT_HIT` — champ GRIND specialist; no cliff specialist — motivates regime sleeves
- 0kbj: `IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020` — 0kbi AND gate hist OOS overfit 2020 — motivates cross-era floors
- 0kbi: `IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT` — AND champ `and::rvol63_l4&fuse_prem_neg5` reused as full-sample baseline
- 0kbf: `SOAK_OPEN` — soak freeze unchanged — this pack does not unlock SOAK_PASS
- 0kbg: `IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY` — uniform overlays hurt held — regime-conditional is the design bet

## Family summary

| Family | n | HIT | MDD help | held+ | max held | max y20 MDD↑ | max Mar MDD↑ | max sealed | max cross-era n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BASE_AND | 2 | 0 | 2 | 0 | -1.1071 | 7.1276 | 9.8236 | 0.1286 | 1 |
| BASE_CLIFF | 2 | 0 | 2 | 0 | -0.5076 | 6.8462 | 6.9606 | -2.423 | 0 |
| BASE_GRIND | 2 | 0 | 0 | 0 | -0.0923 | 0.0 | 0.0 | 0.0 | 0 |
| BASE_VOL | 2 | 0 | 1 | 0 | -0.8474 | 0.0391 | 0.6131 | 0.9443 | 1 |
| ROUTER | 27 | 0 | 27 | 9 | 0.5277 | 6.8462 | 6.9606 | 0.0 | 0 |

## Top arms

| Arm | fam | held | y2020 MDD↑ | Mar2020 MDD↑ | 2015 | 2018 | 2022 | sealed | tipY | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| R_RC_C00_G05 | ROUTER | 0.5277 | 5.4852 | 5.5769 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C00_G07 | ROUTER | 0.5277 | 5.4852 | 5.5769 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C00_G085 | ROUTER | 0.5277 | 5.4852 | 5.5769 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C025_G05 | ROUTER | 0.3999 | 4.0915 | 4.1599 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C025_G07 | ROUTER | 0.3999 | 4.0915 | 4.1599 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C025_G085 | ROUTER | 0.3999 | 4.0915 | 4.1599 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C05_G05 | ROUTER | 0.2694 | 2.7128 | 2.7582 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C05_G07 | ROUTER | 0.2694 | 2.7128 | 2.7582 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| R_RC_C05_G085 | ROUTER | 0.2694 | 2.7128 | 2.7582 | 0.0 | -0.0 | 0.0 | 0.0 | 0.0 | OVERFIT |
| BASE_AND_0KBI_S50 | BASE_AND | -1.1071 | 4.7225 | 4.8015 | -0.0 | 0.1545 | -0.4215 | 0.1286 | -6.8103 | TIP_BLOCK |
| BASE_VOL_W20_T012_F03 | BASE_VOL | -1.8246 | 0.0391 | 0.6131 | -0.0 | 0.268 | 0.0 | 0.9443 | -10.9078 | TIP_BLOCK |
| R_RA_C05_G085 | ROUTER | -0.3772 | 3.3726 | 3.429 | -0.0 | -0.3199 | 0.0 | -0.5513 | 0.1095 | MDD_BLOCK |
| R_RA_C05_G07 | ROUTER | -0.4232 | 3.3726 | 3.429 | -0.0 | -0.3199 | 0.0 | -0.5513 | 0.1095 | MDD_BLOCK |
| R_RA_C05_G05 | ROUTER | -0.4847 | 3.3726 | 3.429 | -0.0 | -0.3199 | 0.0 | -0.5513 | 0.1095 | MDD_BLOCK |
| BASE_CLIFFONLY_C025 | BASE_CLIFF | -0.5076 | 5.0967 | 5.1818 | -0.0 | -0.4798 | -0.0 | -2.423 | 0.1637 | MDD_BLOCK |
| R_RB_C05_G085 | ROUTER | -0.526 | 2.7128 | 2.7582 | -0.0 | -0.3199 | 0.0 | -0.5513 | -0.3184 | MDD_BLOCK |
| R_RA_C025_G085 | ROUTER | -0.5535 | 5.0967 | 5.1818 | -0.0 | -0.4798 | -0.0 | -2.423 | 0.1637 | MDD_BLOCK |
| R_RB_C05_G07 | ROUTER | -0.572 | 2.7128 | 2.7582 | -0.0 | -0.3199 | 0.0 | -0.5513 | -0.3184 | MDD_BLOCK |
| R_RA_C025_G07 | ROUTER | -0.5995 | 5.0967 | 5.1818 | -0.0 | -0.4798 | -0.0 | -2.423 | 0.1637 | MDD_BLOCK |
| R_RB_C05_G05 | ROUTER | -0.6334 | 2.7128 | 2.7582 | -0.0 | -0.3199 | 0.0 | -0.5513 | -0.3184 | MDD_BLOCK |
| R_RA_C025_G05 | ROUTER | -0.6609 | 5.0967 | 5.1818 | -0.0 | -0.4798 | -0.0 | -2.423 | 0.1637 | MDD_BLOCK |
| BASE_CLIFFONLY_C00 | BASE_CLIFF | -0.6913 | 6.8462 | 6.9606 | -0.0 | -0.6397 | 0.0 | -4.2764 | 0.2176 | MDD_BLOCK |
| R_RA_C00_G085 | ROUTER | -0.7372 | 6.8462 | 6.9606 | -0.0 | -0.6397 | 0.0 | -4.2764 | 0.2176 | MDD_BLOCK |
| R_RB_C025_G085 | ROUTER | -0.7758 | 4.0915 | 4.1599 | -0.0 | -0.4798 | 0.0 | -2.423 | -0.4776 | MDD_BLOCK |
| R_RA_C00_G07 | ROUTER | -0.7831 | 6.8462 | 6.9606 | -0.0 | -0.6397 | 0.0 | -4.2764 | 0.2176 | MDD_BLOCK |

## Optimize / disposition

1. Objective: regime-conditional crisis sleeves on L4 — held+ with Mar/y2020 MDD↑ and ≥1 non-2020 major DD not-worse
2. Champion `R_RC_C00_G05` fam=ROUTER held=0.5277 y2020MDD↑=5.4852 Mar2020MDD↑=5.5769 sealed=0.0 tipY=0.0 cross_era_imp=0 verdict=OVERFIT
3. Clears: HIT=0 · MDD_ONLY=0 · OVERFIT=9 · HELD_BLOCK=0 · NO_EDGE=0 / mech=35 (grid≤40)
4. Router pct RA cliff/grind/normal={'CLIFF_RISK': 1.19, 'GRIND_RISK': 0.36, 'NORMAL': 98.46}
5. vs priors: 0kbk SPLIT_HIT (regime tools differ) · 0kbj OVERFIT_2020 · 0kbl PARTIAL · 0kbg MDD_ONLY
6. Disposition: does **not** unlock soak freeze · does **not** recommend LIVE wire · research path only
7. Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_regime_improve_stagea.py`

Label: `TIPSOFT_IP3_CRISIS_REGIME_IMPROVE_STAGEA_SCREEN_2026-10-04__CRISIS_REGIME_IMPROVE_OVERFIT__CRISIS_REGIME_IMPROVE_PARALLEL`
