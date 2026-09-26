# TEL T3 densify / T2 half / near-flat — Stage A Screen

Generated: `2026-09-26T11:58:10Z`
Verdict: **`TEL_NEARFLAT_READY`** · base `BASE_LIVE_FUSE_COOL` · Soft-Frozen KEEP · **no live wire**
Floors: HIT +0.20pp · near-flat +0.15pp

HIT: `[]`
NEARFLAT: `['D3_A100_C100_B00']`
SOFT (<+0.15): `['D3_A150_C100_B50', 'D3_A050_C050_B00', 'D3_A050_C050_B50', 'D3_A100_C050_B00', 'D3_A100_C050_B50', 'D3_A150_C050_B00', 'D3_A150_C050_B50']`
MDD_BLOCK: `['D3_A050_C100_B00', 'D3_A050_C100_B50', 'D3_A100_C100_B50', 'D3_A150_C100_B00', 'T2_ALWAYS_A25', 'T2_ALWAYS_A50', 'T2_ALWAYS_A75', 'T2_ALWAYS_A100', 'T2_PROP_A50', 'T2_PROP_A100']`

| id | track | CAGR↑h | MDD↑h | MDD↑s | tip | nf | hit |
|---|---|---:|---:|---:|:---:|:---:|:---:|
| `D3_A100_C100_B00` | P1_T3_DENSIFY | +0.16pp | +0.06pp | +0.02pp | Y | Y | N |
| `D3_A150_C100_B50` | P1_T3_DENSIFY | +0.01pp | +0.02pp | +0.01pp | Y | N | N |
| `D3_A050_C050_B00` | P1_T3_DENSIFY | -0.01pp | -0.04pp | +0.02pp | Y | N | N |
| `D3_A050_C050_B50` | P1_T3_DENSIFY | -0.01pp | -0.04pp | +0.02pp | Y | N | N |
| `D3_A100_C050_B00` | P1_T3_DENSIFY | -0.01pp | -0.04pp | +0.02pp | Y | N | N |
| `D3_A100_C050_B50` | P1_T3_DENSIFY | -0.01pp | -0.04pp | +0.02pp | Y | N | N |
| `D3_A150_C050_B00` | P1_T3_DENSIFY | -0.01pp | -0.04pp | +0.02pp | Y | N | N |
| `D3_A150_C050_B50` | P1_T3_DENSIFY | -0.01pp | -0.04pp | +0.02pp | Y | N | N |
| `T2_ALWAYS_A100` | P2_T2_HALF | +0.26pp | +0.16pp | -0.23pp | Y | N | N |
| `T2_PROP_A50` | P2_T2_HALF | +0.11pp | +0.04pp | -0.00pp | Y | N | N |
| `T2_ALWAYS_A75` | P2_T2_HALF | +0.10pp | +0.24pp | -0.21pp | Y | N | N |
| `D3_A050_C100_B00` | P1_T3_DENSIFY | +0.09pp | -0.04pp | -0.02pp | Y | N | N |
| `T2_PROP_A100` | P2_T2_HALF | +0.09pp | -0.04pp | -0.02pp | Y | N | N |
| `T2_ALWAYS_A50` | P2_T2_HALF | +0.06pp | +0.12pp | -0.27pp | Y | N | N |
| `D3_A050_C100_B50` | P1_T3_DENSIFY | +0.06pp | +0.01pp | -0.01pp | Y | N | N |
| `D3_A100_C100_B50` | P1_T3_DENSIFY | +0.03pp | +0.05pp | -0.02pp | Y | N | N |
| `D3_A150_C100_B00` | P1_T3_DENSIFY | +0.03pp | +0.07pp | -0.11pp | Y | N | N |
| `T2_ALWAYS_A25` | P2_T2_HALF | -0.05pp | +0.02pp | -0.12pp | Y | N | N |

Repro: `PYTHONPATH=scripts python3 scripts/tel_t3_densify_stagea.py`

Label: `TEL_T3_DENSIFY_STAGEA_SCREEN_2026-09-26__TEL_NEARFLAT_READY`
