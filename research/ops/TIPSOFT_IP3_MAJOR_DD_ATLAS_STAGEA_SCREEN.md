# TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_SCREEN

Date: 2026-10-04 · Register **0kbl** · Verdict **`MAJOR_DD_ATLAS_PARTIAL`**
Tip SHA: `c56778cf785a764f3077f0eb154dc80855caef8e`

## Coverage

- 0050 from **2010-01-04** · Soft/L4 from **2012-12-04**
- **No pre-2010 / GFC** in-repo
- Atlas n(≥8%)=61 · n(≥10%)=44 · major deduped=22

## Major DDs by regime (deduped ≥10%)

- CLIFF: n=12 · {'n': 12, 'median_depth': 0.1146, 'median_ttm_days': 14.0, 'median_velocity_pp_day': 0.8388, 'median_recovery_days': 20.0, 'eras': ['2010', '2011', '2015', '2018', '2020_mar', '2021', '2022', '2024', '2025']}
- GRIND: n=4 · {'n': 4, 'median_depth': 0.1902, 'median_ttm_days': 53.5, 'median_velocity_pp_day': 0.3096, 'median_recovery_days': None, 'eras': ['2011', '2015', '2018', '2022']}
- OTHER: n=6 · {'n': 6, 'median_depth': 0.1117, 'median_ttm_days': 24.5, 'median_velocity_pp_day': 0.4775, 'median_recovery_days': 22.0, 'eras': ['2010', '2011', '2012', '2026']}

## Named ref coverage

- `EU_US_2011` (2011): n=9 labels=['CLIFF', 'GRIND'] max_depth=0.1961
- `TW_CN_2015` (2015): n=9 labels=['CLIFF', 'GRIND', 'OTHER'] max_depth=0.218
- `Q4_2018` (2018): n=8 labels=['CLIFF', 'GRIND', 'OTHER'] max_depth=0.1477
- `MAR2020_CLIFF` (2020_mar): n=11 labels=['CLIFF'] max_depth=0.2653
- `MID2020_RESIDUAL` (2020_mid): n=3 labels=['OTHER'] max_depth=0.0033
- `BEAR_2022` (2022): n=27 labels=['CLIFF', 'GRIND', 'OTHER'] max_depth=0.3638

## Cross-era detector score (exclude Mar2020)

| arm | eras | OOS_HIT | WEAK | MISS | non2020 HIT | eras_hit |
|---|---:|---:|---:|---:|---:|---|
| `base::fuse_prem_neg5` | 7 | 2 | 3 | 2 | 2 | 2015,2024 |
| `base::fuse_neg_flag` | 7 | 2 | 2 | 3 | 2 | 2015,2024 |
| `base::atr_like_20` | 7 | 1 | 3 | 3 | 1 | 2024 |
| `base::neg_gap_ma200` | 7 | 1 | 3 | 3 | 1 | 2021 |
| `or::rvol20_l4|atr_like_20` | 7 | 1 | 3 | 3 | 1 | 2026 |
| `and::rvol63_l4&fuse_prem_neg5` | 7 | 1 | 1 | 5 | 1 | 2024 |
| `base::consec_down_mkt` | 7 | 1 | 1 | 5 | 1 | 2022 |
| `base::cool_defend_l1` | 7 | 1 | 1 | 5 | 1 | 2021 |
| `base::rvol20_mkt` | 7 | 1 | 1 | 5 | 1 | 2024 |
| `or::rvol20_l4|fuse_prem_neg5` | 7 | 1 | 1 | 5 | 1 | 2015 |

## Best incl Mar2020

- `base::fuse_prem_neg5` OOS_HIT=2 eras=['2015', '2024']

## Parents

- 0kbk: Cliff/grind taxonomy + GRIND_SPECIALIST champ — atlas extends to all eras.
- 0kbj: Hist OOS overfit 2020 — atlas tests generalization excl/incl Mar2020.
- 0kbi: AND champ `and::rvol63_l4&fuse_prem_neg5` reused when Soft features exist.
- 0kbf: Soak freeze unchanged — atlas Stage A does not unlock SOAK_PASS.

## Optimize / disposition

- Objective: major historical DD atlas — cliff vs grind across eras + detector generalization
- Coverage: 0050 from 2010-01-04 · Soft/L4 from 2012-12-04 · **no pre-2010/GFC in-repo**
- Taxonomy (0kbk): depth≥8%/10% · CLIFF ttm≤20 vel≥0.004 · GRIND ttm≥40
- Major (≥10%) regime counts: CLIFF=12 · GRIND=4 · OTHER=6 · n=22
- Best excl-Mar2020: `base::fuse_prem_neg5` OOS_HIT=2 non2020=2
- Best incl-Mar2020: `base::fuse_prem_neg5` OOS_HIT=2
- Implication: Some cross-era lift exists but floors are uneven — consistent with 0kbk SPLIT_HIT (regime tools differ) and 0kbj OVERFIT_2020 (Mar window strongest).
- Disposition: signal≠apply · soak freeze unchanged · no LIVE · no tip Soft · no year-oracle
- Soft KEEP · Path4 OFF · broker false · Exact T+1
