# Stage-11 E45-C1 Monte Carlo / Governance Package

Locked challengers only (C4, S9A1, S10R3). **No retune. No new search. Not an E45 in-place edit.**

MC: 5000 block-21 path draws. Probabilities = P(challenger beats C4).

## Governance label: `GOVERNANCE_REVIEW_READY_NO_AUTO_PROMOTE`

Suggested mixed overlay for review: **S9A1**

### OOF_2011_2018

| kind | CAGR | MDD | Util | Boot | Turn | StressEx |
|---|---:|---:|---:|---:|---:|---:|
| C4 | 9.20% | -30.24% | -0.0592 | 0.7030 | 1.90% | 0.00019789917649721262 |
| S9A1 | 9.63% | -30.24% | -0.0549 | 0.7370 | 1.82% | 0.0003207064491405518 |
| S10R3 | 7.22% | -30.24% | -0.0790 | 0.5292 | 2.33% | 0.00020133150924938237 |

| vs C4 MC | P(better MDD) | P(better util) | P(better stress mean) | P(better stress compound) |
|---|---:|---:|---:|---:|
| S9A1 | 0.610 | 0.688 | 0.694 | 0.699 |
| S10R3 | 0.216 | 0.032 | 0.518 | 0.491 |

### VAL_2019_2022

| kind | CAGR | MDD | Util | Boot | Turn | StressEx |
|---|---:|---:|---:|---:|---:|---:|
| C4 | 21.65% | -31.87% | 0.0572 | 0.5588 | 2.19% | 0.0003472895953742069 |
| S9A1 | 23.45% | -29.79% | 0.0855 | 0.6232 | 2.38% | 0.0007770435301989302 |
| S10R3 | 22.02% | -33.30% | 0.0537 | 0.5874 | 2.62% | 0.0008225335198517046 |

| vs C4 MC | P(better MDD) | P(better util) | P(better stress mean) | P(better stress compound) |
|---|---:|---:|---:|---:|
| S9A1 | 0.726 | 0.657 | 0.944 | 0.950 |
| S10R3 | 0.285 | 0.498 | 0.726 | 0.719 |

### SEALED_2023_LATEST

| kind | CAGR | MDD | Util | Boot | Turn | StressEx |
|---|---:|---:|---:|---:|---:|---:|
| C4 | 47.68% | -20.99% | 0.3718 | 0.9984 | 1.19% | 0.001556890645892672 |
| S9A1 | 59.00% | -25.01% | 0.4650 | 1.0000 | 1.38% | 0.001094896017991568 |
| S10R3 | 38.49% | -29.82% | 0.2358 | 0.9760 | 1.91% | -0.0003546645881716979 |

| vs C4 MC | P(better MDD) | P(better util) | P(better stress mean) | P(better stress compound) |
|---|---:|---:|---:|---:|
| S9A1 | 0.154 | 0.886 | 0.145 | 0.132 |
| S10R3 | 0.032 | 0.039 | 0.000 | 0.000 |

## Decision options for humans

1. Keep C4-only as research reference; leave overlays EXPERIMENTAL
2. Accept a MIXED overlay (S9A1 or S10R3) for paper/monitoring only — **not** frozen promotion
3. Require a new information set before further challengers

Artifact: `reports/stage11_e45c1_monte_carlo_summary.json`
