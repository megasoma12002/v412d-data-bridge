# E45 PAPER Sleeve-Local Deep-Dive

Generated: `2026-09-06T02:47:38.341136+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**; does **not** auto-OPEN observe.

High-beta sleeves (beta>=median vs TAIEX): **0050, Financial**
Grid: alpha in {0.05, 0.08, 0.1} · cost in {1x, 2x} · scopes ALL / FIN_ONLY / FIN_0050 / HIGH_BETA

## Held-out deltas vs BASE @ 1x cost

| Book | Scope | alpha | MDD dpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|
| FIN_ONLY_A10_C1x | FIN_ONLY | 0.10 | +0.91 | +1.25 | +0.29 |
| FIN_ONLY_A05_C1x | FIN_ONLY | 0.05 | +0.64 | +0.76 | +0.26 |
| FIN_0050_A05_C1x | FIN_0050 | 0.05 | +0.66 | +0.85 | +0.23 |
| HIGH_BETA_A05_C1x | HIGH_BETA | 0.05 | +0.66 | +0.85 | +0.23 |
| ALL_A05_C1x | ALL | 0.05 | +0.70 | +0.96 | +0.22 |
| FIN_0050_A08_C1x | FIN_0050 | 0.08 | +0.80 | +1.17 | +0.21 |
| HIGH_BETA_A08_C1x | HIGH_BETA | 0.08 | +0.80 | +1.17 | +0.21 |
| ALL_A08_C1x | ALL | 0.08 | +0.82 | +1.22 | +0.20 |
| HIGH_BETA_A10_C1x | HIGH_BETA | 0.10 | +0.87 | +1.34 | +0.20 |
| FIN_0050_A10_C1x | FIN_0050 | 0.10 | +0.87 | +1.34 | +0.20 |
| FIN_ONLY_A08_C1x | FIN_ONLY | 0.08 | +0.76 | +1.15 | +0.19 |
| ALL_A10_C1x | ALL | 0.10 | +0.80 | +1.51 | +0.04 |

## Held-out deltas vs BASE @ 2x cost

| Book | Scope | alpha | MDD dpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|
| FIN_ONLY_A10_C2x | FIN_ONLY | 0.10 | +0.96 | +1.29 | +0.32 |
| FIN_0050_A10_C2x | FIN_0050 | 0.10 | +0.96 | +1.35 | +0.28 |
| HIGH_BETA_A10_C2x | HIGH_BETA | 0.10 | +0.96 | +1.35 | +0.28 |
| FIN_ONLY_A08_C2x | FIN_ONLY | 0.08 | +0.84 | +1.17 | +0.26 |
| ALL_A08_C2x | ALL | 0.08 | +0.89 | +1.25 | +0.26 |
| FIN_ONLY_A05_C2x | FIN_ONLY | 0.05 | +0.65 | +0.80 | +0.25 |
| ALL_A05_C2x | ALL | 0.05 | +0.74 | +0.97 | +0.25 |
| HIGH_BETA_A05_C2x | HIGH_BETA | 0.05 | +0.67 | +0.85 | +0.25 |
| FIN_0050_A05_C2x | FIN_0050 | 0.05 | +0.67 | +0.85 | +0.25 |
| FIN_0050_A08_C2x | FIN_0050 | 0.08 | +0.82 | +1.20 | +0.21 |
| HIGH_BETA_A08_C2x | HIGH_BETA | 0.08 | +0.82 | +1.20 | +0.21 |
| ALL_A10_C2x | ALL | 0.10 | +0.88 | +1.53 | +0.12 |

## Sealed deltas vs BASE @ 1x cost

| Book | Scope | alpha | MDD dpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|
| ALL_A10_C1x | ALL | 0.10 | +3.65 | +2.12 | +2.60 |
| HIGH_BETA_A10_C1x | HIGH_BETA | 0.10 | +3.48 | +1.89 | +2.54 |
| FIN_0050_A10_C1x | FIN_0050 | 0.10 | +3.48 | +1.89 | +2.54 |
| FIN_ONLY_A10_C1x | FIN_ONLY | 0.10 | +3.42 | +1.80 | +2.52 |
| HIGH_BETA_A08_C1x | HIGH_BETA | 0.08 | +3.30 | +1.68 | +2.46 |
| FIN_0050_A08_C1x | FIN_0050 | 0.08 | +3.30 | +1.68 | +2.46 |
| ALL_A08_C1x | ALL | 0.08 | +3.30 | +1.72 | +2.44 |
| FIN_ONLY_A08_C1x | FIN_ONLY | 0.08 | +3.18 | +1.68 | +2.34 |
| ALL_A05_C1x | ALL | 0.05 | +2.78 | +1.42 | +2.07 |
| FIN_0050_A05_C1x | FIN_0050 | 0.05 | +2.58 | +1.27 | +1.95 |
| HIGH_BETA_A05_C1x | HIGH_BETA | 0.05 | +2.58 | +1.27 | +1.95 |
| FIN_ONLY_A05_C1x | FIN_ONLY | 0.05 | +2.36 | +1.14 | +1.79 |

## Crisis-year MDD improve vs BASE (selected books)

| Book | 2015 | 2018 | 2020 | 2022 |
|---|---:|---:|---:|---:|
| ALL_A05_C1x | -0.08 | +0.06 | +0.70 | -1.49 |
| FIN_0050_A05_C1x | -0.07 | +0.00 | +0.66 | -1.44 |
| FIN_ONLY_A05_C1x | -0.08 | -0.01 | +0.64 | -1.33 |
| FIN_ONLY_A10_C1x | -0.06 | +0.17 | +0.91 | -1.67 |
| HIGH_BETA_A05_C1x | -0.07 | +0.00 | +0.66 | -1.44 |

## Read-through (paper)

1. Held-out preferred @1x: **`FIN_ONLY_A10_C1x`** (scope=FIN_ONLY, alpha=0.1, score=0.285).
2. Preferred book's share of positive crisis-year MDD help in **2020**: **84.2%** (same concentration risk as whole-book A05).
3. Best sleeve-local (`FIN_ONLY_A10_C1x`, score 0.285) **beats** `ALL_A05_C1x` (0.222) — structure edge holds on denser grid.
4. Preferred twin @2x (`FIN_ONLY_A10_C2x`) score **0.319** (1x was 0.285) — cost stress check.
5. Does **not** open sleeve-local observe or authorize stitch from this memo.
6. Whole-book **blend-alpha=0.05 observe OPEN** is a separate ballot (`E45_BLEND005_OBSERVE_OPEN.md`).

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · the retired handoff MDD narrative `RETIRED_HISTORICAL_NARRATIVE`

## Reproduce

```bash
python3 scripts/e45_sleeve_local_deep_dive.py
```

