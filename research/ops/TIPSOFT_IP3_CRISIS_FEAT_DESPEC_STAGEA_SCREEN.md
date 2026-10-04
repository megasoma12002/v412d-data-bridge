# TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_SCREEN

Date: 2026-10-04
Register: **0kbn** · **CRISIS_FEAT_DESPEC_PARALLEL** · arms=229 · HIT=0 · PARTIAL=6 · STILL_SPEC=108 · NO_EDGE=115
Verdict: **`CRISIS_FEAT_DESPEC_PARTIAL`**
Tip SHA: `a5d1a92939a0aa2ea3921096a61c11d4445b9548`

## Champion (cross-era rank)

- arm: `k2::pct252::cool_defend_l1`
- family: **k_confirm**
- despec_verdict: **PARTIAL**
- cross_era_score: **0.4229**
- mean/min IC: **0.2193** / **0.2144**
- non2020 ERA_HIT: **1** `['2022']`
- eras_hit: `['2022']` · weak: `['2015']`
- IC primary / OOS ex-2020 / year-dummy|IC|: **0.0034** / **0.0021** / **0.0565**
- specialization_reduced vs 0kbi AND: **True**

## Cross-era table (champ vs priors)

- despec champ: `{"arm": "k2::pct252::cool_defend_l1", "despec_verdict": "PARTIAL", "cross_era_score": 0.4229, "mean_ic": 0.2193, "min_ic": 0.2144, "n_non2020_hit": 1, "eras_hit": ["2022"], "eras_weak": ["2015"], "era_ics": {"2015": 0.2242, "2018": null, "2022": 0.2144, "2020": null}, "era_verdicts": {"2015": "ERA_WEAK", "2018": "MISS", "2022": "ERA_HIT", "2020": "MISS"}, "ic_primary": 0.0034, "ic_oos_ex2020": 0.0021, "year2020_dummy_abs_ic": 0.0565}`
- 0kbi AND: `{"arm": "and::rvol63_l4&fuse_prem_neg5", "despec_verdict": "NO_EDGE", "cross_era_score": -0.506, "mean_ic": -0.3638, "min_ic": -0.5688, "n_non2020_hit": 0, "eras_hit": [], "eras_weak": [], "era_ics": {"2015": -0.4618, "2018": -0.5688, "2022": 0.0707, "2020": -0.4954}, "era_verdicts": {"2015": "MISS", "2018": "MISS", "2022": "MISS", "2020": "MISS"}, "ic_primary": 0.1776, "ic_oos_ex2020": 0.1725, "year2020_dummy_abs_ic": 0.1231}`
- 0kbh rvol20: `{"arm": "raw::rvol20_l4", "despec_verdict": "NO_EDGE", "cross_era_score": -0.6137, "mean_ic": -0.4171, "min_ic": -0.7864, "n_non2020_hit": 0, "eras_hit": [], "eras_weak": [], "era_ics": {"2015": -0.3424, "2018": -0.2281, "2022": -0.3116, "2020": -0.7864}, "era_verdicts": {"2015": "MISS", "2018": "MISS", "2022": "MISS", "2020": "MISS"}, "ic_primary": 0.1249, "ic_oos_ex2020": 0.1193, "year2020_dummy_abs_ic": 0.1554}`
- 0kbm router (apply OVERFIT prior): `{"register": "0kbm", "verdict": "CRISIS_REGIME_IMPROVE_OVERFIT", "champ": "R_RC_C00_G05", "held": 0.5277, "y2020_mdd_imp": 5.4852, "mar2020_mdd_imp": 5.5769, "cross_era_improve_n": 0, "note": "regime router OVERFIT \u2014 2020 MDD help, cross-era improve_n=0"}`

## Leave-one-era-out (despec pool)

- held-out **2015**: select `and::vsmed252::neg_gap_ma60&vsmed252::neg_gap_ma200` → MISS IC=-0.0719
- held-out **2018**: select `k2::pct252::cool_defend_l1` → MISS IC=None
- held-out **2022**: select `and::k3::pct252::cool_defend_l1&vsmed252::neg_gap_ma60` → MISS IC=0.067
- held-out **2020**: select `k2::pct252::cool_defend_l1` → MISS IC=None

## Top arms

