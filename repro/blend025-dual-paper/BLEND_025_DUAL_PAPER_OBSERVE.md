# BLEND_025 Dual-Paper Observe Sleeve

Generated: `2026-09-09T12:45:05.030251+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

## Locked challenger

- **BLEND_025**: α=0.25·FIN_CAP_50([0.35,0.50]) + 0.75·Soft-Frozen BASE, renormalized
- Regime router / Exact T+1 / E22_v2s unchanged vs live E16

## Dual paper metrics

| Book | Window | CAGR | MDD | Fin mean | Fin max | Exact T+1 |
|---|---|---:|---:|---:|---:|---|
| BASE_E16 | full | 13.97% | -22.39% | 79.8% | 89.4% | True |
| BASE_E16 | oof_2011_2018 | 8.98% | -17.57% | 80.3% | 88.8% | True |
| BASE_E16 | validation_2019_2022 | 12.25% | -22.39% | 79.7% | 89.4% | True |
| BASE_E16 | sealed_2023_plus | 25.54% | -13.95% | 79.1% | 87.9% | True |
| BASE_E16 | heldout_2019_plus | 18.47% | -22.39% | 79.4% | 89.4% | True |
| BLEND_025 | full | 13.94% | -21.68% | 72.4% | 79.5% | True |
| BLEND_025 | oof_2011_2018 | 8.93% | -16.04% | 72.7% | 79.1% | True |
| BLEND_025 | validation_2019_2022 | 12.57% | -21.68% | 72.3% | 79.5% | True |
| BLEND_025 | sealed_2023_plus | 25.13% | -11.94% | 71.8% | 78.4% | True |
| BLEND_025 | heldout_2019_plus | 18.46% | -21.68% | 72.1% | 79.5% | True |

Held-out vs BASE: MDD improve **0.71 pp**; CAGR giveback **0.01 pp**.
Sealed vs BASE: MDD improve **2.01 pp**; CAGR giveback **0.41 pp**.

## Ops checklist

1. Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR
2. Run BLEND_025 dual paper ledgers in parallel with month-end monitor
3. Re-check charter trailing gates (ytd / trailing_1y) each month-end
4. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
5. Observe sleeve ≠ cutover license; FIN50/L4 cutover stays FROZEN

## Explicit non-goals

- Auto live-wire from this observe sleeve
- Retune FIN_CAP_50 lock [0.35,0.50]
- Retune Soft-Frozen [0.50,0.95]
- Close or replace FIN50 / L4 dual-paper sleeves
- Claim CAGR≥20% / MDD≤15% as live results

## Label

`BLEND_025_DUAL_PAPER_OBSERVE_SLEEVE`

Artifacts:
- `/workspace/repro/blend025-dual-paper/reports/blend025_dual_paper_observe.json`
- `/workspace/repro/blend025-dual-paper/outputs/dual_paper_nav_compare.csv`
