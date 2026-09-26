# COOL × 台50正2（00631L）搶反彈 — Stage A Screen

Generated: `2026-09-26T08:05:46Z`
Status: **`MDD_BLOCK`** · baseline `BASE_LIVE_FUSE_COOL` · Soft-Frozen **KEEP** · live wire **false**
OFF=`00631L` · sell_amp=**0.75** · cool defend_frac=**16.02%** · exits=**38** · listed_from **2014-10-31**

Coexist / HIT: **0** / 12

## Ranked (exit-pulse books)

| book | α | H | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `REB_A10_H10` | 0.10 | 10 | +0.74 | +1.28 | -0.57 | -1.20 | Y | N |
| `REB_A25_H10` | 0.25 | 10 | +1.75 | +2.98 | -1.47 | -3.45 | N | N |
| `REB_A10_H5` | 0.10 | 5 | +0.38 | +0.85 | -0.23 | -1.23 | Y | N |
| `REB_A25_H5` | 0.25 | 5 | +0.82 | +1.82 | -0.65 | -3.24 | Y | N |
| `REB_A10_H3` | 0.10 | 3 | +0.07 | -0.02 | -0.22 | -1.55 | Y | N |
| `REB_A25_H3` | 0.25 | 3 | +0.66 | +1.29 | -0.40 | -3.28 | Y | N |
| `REB_A50_H10` | 0.50 | 10 | +3.21 | +5.14 | -3.60 | -7.08 | N | N |
| `REB_A50_H3` | 0.50 | 3 | +1.30 | +3.24 | -1.07 | -6.31 | Y | N |
| `REB_A50_H5` | 0.50 | 5 | +1.42 | +4.37 | -3.04 | -5.96 | N | N |
| `REB_A10_H21` | 0.10 | 21 | +0.19 | +0.05 | -2.78 | -8.58 | N | N |
| `REB_A25_H21` | 0.25 | 21 | -0.17 | -0.81 | -14.84 | -23.13 | N | N |
| `REB_A50_H21` | 0.50 | 21 | -3.08 | -6.36 | -37.67 | -45.96 | N | N |

## Controls

`ALWAYS_A25`: held CAGR↑ +5.64 · sealed MDD↑ -24.21 · tip=N (not promote)
`DEFEND_A25_H5` (wrong timing): held CAGR↑ -2.64 · sealed MDD↑ -20.03 · tip=N

## Binding

1. Soft-Frozen live + COOL_c8 params **KEEP**.
2. Even HIT → paper observe only; live `00631L` needs Class D ACCEPT.

Repro: `PYTHONPATH=scripts python3 scripts/cool_t50_lev_rebound_stagea.py`

Label: `COOL_T50_LEV_REBOUND_STAGEA_SCREEN_2026-09-26__MDD_BLOCK`
