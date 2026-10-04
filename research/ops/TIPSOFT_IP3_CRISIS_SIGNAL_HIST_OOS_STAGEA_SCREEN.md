# TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_SCREEN

Date: 2026-10-04 · Verdict: **`IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020`** · champ=**`and::rvol63_l4&fuse_prem_neg5`**
Register: **0kbj** · **SIGNAL_HIST_OOS_PARALLEL** · HIT=5 · WEAK=20 · MISS=14 · NO_DATA=26

## Data coverage (fail loud)

- NAV (`L4_LIVE_P3_WITHIN`): **2012-12-04** → 2026-09-29
- 0050 market: **2010-01-04** → 2026-09-01
- Panel: 2012-12-04 → 2026-09-29
- Note: L4/Soft NAV panel starts ~2012-12; 0050 OHLCV starts 2010-01. GFC ~2008 and 2011 NAV-twin episodes are NO_DATA (fail loud). Longest available twin world used for 2015 / 2018 / 2020.
- **FAIL_LOUD GFC_2008: episode 2008-09-01→2009-03-31 precedes panel_start=2012-12-04 (nav_start=2012-12-04, mkt_0050_start=2010-01-04) (required hist episode; marking NO_DATA)**

## Floors (hist OOS)

- IC≥0.05 (positive / stress-high) · hit≥0.55 · recall≥0.3 · F1≥0.2 · lead≥3.0d · FA≤0.15

## Champ by episode

| episode | verdict | IC_mdd10 | IC_crash10 | hit | recall | F1 | lead_d | FA_dec | trough | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GFC_2008 | NO_DATA |  |  |  |  |  |  |  |  | episode 2008-09-01→2009-03-31 precedes panel_start=2012-12-04 (nav_start=2012-12-04, mkt_0050_start=2010-01-04) |
| TW_CN_2015 | OOS_MISS | -0.294 | 0.04 | 0.4207 | 0.0 | 0.0 |  | 0.0209 | 2015-08-24 |  |
| EU_US_2011 | NO_DATA |  |  |  |  |  |  |  |  | episode 2011-07-01→2011-10-31 precedes panel_start=2012-12-04 (nav_start=2012-12-04, mkt_0050_start=2010-01-04) |
| Q4_2018 | OOS_WEAK | 0.0734 | 0.3066 | 0.6099 | 0.0984 | 0.1791 | 1.0 | 0.0209 | 2018-10-25 |  |
| MAR2020 | OOS_WEAK | 0.0466 | -0.1416 | 0.6724 | 0.5 | 0.3667 | 17.0 | 0.1678 | 2020-03-19 |  |

## Champ + top HIT arms × episode

| arm | episode | verdict | IC | hit | recall | F1 | lead | FA |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| and::rvol63_l4&fuse_prem_neg5 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| and::rvol63_l4&fuse_prem_neg5 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| and::rvol63_l4&fuse_prem_neg5 | MAR2020 | OOS_WEAK | 0.0466 | 0.6724 | 0.5 | 0.3667 | 17.0 | 0.1678 |
| and::rvol63_l4&fuse_prem_neg5 | Q4_2018 | OOS_WEAK | 0.0734 | 0.6099 | 0.0984 | 0.1791 | 1.0 | 0.0209 |
| and::rvol63_l4&fuse_prem_neg5 | TW_CN_2015 | OOS_MISS | -0.294 | 0.4207 | 0.0 | 0.0 |  | 0.0209 |
| or::neg_gap_ma200|dd63_l4 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| or::neg_gap_ma200|dd63_l4 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| or::neg_gap_ma200|dd63_l4 | MAR2020 | OOS_WEAK | 0.0954 | 0.7414 | 0.4545 | 0.4 | 9.0 | 0.1511 |
| or::neg_gap_ma200|dd63_l4 | Q4_2018 | OOS_HIT | 0.2257 | 0.7163 | 0.3934 | 0.5455 | 9.0 | 0.0289 |
| or::neg_gap_ma200|dd63_l4 | TW_CN_2015 | OOS_MISS | -0.1788 | 0.4414 | 0.0357 | 0.069 | 0.0 | 0.0289 |
| or::atr_like_20|dd63_l4 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| or::atr_like_20|dd63_l4 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| or::atr_like_20|dd63_l4 | MAR2020 | OOS_WEAK | -0.0847 | 0.6983 | 0.4545 | 0.3636 | 9.0 | 0.123 |
| or::atr_like_20|dd63_l4 | Q4_2018 | OOS_WEAK | 0.009 | 0.7376 | 0.4426 | 0.5934 | 9.0 | 0.0305 |
| or::atr_like_20|dd63_l4 | TW_CN_2015 | OOS_WEAK | -0.2341 | 0.5655 | 0.25 | 0.4 | 0.0 | 0.0305 |
| or::rvol20_l4|atr_like_20 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| or::rvol20_l4|atr_like_20 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| or::rvol20_l4|atr_like_20 | MAR2020 | OOS_WEAK | -0.1856 | 0.5948 | 0.5 | 0.3188 | 28.0 | 0.1819 |
| or::rvol20_l4|atr_like_20 | Q4_2018 | OOS_MISS | -0.2473 | 0.6099 | 0.0984 | 0.1791 | 9.0 | 0.0008 |
| or::rvol20_l4|atr_like_20 | TW_CN_2015 | OOS_WEAK | -0.0063 | 0.5517 | 0.2262 | 0.3689 |  | 0.0008 |
| or::rvol20_l4|dd63_l4 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| or::rvol20_l4|dd63_l4 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| or::rvol20_l4|dd63_l4 | MAR2020 | OOS_WEAK | 0.0135 | 0.6293 | 0.7273 | 0.4267 | 28.0 | 0.109 |
| or::rvol20_l4|dd63_l4 | Q4_2018 | OOS_WEAK | -0.0553 | 0.7305 | 0.4262 | 0.5778 | 9.0 | 0.0305 |
| or::rvol20_l4|dd63_l4 | TW_CN_2015 | OOS_MISS | -0.146 | 0.4414 | 0.0357 | 0.069 | 0.0 | 0.0305 |
| or::neg_gap_ma200|fuse_prem_neg5 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| or::neg_gap_ma200|fuse_prem_neg5 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| or::neg_gap_ma200|fuse_prem_neg5 | MAR2020 | OOS_WEAK | 0.3951 | 0.8017 | 0.4091 | 0.439 | 8.0 | 0.1889 |
| or::neg_gap_ma200|fuse_prem_neg5 | Q4_2018 | OOS_WEAK | 0.087 | 0.5532 | 0.0164 | 0.0308 |  | 0.0201 |
| or::neg_gap_ma200|fuse_prem_neg5 | TW_CN_2015 | OOS_MISS | -0.0239 | 0.5172 | 0.1786 | 0.3 | 12.0 | 0.0201 |
| or::cool_defend_l1|fuse_prem_neg5 | EU_US_2011 | NO_DATA |  |  |  |  |  |  |
| or::cool_defend_l1|fuse_prem_neg5 | GFC_2008 | NO_DATA |  |  |  |  |  |  |
| or::cool_defend_l1|fuse_prem_neg5 | MAR2020 | OOS_WEAK | -0.2454 | 0.7414 | 0.4091 | 0.375 | 8.0 | 0.1072 |
| or::cool_defend_l1|fuse_prem_neg5 | Q4_2018 | OOS_MISS | -0.0282 | 0.5745 | 0.1148 | 0.1892 | 0.0 | 0.049 |
| or::cool_defend_l1|fuse_prem_neg5 | TW_CN_2015 | OOS_WEAK | -0.0116 | 0.5448 | 0.25 | 0.3889 | 63.0 | 0.049 |

