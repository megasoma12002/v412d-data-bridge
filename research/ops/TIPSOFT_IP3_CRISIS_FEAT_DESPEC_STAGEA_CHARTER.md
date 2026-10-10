# TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_CHARTER

Date: 2026-10-04
Register: **0kbn** · Parents: 0kbm, 0kbl, 0kbk, 0kbj, 0kbf
Mech: **TIPSOFT_IP3_CRISIS_FEAT_DESPEC** · Label: **CRISIS_FEAT_DESPEC_PARALLEL**

## Question

Can transforms / normalizations / confirms on **existing** crisis features
(rvol20/63, atr_like, MA gap, dd63, fuse_prem_neg, fuse_neg_flag, cool_defend,
consec_down — no new exotic data) produce detectors or light gates that keep
stress signal quality, fire outside 2020 (2015/2018/2022), and avoid
year-dummy / Mar2020-only routers?

## Motivation (parents)

- 0kbi SIGNAL_HIT refine AND `and::rvol63_l4&fuse_prem_neg5`
- 0kbj HIST_OOS_OVERFIT_2020 on that AND
- 0kbl MAJOR_DD_ATLAS_PARTIAL — fuse_prem only partial cross-era
- 0kbk CLIFF_GRIND_SPLIT_HIT — regime tools differ
- 0kbm CRISIS_REGIME_IMPROVE_OVERFIT — router 2020 MDD help, cross-era 0

## Screen families (lag-1 causal)

1. Raw baseline (0kbh/0kbi arms)
2. Rolling z-score / percentile rank (252/504d)
3. Vol-of-vol / change in rvol (delta 5/21)
4. Feature vs own long median (252/504d)
5. k-confirm on transformed features
6. Simple AND of two despec'd features (small grid)
7. Optional light cash-gate CF on best despec — report held + cross-era MDD

## Ranking / floors

- Primary rank = **cross-era score** (mean/min OOS IC across 2015/2018/2022/2020)
- Leave-one-era-out discipline (select on 3, evaluate held-out)
- HIT: global IC floors + ≥2 non-2020 era ERA_HIT + OOS ex-2020 OK + year-dummy ceil
- Forbidden: year/month/episode-label inputs; Mar2020-only primary rank

## Constraints

- Soft KEEP · Path4 OFF · broker false · soak freeze unchanged
- signal≠apply · no tip Soft LIVE · no Soft FIN/TEL ACCEPT