| arm | family | verdict | cross | n_non2020 | meanIC | minIC | OOSex2020 | yd|IC| |
|---|---|---|---|---|---|---|---|---|
| `k2::pct252::cool_defend_l1` | k_confirm | PARTIAL | 0.4229 | 1 | 0.2193 | 0.2144 | 0.0021 | 0.0565 |
| `and::k2::pct252::cool_defend_l1&pct252::cool_defend_l1` | and_despec | PARTIAL | 0.4207 | 1 | 0.2178 | 0.2115 | -0.0153 | 0.0587 |
| `and::k2::pct252::cool_defend_l1&k3::pct252::cool_defend_l1` | and_despec | PARTIAL | 0.419 | 1 | 0.2167 | 0.2092 | 0.0001 | 0.0519 |
| `k3::pct252::cool_defend_l1` | k_confirm | PARTIAL | 0.412 | 1 | 0.2121 | 0.1999 | -0.0013 | 0.0484 |
| `and::k3::pct252::cool_defend_l1&pct252::cool_defend_l1` | and_despec | PARTIAL | 0.4107 | 1 | 0.2112 | 0.1981 | -0.0183 | 0.0526 |
| `pct252::cool_defend_l1` | pct_rank | PARTIAL | 0.4099 | 1 | 0.2106 | 0.197 | -0.0159 | 0.0638 |
| `and::k3::pct252::cool_defend_l1&vsmed252::neg_gap_ma60` | and_despec | STILL_SPEC | 0.2726 | 0 | 0.2723 | 0.0013 | 0.0385 | 0.0161 |
| `and::k2::pct252::cool_defend_l1&vsmed252::neg_gap_ma60` | and_despec | STILL_SPEC | 0.2723 | 0 | 0.2722 | 0.0004 | 0.0402 | 0.0095 |
| `and::vsmed504::neg_gap_ma60&vsmed252::neg_gap_ma200` | and_despec | STILL_SPEC | 0.2614 | 0 | 0.2765 | -0.0603 | 0.1181 | 0.0422 |
| `and::vsmed252::neg_gap_ma60&vsmed252::neg_gap_ma200` | and_despec | STILL_SPEC | 0.2567 | 0 | 0.2747 | -0.0719 | 0.1113 | 0.003 |
| `and::pct252::cool_defend_l1&vsmed252::neg_gap_ma60` | and_despec | STILL_SPEC | 0.2562 | 0 | 0.265 | -0.0354 | 0.01 | 0.0057 |
| `vsmed252::neg_gap_ma60` | vs_median | STILL_SPEC | 0.254 | 0 | 0.2642 | -0.0412 | 0.1123 | 0.0187 |

## Cash-gate CF (illustrative; not primary HIT path)

```json
{
  "note": "ILLUSTRATIVE ONLY \u2014 signal\u2260apply; no size-overlay / tip Soft promote",
  "label": "champ_despec_cf",
  "held_cagr_lift_pp": -7.4344,
  "sealed_mdd_improve_pp": -1.4414,
  "tipY_cagr_lift_pp": -21.8599,
  "pct_cash_days": 60.34,
  "window": [
    "2020-02-20",
    "2020-03-23"
  ],
  "window_mdd_improve_pp": 13.0011,
  "base_window_mdd": -0.130011,
  "chal_window_mdd": 0.0,
  "cross_era_mdd_improve_pp": {
    "2015": 4.9262,
    "2018": 6.9523,
    "2022": 7.0038,
    "2020": 13.0011
  },
  "held_pos": false,
  "non2020_mdd_improve_n": 3,
  "primary_hit_path": false
}
```

## Family summary

    family  n  n_hit  n_partial  n_still_spec  best_cross  best_non2020
and_despec 28      0          3            25      0.4207             1
delta_rvol  8      0          0             4     -0.1503             0
 k_confirm 80      0          2            31      0.4229             1
  pct_rank 32      0          1            15      0.4099             1
prior_0kbi  1      0          0             0     -0.5060             0
       raw 16      0          0             7      0.2415             0
 vs_median 32      0          0            14      0.2540             0
    zscore 32      0          0            12      0.2382             0

## Constraints kept

- Soft KEEP · Path4 OFF · broker false · Exact T+1
- **signal ≠ apply** · soak freeze unchanged · no LIVE · no tip Soft promote
- No year/month/episode-label inputs · primary rank = cross-era (not Mar-only)
