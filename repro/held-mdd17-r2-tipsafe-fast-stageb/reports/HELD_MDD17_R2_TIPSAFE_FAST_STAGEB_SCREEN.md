# Tip-safe FAST — Stage B Screen (R2)

Generated: `2026-09-25T06:53:31Z`
Books: `E22_v3_recv_pay_effdelay` · Soft-Frozen **KEEP** · live wire **False**
Anchor: `FAST_x08_ex06_f50_d21` (held gb~+0.56pp, tip MDD fail)
Band: `[-0.145, -0.13]` · stretch gb≤0.56 · preserve≤0.7 · ok≤1.0
Verdict: **`TIP_FAIL`** · winners: `['ANCHOR_FAST_x08_ex06_f50_d21', 'COOL_c3_f50_d21', 'COOL_c5_f50_d21']`

| id | track | held CAGR | held MDD | band | gb | tip_ok | tip ytd↑ | tip 1y↑ |
|---|---|---:|---:|---|---:|---|---:|---:|
| `COOL_c5_f50_d21` | COOL_EXT | 15.63% | -14.42% | True | -0.0694 | False | -0.9934 | -0.9934 |
| `COOL_c3_f50_d21` | COOL_EXT | 15.31% | -14.50% | True | 0.2534 | False | -1.1163 | -1.1163 |
| `ANCHOR_FAST_x08_ex06_f50_d21` | CTRL | 15.00% | -14.45% | True | 0.5584 | False | -0.9862 | -0.9862 |
| `COOL_c8_f50_d21` | COOL_EXT | 15.29% | -14.86% | False | 0.2667 | True | 2.5977 | 2.5977 |
| `COOL_c10_f55_d21` | COOL_EXT | 15.25% | -15.61% | False | 0.314 | True | 0.0507 | 0.0507 |
| `GATE_g04_f50_d21` | BOOK_GATE | 15.17% | -14.61% | False | 0.3929 | True | 0.7291 | 0.7291 |
| `COOL_c8_f55_d21` | COOL_EXT | 15.06% | -15.71% | False | 0.5045 | True | 2.6703 | 2.6703 |
| `HYB_b04_f55_d21_c8` | DUAL_ENTRY | 14.95% | -15.44% | False | 0.6102 | True | 1.2693 | 1.2693 |
| `GATE_g04_f55_d21` | BOOK_GATE | 14.87% | -15.56% | False | 0.6916 | True | 1.3675 | 1.3675 |
| `DUAL_b04_f55_d21` | DUAL_ENTRY | 14.87% | -15.51% | False | 0.6965 | True | 0.8083 | 0.8083 |
| `DUAL_b04_f50_d21` | DUAL_ENTRY | 14.77% | -14.74% | False | 0.7932 | True | 1.1902 | 1.1902 |
| `DUAL_b04_f55_d18` | DUAL_ENTRY | 14.72% | -15.59% | False | 0.8453 | True | 0.6423 | 0.6423 |
| `EXIT_ex075_f50_d18` | FAST_EXIT | 14.65% | -14.94% | False | 0.909 | True | 3.0012 | 3.0012 |
| `FLOOR_f55_d24` | FLOOR_UP | 14.65% | -15.31% | False | 0.9091 | True | 0.2237 | 0.2237 |
| `FLOOR_f55_d18` | FLOOR_UP | 14.64% | -15.32% | False | 0.9194 | True | 2.418 | 2.418 |
| `DUAL_b04_f50_d18` | DUAL_ENTRY | 14.62% | -14.73% | False | 0.9437 | True | 0.6396 | 0.6396 |
| `BASE_LIVE` | BASE | 15.56% | -25.27% | False | 0.0 | True | 0.0 | 0.0 |

## Reading

- Stage B seeks tip-safe variants that preserve ~+0.56pp held giveback.
- Soft-Frozen tip untouched; HIT → paper observe only.

Repro: `repro/held-mdd17-r2-tipsafe-fast-stageb/` · Charter: `HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER`

Label: `HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN_2026-09-25__TIP_FAIL`
