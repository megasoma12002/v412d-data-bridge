# BLEND_025 Dual-Paper Observe Sleeve

Generated: `2026-09-07T15:50:14.744114+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

## Locked challenger

- **BLEND_025**: α=0.25·FIN_CAP_50([0.35,0.50]) + 0.75·Soft-Frozen BASE, renormalized
- Regime router / Exact T+1 / E22_v2s unchanged vs live E16

## Dual paper metrics

| Book | Window | CAGR | MDD | Fin mean | Fin max | Exact T+1 |
|---|---|---:|---:|---:|---:|---|
| BASE_E16 | full | 13.78% | -22.39% | 79.9% | 91.9% | True |
| BASE_E16 | oof_2011_2018 | 9.46% | -16.49% | 80.3% | 91.1% | True |
| BASE_E16 | validation_2019_2022 | 11.18% | -22.39% | 80.0% | 91.9% | True |
| BASE_E16 | sealed_2023_plus | 25.20% | -12.85% | 79.0% | 88.7% | True |
| BASE_E16 | heldout_2019_plus | 17.72% | -22.39% | 79.5% | 91.9% | True |
| BLEND_025 | full | 13.92% | -21.55% | 72.4% | 81.5% | True |
| BLEND_025 | oof_2011_2018 | 9.21% | -16.04% | 72.7% | 80.8% | True |
| BLEND_025 | validation_2019_2022 | 12.06% | -21.55% | 72.5% | 81.5% | True |
| BLEND_025 | sealed_2023_plus | 25.18% | -10.55% | 71.7% | 79.0% | True |
| BLEND_025 | heldout_2019_plus | 18.19% | -21.55% | 72.2% | 81.5% | True |

Held-out vs BASE: MDD improve **0.83 pp**; CAGR giveback **-0.47 pp**.
Sealed vs BASE: MDD improve **2.31 pp**; CAGR giveback **0.02 pp**.

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