## Arm hist rank (excl Mar2020 ref)

| arm | family | n_HIT | n_WEAK | n_MISS | n_NO_DATA | Mar2020 |
| --- | --- | --- | --- | --- | --- | --- |
| and::rvol63_l4&fuse_prem_neg5 | and_combo | 0 | 1 | 1 | 2 | OOS_WEAK |
| or::neg_gap_ma200|dd63_l4 | or_combo | 1 | 0 | 1 | 2 | OOS_WEAK |
| or::atr_like_20|dd63_l4 | or_combo | 0 | 2 | 0 | 2 | OOS_WEAK |
| or::rvol20_l4|atr_like_20 | or_combo | 0 | 1 | 1 | 2 | OOS_WEAK |
| or::rvol20_l4|dd63_l4 | or_combo | 0 | 1 | 1 | 2 | OOS_WEAK |
| or::neg_gap_ma200|fuse_prem_neg5 | or_combo | 0 | 1 | 1 | 2 | OOS_WEAK |
| or::cool_defend_l1|fuse_prem_neg5 | or_combo | 0 | 1 | 1 | 2 | OOS_WEAK |
| andflag::fuse_neg_flag&fuse_prem_neg5 | and_combo | 0 | 1 | 1 | 2 | OOS_HIT |
| or::atr_like_20|fuse_prem_neg5 | or_combo | 0 | 1 | 1 | 2 | OOS_WEAK |
| kconfirm2::fuse_prem_neg5 | k_confirm | 0 | 1 | 1 | 2 | OOS_HIT |
| kconfirm2::fuse_neg_flag | k_confirm | 0 | 1 | 1 | 2 | OOS_HIT |
| or::rvol20_l4|fuse_prem_neg5 | or_combo | 0 | 0 | 2 | 2 | OOS_HIT |
| base::rvol20_l4 | baseline | 0 | 0 | 2 | 2 | OOS_WEAK |

## Optimize / disposition

1. Objective: hist OOS stress-test 0kbi SIGNAL_HIT arms on GFC/2015/(2011)/2018 + Mar2020 ref
2. Global `IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020` · champ `and::rvol63_l4&fuse_prem_neg5` · by_ep={'GFC_2008': 'NO_DATA', 'TW_CN_2015': 'OOS_MISS', 'EU_US_2011': 'NO_DATA', 'Q4_2018': 'OOS_WEAK', 'MAR2020': 'OOS_WEAK'}
3. Counts: HIT=5 WEAK=20 MISS=14 NO_DATA=26 / n=65
4. FAIL_LOUD GFC_2008: episode 2008-09-01→2009-03-31 precedes panel_start=2012-12-04 (nav_start=2012-12-04, mkt_0050_start=2010-01-04) (required hist episode; marking NO_DATA)
5. **SIGNAL_HIST_OOS / PARALLEL** — detection only; **signal ≠ apply**
6. Does **not** unlock soak freeze · does **not** recommend LIVE wire
7. No tip Soft promote · no year-oracle · Soft KEEP · Path4 OFF · broker false
8. Data limitation: panel/NAV start 2012-12-04; 0050 start 2010-01-04 — GFC 2008 = NO_DATA (fail loud)
9. Champ selected on Mar2020 (0kbi) fails OOS floors on available hist cores (2015 miss / 2008 no-data) — overfit-2020 risk elevated; do not promote signal→apply

Label: `TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_SCREEN_2026-10-04__IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020__SIGNAL_HIST_OOS_PARALLEL`
