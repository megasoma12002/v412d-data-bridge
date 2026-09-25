# COOL_c8 × DH_dd06+FUSE — stack vs replace paper trial

Generated: `2026-09-25T07:10:33Z`  
Books: Stage-E `E22_v3_recv_pay_effdelay` · Soft-Frozen KEEP · **no live wire**  
Compare base: `FUSE_DH` (= current live FUSE+DH)

## Construction

| ID | Meaning |
|---|---|
| `FUSE_DH` | live 現況 = FUSE + DH |
| `FUSE_COOL` | **不疊** = FUSE + COOL（取代 DH） |
| `FUSE_DH_min_COOL` | **疊** = FUSE + min(DH, COOL) |
| `FUSE_DH_x_COOL` | **疊** = FUSE + (DH × COOL) |
| `LIVE_COOL` | observe twin（無 FUSE） |

## Held-out 2019+ (primary)

| book | role | CAGR | MDD | vs FUSE_DH CAGR giveback | vs FUSE_DH MDD↑ |
|---|---|---:|---:|---:|---:|
| `LIVE_STACK` | base | 15.56% | -25.27% | -0.67pp | -0.89pp |
| `LIVE_COOL` | observe | 15.29% | -14.86% | -0.40pp | +9.52pp |
| `FUSE_ONLY` | offense | 16.33% | -24.05% | -1.44pp | +0.33pp |
| `FUSE_DH` | live 現況 | 14.89% | -24.38% | — | — |
| `FUSE_COOL` | 不疊 | 15.07% | -14.62% | -0.17pp | +9.76pp |
| `FUSE_DH_min_COOL` | 疊 min | 14.62% | -14.84% | +0.27pp | +9.54pp |
| `FUSE_DH_x_COOL` | 疊 × | 14.32% | -14.54% | +0.58pp | +9.84pp |

## Sealed 2023+

| book | CAGR | MDD | vs FUSE_DH gb | vs FUSE_DH MDD↑ |
|---|---:|---:|---:|---:|
| `LIVE_STACK` | 22.28% | -9.71% | -2.58pp | +1.32pp |
| `LIVE_COOL` | 17.58% | -6.94% | +2.13pp | +4.10pp |
| `FUSE_ONLY` | 23.25% | -9.68% | -3.54pp | +1.35pp |
| `FUSE_DH` | 19.70% | -11.04% | — | — |
| `FUSE_COOL` | 16.76% | -6.92% | +2.94pp | +4.12pp |
| `FUSE_DH_min_COOL` | 16.64% | -6.88% | +3.06pp | +4.16pp |
| `FUSE_DH_x_COOL` | 16.69% | -6.70% | +3.01pp | +4.34pp |

## Exposure duty

| exposure | frac_defense | mean | min |
|---|---:|---:|---:|
| `LIVE_COOL` | 0.1602 | 0.9199 | 0.5000 |
| `FUSE_DH` | 0.0128 | 0.9936 | 0.5000 |
| `FUSE_COOL` | 0.1602 | 0.9199 | 0.5000 |
| `FUSE_DH_min_COOL` | 0.1652 | 0.9174 | 0.5000 |
| `FUSE_DH_x_COOL` | 0.1652 | 0.9155 | 0.2500 |

## Tip vs FUSE_DH (YTD / trailing 1y)

| book | ytd MDD↑ | ytd gb | 1y MDD↑ | 1y gb |
|---|---:|---:|---:|---:|
| `FUSE_COOL` | +0.98pp | +7.17pp | +0.98pp | +4.88pp |
| `FUSE_DH_min_COOL` | +1.13pp | +5.39pp | +1.13pp | +3.71pp |
| `FUSE_DH_x_COOL` | +1.33pp | +5.83pp | +1.33pp | +4.17pp |
| `LIVE_COOL` | +0.45pp | +2.13pp | +0.45pp | +1.15pp |

## Reading

- **不疊 (`FUSE_COOL`)**：用 COOL 換掉 DH；對齊 |MDD|≤17% 路線的單層 PROXY。
- **疊 min**：兩層都開時仍只縮到 50%；防衛日取聯集。
- **疊 ×**：兩層同時防衛可縮到 25%；防衛更深、giveback 通常更大。
- 本 trial **不**授權 live；cutover 仍 BLOCKED。

Repro: `repro/cool-c8-dh-fuse-stack-trial/`

Label: `COOL_C8_DH_FUSE_STACK_TRIAL_2026-09-25__PAPER_ONLY__NO_LIVE_WIRE`

