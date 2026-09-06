# E45 FIN_ONLY densify thicken (around observe lock a=0.10)

Generated: `2026-09-06T06:00:44.136340+00:00`
Status: **PAPER ONLY** — observe lock unchanged unless densify clearly flips
Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA remains DRAFT

## Held-out ranking (score = MDD improve - 0.5*|CAGR giveback|)

| Book | a | Scope | MDD improve pp | CAGR giveback pp | Score | Ann. turnover |
|---|---:|---|---:|---:|---:|---:|
| `FIN_ONLY_A10` | 0.10 | Financial | +0.91 | +1.25 | +0.29 | 1.13 |
| `FIN_ONLY_A05` | 0.05 | Financial | +0.64 | +0.76 | +0.26 | 1.11 |
| `BLEND_E45_A05` | 0.05 | ALL | +0.70 | +0.96 | +0.22 | 1.12 |
| `FIN_ONLY_A08` | 0.08 | Financial | +0.76 | +1.15 | +0.19 | 1.12 |
| `FIN_ONLY_A12` | 0.12 | Financial | +0.83 | +1.43 | +0.11 | 1.15 |
| `BLEND_E45_A10` | 0.10 | ALL | +0.80 | +1.51 | +0.04 | 1.13 |
| `FIN_ONLY_A15` | 0.15 | Financial | +0.74 | +1.73 | -0.12 | 1.15 |

**Held-out preferred (all candidates):** `FIN_ONLY_A10`
**Held-out preferred among FIN_ONLY densify:** `FIN_ONLY_A10`
**Observe lock `FIN_ONLY_A10` still preferred among FIN densify?** **YES**

## COVID-year-excluded held-out (2019+ minus all 2020 days)

Removes the COVID mega-DD year from the held-out path so sleeve-local edge is not COVID-only.

| Book | MDD improve pp | CAGR giveback pp | Score | n_days |
|---|---:|---:|---:|---:|
| `FIN_ONLY_A05` | -1.33 | +0.90 | -1.78 | 1611 |
| `BLEND_E45_A05` | -1.49 | +1.13 | -2.05 | 1611 |
| `FIN_ONLY_A08` | -1.70 | +1.35 | -2.38 | 1611 |
| `FIN_ONLY_A10` | -1.67 | +1.48 | -2.41 | 1611 |
| `FIN_ONLY_A12` | -1.63 | +1.69 | -2.47 | 1611 |
| `BLEND_E45_A10` | -1.70 | +1.78 | -2.59 | 1611 |
| `FIN_ONLY_A15` | -1.68 | +2.04 | -2.70 | 1611 |

## Rolling 3y tip window (end 2026-09-04)

Latest rolling-3y winner vs BASE: **`FIN_ONLY_A15`**

| Book | MDD improve pp | CAGR giveback pp | Score |
|---|---:|---:|---:|
| `FIN_ONLY_A15` | +3.91 | +2.46 | +2.68 |
| `BLEND_E45_A10` | +3.65 | +2.12 | +2.60 |
| `FIN_ONLY_A12` | +3.59 | +2.03 | +2.58 |
| `FIN_ONLY_A10` | +3.42 | +1.80 | +2.52 |
| `FIN_ONLY_A08` | +3.18 | +1.68 | +2.34 |
| `BLEND_E45_A05` | +2.78 | +1.42 | +2.07 |
| `FIN_ONLY_A05` | +2.36 | +1.14 | +1.79 |

## Cost stress (1-3x) @ heldout_2019_plus

| Book | Cost | MDD improve pp | CAGR giveback pp | Score | Ann. turnover |
|---|---:|---:|---:|---:|---:|
| `BLEND_E45_A05` | 1x | +0.70 | +0.96 | +0.22 | 1.12 |
| `BLEND_E45_A05_C2x` | 2x | +0.74 | +0.97 | +0.25 | 1.11 |
| `BLEND_E45_A05_C3x` | 3x | +0.76 | +0.99 | +0.26 | 1.11 |
| `FIN_ONLY_A08` | 1x | +0.76 | +1.15 | +0.19 | 1.12 |
| `FIN_ONLY_A08_C2x` | 2x | +0.84 | +1.17 | +0.26 | 1.12 |
| `FIN_ONLY_A08_C3x` | 3x | +0.92 | +1.23 | +0.30 | 1.12 |
| `FIN_ONLY_A10` | 1x | +0.91 | +1.25 | +0.29 | 1.13 |
| `FIN_ONLY_A10_C2x` | 2x | +0.96 | +1.29 | +0.32 | 1.13 |
| `FIN_ONLY_A10_C3x` | 3x | +1.03 | +1.34 | +0.37 | 1.13 |
| `FIN_ONLY_A12` | 1x | +0.83 | +1.43 | +0.11 | 1.15 |
| `FIN_ONLY_A12_C2x` | 2x | +0.90 | +1.48 | +0.16 | 1.14 |
| `FIN_ONLY_A12_C3x` | 3x | +1.02 | +1.52 | +0.26 | 1.14 |

## Verdict

- Thicken densify around FIN_ONLY a in {0.05,0.08,0.10,0.12,0.15} + cost 1-3x + COVID-year-excluded held-out.
- Observe sleeve stays **`SLEEVE_FIN_ONLY_A10`** unless a dedicated ballot flips it (this paper does not).
- Pair with COVID-framed multi-event report: COVID help is expected; non-COVID multi-event remains the hard gate.

Label: `E45_FINA10_THICKEN_2026-09-06__STITCH_FORBIDDEN`
