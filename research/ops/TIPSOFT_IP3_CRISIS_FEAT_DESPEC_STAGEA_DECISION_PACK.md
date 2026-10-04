# TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_DECISION_PACK

Date: 2026-10-04 · Verdict: **`CRISIS_FEAT_DESPEC_PARTIAL`** · champion=**`k2::pct252::cool_defend_l1`**
Register: **0kbn** · Parents: 0kbm, 0kbl, 0kbk, 0kbj, 0kbf · **CRISIS_FEAT_DESPEC_PARALLEL**
Tip SHA: `452b877ce3a4607dd8124d26e6248838f8c1c145`

## Result

- family: **k_confirm** · transform **k2:pct252**
- cross-era score: **0.4229** (meanIC **0.2193** · minIC **0.2144**)
- non2020 ERA_HIT n: **1** `['2022']`
- eras_hit: `['2022']` · weak: `['2015']`
- IC primary **0.0034** · OOS ex-2020 **0.0021** · year-dummy|IC| **0.0565**
- specialization_reduced: **True**
- clears: HIT **0** · PARTIAL **6** · STILL_SPEC **108** · NO_EDGE **115**

## vs 0kbi AND / 0kbm OVERFIT router

- vs 0kbi `and::rvol63_l4&fuse_prem_neg5`: non2020_HIT **0** → champ **1** (Δ=1); cross-era Δ=0.9289
- vs 0kbm `R_RC_C00_G05` OVERFIT: held **0.5277** · y2020 MDD↑ **5.4852** · cross-era improve_n **0** — despec is detection-side response (feature transforms), not another 2020 router

## Disposition

- **CRISIS_FEAT_DESPEC_PARALLEL** — research path only; **signal ≠ apply**
- HIT only if global IC floors + ≥2 non-2020 era fires + OOS ex-2020 + year-dummy ceil
- STILL_SPEC if fires remain 2020-dominated
- Does **not** unlock soak freeze · does **not** recommend LIVE wire
- Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle

## Next

1. Objective: despec existing crisis features for cross-era fire (2015/2018/2022) without year-dummies
2. Champion `k2::pct252::cool_defend_l1` fam=k_confirm cross=0.4229 non2020_HIT=1 meanIC=0.2193 OOSex2020=0.0021 verdict=PARTIAL
3. Clears: HIT=0 · PARTIAL=6 · STILL_SPEC=108 · NO_EDGE=115 / n=229
4. specialization_reduced vs 0kbi AND: True (Δnon2020=1, Δcross=0.9289)
5. vs priors: 0kbi AND Mar HIT / 0kbj OVERFIT_2020 · 0kbl PARTIAL · 0kbm OVERFIT router
6. Disposition: does **not** unlock soak freeze · does **not** recommend LIVE wire · research path only
7. Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle

Label: `TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_DECISION_PACK_2026-10-04__CRISIS_FEAT_DESPEC_PARTIAL__CRISIS_FEAT_DESPEC_PARALLEL__NO_LIVE`

Screen: `TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_SCREEN.md` · Charter: `TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_CHARTER.md`
Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_feat_despec_stagea.py`
