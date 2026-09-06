# E45 PAPER Sleeve-Local Overlay

Generated: `2026-09-06T01:46:50.033044+00:00`
Status: **PAPER ONLY** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**; observe unchanged.

High-β sleeves (β≥median vs TAIEX): **0050, Financial**

## Held-out deltas vs BASE

| Book | Scope | α | Sleeves | MDD Δpp | Giveback pp | Score |
|---|---|---:|---|---:|---:|---:|
| FIN0050_A05 | FIN_0050 | 0.05 | Financial,0050 | +0.80 | +0.91 | +0.34 |
| HIGHBETA_A05 | HIGH_BETA | 0.05 | 0050,Financial | +0.80 | +0.91 | +0.34 |
| FIN_A05 | FIN_ONLY | 0.05 | Financial | +0.75 | +0.82 | +0.34 |
| ALL_A05 | ALL | 0.05 |  | +0.85 | +1.07 | +0.32 |
| FIN_A25 | FIN_ONLY | 0.25 | Financial | +0.66 | +2.55 | -0.61 |
| FIN0050_A25 | FIN_0050 | 0.25 | Financial,0050 | +0.63 | +2.66 | -0.70 |
| HIGHBETA_A25 | HIGH_BETA | 0.25 | 0050,Financial | +0.63 | +2.66 | -0.70 |
| FIN_FULL | FIN_ONLY | 1.00 | Financial | +1.84 | +5.22 | -0.77 |
| ALL_A25 | ALL | 0.25 |  | +0.63 | +2.83 | -0.78 |
| ALL_FULL | ALL | 1.00 |  | +1.88 | +5.65 | -0.94 |

## Sealed deltas vs BASE

| Book | Scope | α | MDD Δpp | Giveback pp | Score |
|---|---|---:|---:|---:|---:|
| FIN_A25 | FIN_ONLY | 0.25 | +5.15 | +3.85 | +3.22 |
| FIN0050_A25 | FIN_0050 | 0.25 | +5.14 | +4.01 | +3.13 |
| HIGHBETA_A25 | HIGH_BETA | 0.25 | +5.14 | +4.01 | +3.13 |
| ALL_A25 | ALL | 0.25 | +5.13 | +4.36 | +2.94 |
| ALL_A05 | ALL | 0.05 | +3.07 | +1.50 | +2.32 |
| FIN0050_A05 | FIN_0050 | 0.05 | +2.67 | +1.28 | +2.03 |
| HIGHBETA_A05 | HIGH_BETA | 0.05 | +2.67 | +1.28 | +2.03 |
| FIN_A05 | FIN_ONLY | 0.05 | +2.50 | +1.16 | +1.92 |
| FIN_FULL | FIN_ONLY | 1.00 | +5.06 | +8.99 | +0.57 |
| ALL_FULL | ALL | 1.00 | +4.90 | +9.40 | +0.19 |

## Read-through (paper)

1. Held-out preferred: **`FIN0050_A05`** (scope=FIN_0050, α=0.05).
2. **FIN_A05 beats ALL_A05** on held-out score (0.342 vs 0.320) — localizing cut can reduce CAGR tax.
3. Does **not** open observe / authorize stitch.

## Governance

- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED

## Reproduce

```bash
python3 scripts/e45_sleeve_local_paper.py
```

