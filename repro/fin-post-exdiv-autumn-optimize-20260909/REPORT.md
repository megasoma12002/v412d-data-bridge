# FIN_POST_EXDIV_KD — autumn parameter small-search (paper)

Generated: `2026-09-09T10:33:35.940915+00:00`
Status: **STOP** · Soft-Frozen **KEEP** · live **KD_OPT untouched**

Grid: 4 seasons × 3 K × 3 hold = **36**

## Anchors

| id | heldout | tip_clean |
|---|---:|---|
| `KD_OPT` | 0.647 | True |
| probe baseline `OCT20_DEC10 Klt25 H40` | 0.422 | True |

## Best autumn

- **`AUT_OCT20_DEC10_Klt20_H40`** held-out **+0.428** · tip_clean=True
- vs KD_OPT Δ held-out **-0.220**
- Beats KD_OPT (tip+held-out)? **False**

## Top 10 autumn

| id | heldout | MDD↑ | CAGR gb | YTD | 1y | vs KD Δ |
|---|---:|---:|---:|---|---|---:|
| `AUT_OCT20_DEC10_Klt20_H40` | 0.428 | 0.678 | 0.500 | PASS | PASS | -0.220 |
| `AUT_OCT20_DEC10_Klt20_H60` | 0.428 | 0.678 | 0.500 | PASS | PASS | -0.220 |
| `AUT_OCT20_DEC10_Klt25_H40` | 0.422 | 0.677 | 0.509 | PASS | PASS | -0.225 |
| `AUT_OCT20_DEC10_Klt25_H60` | 0.422 | 0.677 | 0.509 | PASS | PASS | -0.225 |
| `AUT_OCT1_DEC15_Klt30_H60` | 0.404 | 0.575 | 0.342 | PASS | PASS | -0.243 |
| `AUT_OCT1_DEC15_Klt25_H60` | 0.375 | 0.624 | 0.499 | PASS | PASS | -0.273 |
| `AUT_OCT15_NOV30_Klt25_H40` | 0.372 | 0.606 | 0.468 | PASS | PASS | -0.276 |
| `AUT_OCT15_NOV30_Klt25_H60` | 0.372 | 0.606 | 0.468 | PASS | PASS | -0.276 |
| `AUT_OCT20_DEC10_Klt20_H20` | 0.351 | 0.592 | 0.483 | PASS | PASS | -0.297 |
| `AUT_OCT15_NOV30_Klt20_H40` | 0.344 | 0.582 | 0.476 | PASS | PASS | -0.303 |

## Verdict

Best autumn `AUT_OCT20_DEC10_Klt20_H40` held-out=+0.428 tip_clean=True · vs KD_OPT Δ=-0.220. KD_OPT held-out=+0.647. No tip/held-out lift vs KD_OPT → STOP. Soft-Frozen KEEP · live KD_OPT untouched.

## Hard rules

- Soft-Frozen KEEP · no live wire · no cutover from this search
- Dual-season follow-up: `FIN_KD_AUTUMN_DUAL_SEASON.md`

Repro: `repro/fin-post-exdiv-autumn-optimize-20260909/`
