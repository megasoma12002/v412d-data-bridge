# E45 PAPER Sleeve-Local Overlay

Generated: `2026-09-06T04:33:31.559104+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**; observe unchanged.

High-β sleeves (β≥median vs TAIEX): **0050, Financial**

## Held-out deltas vs BASE

| Book | Scope | α | Sleeves | MDD Δpp | Giveback pp | Score |
|---|---|---:|---|---:|---:|---:|
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | Financial | +0.64 | +0.76 | +0.26 |
| FIN_0050_A05 | FIN_0050 | 0.05 | Financial,0050 | +0.66 | +0.85 | +0.23 |
| HIGH_BETA_A05 | HIGH_BETA | 0.05 | 0050,Financial | +0.66 | +0.85 | +0.23 |
| BLEND_E45_A05 | ALL | 0.05 |  | +0.70 | +0.96 | +0.22 |
| FIN_ONLY_A25 | FIN_ONLY | 0.25 | Financial | +0.45 | +2.46 | -0.77 |
| FIN_0050_A25 | FIN_0050 | 0.25 | Financial,0050 | +0.44 | +2.55 | -0.84 |
| HIGH_BETA_A25 | HIGH_BETA | 0.25 | 0050,Financial | +0.44 | +2.55 | -0.84 |
| FIN_ONLY_FULL | FIN_ONLY | 1.00 | Financial | +1.67 | +5.14 | -0.90 |
| BLEND_E45_A25 | ALL | 0.25 |  | +0.45 | +2.72 | -0.91 |
| CHAL_E45_E3 | ALL | 1.00 |  | +1.71 | +5.41 | -1.00 |

## Sealed deltas vs BASE

| Book | Scope | α | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|
| FIN_ONLY_A25 | FIN_ONLY | 0.25 | +4.77 | +3.84 | +2.85 |
| FIN_0050_A25 | FIN_0050 | 0.25 | +4.77 | +3.95 | +2.79 |
| HIGH_BETA_A25 | HIGH_BETA | 0.25 | +4.77 | +3.95 | +2.79 |
| BLEND_E45_A25 | ALL | 0.25 | +4.75 | +4.32 | +2.59 |
| BLEND_E45_A05 | ALL | 0.05 | +2.78 | +1.42 | +2.07 |
| FIN_0050_A05 | FIN_0050 | 0.05 | +2.58 | +1.27 | +1.95 |
| HIGH_BETA_A05 | HIGH_BETA | 0.05 | +2.58 | +1.27 | +1.95 |
| FIN_ONLY_A05 | FIN_ONLY | 0.05 | +2.36 | +1.14 | +1.79 |
| FIN_ONLY_FULL | FIN_ONLY | 1.00 | +4.67 | +8.96 | +0.19 |
| CHAL_E45_E3 | ALL | 1.00 | +4.54 | +9.03 | +0.03 |

## Read-through (paper)

1. Held-out preferred: **`FIN_ONLY_A05`** (scope=FIN_ONLY, α=0.05).
2. **FIN_ONLY_A05 beats BLEND_E45_A05** on held-out score (0.261 vs 0.222) — localizing cut can reduce CAGR tax.
3. Does **not** open observe / authorize stitch.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED

## Reproduce

```bash
python3 scripts/e45_sleeve_local_paper.py
```

