# Asymmetric 0050 Bull densify under COOL — Stage A Screen

Generated: `2026-09-25T18:27:41Z`
Verdict: **`CAGR_SOFT`** · base `BASE_LIVE_FUSE_COOL` · Soft-Frozen KEEP · **no live wire**

Base held 15.64% / -14.68%

Hits (MDD flat + CAGR + tip): `[]`
Held-flat tip-fail: `[]`
CAGR soft (MDD flat + tip, CAGR short): `['ASYMM_BSIDE_F0.75_E0.55', 'ASYMM_BSIDE_F0.75_E0.60', 'ASYMM_BSIDE_F0.75_E0.65', 'ASYMM_BULL_DEF_F0.75_E0.55', 'ASYMM_BULL_DEF_F0.75_E0.60', 'ASYMM_BULL_DEF_F0.78_E0.55', 'ASYMM_BULL_DEF_F0.78_E0.60']`

| id | track | gate | mean 0050 | CAGR lift | MDD↑ | band | tip | flat+cagr | hit |
|---|---|---|---:|---:|---:|:---:|:---:|:---:|:---:|
| `ASYMM_BSIDE_F0.75_E0.55` | BULL_SIDE_FIN_ROOM | REG_BULL_SIDE | 11.3% | +0.06pp | +0.41pp | Y | Y | N | N |
| `ASYMM_BSIDE_F0.75_E0.60` | BULL_SIDE_FIN_ROOM | REG_BULL_SIDE | 11.3% | +0.06pp | +0.41pp | Y | Y | N | N |
| `ASYMM_BSIDE_F0.75_E0.65` | BULL_SIDE_FIN_ROOM | REG_BULL_SIDE | 11.3% | +0.06pp | +0.41pp | Y | Y | N | N |
| `ASYMM_BULL_DEF_F0.78_E0.55` | BULL_OFF_DEF_REST | REG_BULL | 10.0% | +0.03pp | +0.18pp | Y | Y | N | N |
| `ASYMM_BULL_DEF_F0.78_E0.60` | BULL_OFF_DEF_REST | REG_BULL | 10.0% | +0.03pp | +0.18pp | Y | Y | N | N |
| `ASYMM_BULL_DEF_F0.75_E0.55` | BULL_OFF_DEF_REST | REG_BULL | 11.0% | +0.02pp | +0.39pp | Y | Y | N | N |
| `ASYMM_BULL_DEF_F0.75_E0.60` | BULL_OFF_DEF_REST | REG_BULL | 11.0% | +0.02pp | +0.39pp | Y | Y | N | N |
| `ASYMM_BULL_F0.75_E0.55` | BULL_FIN_ROOM | REG_BULL | 11.1% | -0.02pp | +0.40pp | Y | Y | N | N |
| `ASYMM_BULL_F0.75_E0.60` | BULL_FIN_ROOM | REG_BULL | 11.1% | -0.02pp | +0.40pp | Y | Y | N | N |
| `ASYMM_BULL_F0.75_E0.65` | BULL_FIN_ROOM | REG_BULL | 11.1% | -0.02pp | +0.40pp | Y | Y | N | N |
| `ASYMM_BSIDE_F0.78_E0.55` | BULL_SIDE_FIN_ROOM | REG_BULL_SIDE | 10.2% | -0.13pp | +0.16pp | Y | Y | N | N |
| `ASYMM_BSIDE_F0.78_E0.60` | BULL_SIDE_FIN_ROOM | REG_BULL_SIDE | 10.2% | -0.13pp | +0.16pp | Y | Y | N | N |
| `ASYMM_BSIDE_F0.78_E0.65` | BULL_SIDE_FIN_ROOM | REG_BULL_SIDE | 10.2% | -0.13pp | +0.16pp | Y | Y | N | N |
| `ASYMM_BULL_F0.78_E0.55` | BULL_FIN_ROOM | REG_BULL | 10.2% | -0.14pp | +0.18pp | Y | Y | N | N |
| `ASYMM_BULL_F0.78_E0.60` | BULL_FIN_ROOM | REG_BULL | 10.2% | -0.14pp | +0.18pp | Y | Y | N | N |
| `ASYMM_BULL_F0.78_E0.65` | BULL_FIN_ROOM | REG_BULL | 10.2% | -0.14pp | +0.18pp | Y | Y | N | N |
| `ASYMM_BULL_E0.55` | BULL_E_HI | REG_BULL | 9.6% | -0.00pp | +0.00pp | Y | N | N | N |
| `ASYMM_BULL_E0.60` | BULL_E_HI | REG_BULL | 9.6% | -0.00pp | +0.00pp | Y | N | N | N |
| `ASYMM_BULL_E0.65` | BULL_E_HI | REG_BULL | 9.6% | -0.00pp | +0.00pp | Y | N | N | N |

## Reading

- Objective: **MDD 持平 (↑≥0) + CAGR ≥+0.20pp + tip OK** under Bull-only densify.
- Live Soft-Frozen already densified F[0.60,0.80] E[0.00,0.50]; this screen densifies **further in Bull**.
- Even HIT → paper observe only.

Repro: `PYTHONPATH=scripts python3 scripts/asymm_0050_bull_densify_under_cool_stagea.py`

Label: `ASYMM_0050_BULL_DENSIFY_UNDER_COOL_STAGEA_SCREEN_2026-09-25__CAGR_SOFT__NO_LIVE_WIRE`
