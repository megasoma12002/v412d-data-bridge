# FIN_SAT_PATH3_WINDOW_PACK_STAGEA_SCREEN

Date: 2026-09-29 · `2026-09-29T07:55:43Z` · Verdict **`WINDOW_UNIFORM__THETA005_HELD_EDGE`**

## Absolute CAGR / MDD

| book | full CAGR | full MDD | held CAGR | held MDD | sealed CAGR | sealed MDD |
|---|---:|---:|---:|---:|---:|---:|
| `BASE_CTRL_LIVE_A10` | 12.74% | -14.42% | 16.31% | -14.42% | 19.51% | -6.20% |
| `COMP_H150_x_A20` | 12.74% | -15.08% | 16.85% | -14.53% | 21.33% | -6.56% |
| `SAT_A20_RELAX` | 12.94% | -14.73% | 16.64% | -14.73% | 19.64% | -6.30% |
| `P3_THETA_0.01` | 15.97% | -14.32% | 19.78% | -14.32% | 24.29% | -6.37% |
| `P3_THETA_0.005` | 16.30% | -14.32% | 20.08% | -14.32% | 24.26% | -6.37% |

## Lift vs BASE (pp)

| book | full CAGR↑ | full MDD↑ | held CAGR↑ | held MDD↑ | sealed CAGR↑ | sealed MDD↑ | tipY↑ | tip1y↑ | tipClean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `COMP_H150_x_A20` | +0.00 | -0.65 | +0.54 | -0.11 | +1.82 | -0.36 | -13.36 | -9.02 | False |
| `SAT_A20_RELAX` | +0.20 | -0.31 | +0.33 | -0.31 | +0.13 | -0.10 | +0.68 | +0.74 | True |
| `P3_THETA_0.01` | +3.23 | +0.10 | +3.48 | +0.10 | +4.78 | -0.17 | +2.73 | +1.74 | True |
| `P3_THETA_0.005` | +3.56 | +0.10 | +3.77 | +0.10 | +4.75 | -0.17 | +2.88 | +2.39 | True |

## Δ θ=0.005 − θ=0.01

| window | Δ CAGR↑ | Δ MDD↑ |
|---|---:|---:|
| full | +0.33 | +0.00 |
| heldout_2019_plus | +0.30 | +0.00 |
| sealed_2023_plus | -0.03 | +0.00 |

Rebuild θ=0.01 vs observe gap (CAGR↑): `{'full': 0.0, 'heldout_2019_plus': 0.0, 'sealed_2023_plus': 0.0}`

Repro: `repro/fin-sat-path3-window-pack-stagea/`

