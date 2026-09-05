# BLEND_025 Dual-Paper Observe Sleeve

Generated: `2026-09-05T08:08:50.045133+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

## Locked challenger

- **BLEND_025**: α=0.25·FIN_CAP_50([0.35,0.50]) + 0.75·Soft-Frozen BASE, renormalized
- Regime router / Exact T+1 / E22_v2s unchanged vs live E16

## Dual paper metrics

| Book | Window | CAGR | MDD | Fin mean | Fin max | Exact T+1 |
|---|---|---:|---:|---:|---:|---|
| BASE_E16 | full | 13.78% | -22.64% | 79.8% | 91.9% | True |
| BASE_E16 | oof_2011_2018 | 8.85% | -17.41% | 80.2% | 91.1% | True |
| BASE_E16 | validation_2019_2022 | 12.33% | -22.64% | 79.9% | 91.9% | True |
| BASE_E16 | sealed_2023_plus | 24.93% | -14.46% | 78.9% | 88.5% | True |
| BASE_E16 | heldout_2019_plus | 18.24% | -22.64% | 79.4% | 91.9% | True |
| BLEND_025 | full | 13.69% | -21.82% | 72.4% | 81.5% | True |
| BLEND_025 | oof_2011_2018 | 8.81% | -16.04% | 72.7% | 80.8% | True |
| BLEND_025 | validation_2019_2022 | 12.53% | -21.82% | 72.4% | 81.5% | True |
| BLEND_025 | sealed_2023_plus | 24.42% | -12.34% | 71.7% | 78.9% | True |
| BLEND_025 | heldout_2019_plus | 18.11% | -21.82% | 72.1% | 81.5% | True |

Held-out vs BASE: MDD improve **0.82 pp**; CAGR giveback **0.12 pp**.
Sealed vs BASE: MDD improve **2.11 pp**; CAGR giveback **0.51 pp**.

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
