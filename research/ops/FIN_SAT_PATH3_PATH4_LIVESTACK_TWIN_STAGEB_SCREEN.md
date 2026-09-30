# FIN_SAT_PATH3_PATH4_LIVESTACK_TWIN_STAGEB_SCREEN

Date: 2026-09-30 · Verdict: **`LIVESTACK_TWIN_MDD_BLOCK`** · champion=**`LIVE_P3_WITHIN`** · fill=`exact_t1`
Register: **0kap** · base=`BASE_LIVE_FUSE_COOL`

## Arms vs live stack

| Arm | vs live | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |
|---|---|---:|---:|---:|---:|---:|---|
| LIVE_P3_WITHIN | MDD_BLOCK | 0.8475 | 0.3296 | -0.5026 | 2.8524 | 2.0757 | 10-5 |
| LIVE_P3_P4_CASH_00025 | MDD_BLOCK | 0.4137 | 0.0401 | -0.53 | 2.6826 | 2.025 | 9-6 |
| LIVE_P3_P4_CASH_0005 | MDD_BLOCK | 0.3216 | -0.0385 | -0.5231 | 3.1852 | 2.2802 | 7-8 |
| LIVE_P3_P4_CASH_001 | MDD_BLOCK | 0.5078 | 0.1384 | -0.5192 | 3.1308 | 2.1696 | 9-6 |
| LIVE_P4_ONLY_001 | NO_EDGE | -0.3898 | -0.2182 | -0.0914 | 0.003 | -0.1522 | 5-10 |

## Champion `LIVE_P3_WITHIN` yearly vs live

| Year | Live ret% | Chal ret% | Ret lift pp |
|---:|---:|---:|---:|
| 2012 | 0.55 | 0.67 | +0.12 |
| 2013 | 7.26 | 5.99 | -1.27 |
| 2014 | 7.31 | 7.63 | +0.33 |
| 2015 | -1.66 | -1.86 | -0.20 |
| 2016 | 14.21 | 11.24 | -2.97 |
| 2017 | 17.74 | 20.15 | +2.41 |
| 2018 | 7.82 | 8.24 | +0.42 |
| 2019 | 20.24 | 18.71 | -1.53 |
| 2020 | 5.47 | 6.66 | +1.20 |
| 2021 | 19.47 | 21.50 | +2.03 |
| 2022 | 6.53 | 4.93 | -1.61 |
| 2023 | 12.64 | 16.39 | +3.75 |
| 2024 | 10.24 | 10.91 | +0.67 |
| 2025 | 10.39 | 10.70 | +0.31 |
| 2026 | 31.52 | 33.29 | +1.76 |

## Optimize live

1. **Keep live Soft + COOL_c8 + FUSE `SELL_a75` as the base** — tip Soft twin does not clear a free P3/P4 upgrade.
2. **Path3 WITHIN:** tip/held look good (held **+0.85** tipY **+2.85**) but **sealed MDD −0.50 → `MDD_BLOCK`**. Do not cut over on Soft-core HIT alone; need sealed-MDD disposition or MDD-harden before ACCEPT.
3. **Path4:** under live stack hurts held vs P3-only and stays `MDD_BLOCK` → **Path4 live OFF**; Soft sticky 0050 KEEP.
4. **P4-only:** `NO_EDGE` (held −0.39).
5. Soft KEEP · broker false · Path4 live flag OFF · no wire this pack

Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_path4_livestack_twin_stageb.py`

Label: `FIN_SAT_PATH3_PATH4_LIVESTACK_TWIN_STAGEB_SCREEN_2026-09-30__LIVESTACK_TWIN_MDD_BLOCK`
