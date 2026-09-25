# COOL × 台50反1 — Stage A Screen

Generated: `2026-09-25T14:35:39Z`
Status: **COOL_INV_SOFT** · baseline `BASE_LIVE_FUSE_COOL` · Soft-Frozen **KEEP** · live wire **false**
DEF=`00632R` · cool defend_frac=**16.02%** · listed_from **2014-10-23**

Coexist / HIT: **0** / 3

## Ranked (defending books)

| book | α | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |
|---|---:|---:|---:|---:|---:|---|---|
| `COOL_INV_A25` | 0.25 | -0.80 | -1.20 | +2.85 | +0.04 | Y | N |
| `COOL_INV_A50` | 0.50 | -1.82 | -2.99 | +5.49 | -1.40 | N | N |
| `COOL_INV_A100` | 1.00 | -4.46 | -2.27 | -0.11 | -8.38 | N | N |

## Sanity control

`ALWAYS_A50`: held CAGR↑ +2.73 · sealed MDD↑ -8.03 · tip=N (not promote)

## Binding

1. Soft-Frozen live + COOL_c8 params **KEEP**.
2. Even HIT → paper observe only; live `00632R` needs Class D ACCEPT.

Repro: `PYTHONPATH=scripts python3 scripts/cool_t50_inv_satellite_stagea.py`

Label: `COOL_T50_INV_SATELLITE_STAGEA_SCREEN_2026-09-25__COOL_INV_SOFT`
