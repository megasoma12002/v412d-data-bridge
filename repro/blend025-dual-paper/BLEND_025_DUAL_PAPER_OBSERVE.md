# BLEND_025 Dual-Paper Observe Sleeve

Generated: `2026-09-07T17:20:22.030903+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).

## Locked challenger

- **BLEND_025**: α=0.25·FIN_CAP_50([0.35,0.50]) + 0.75·Soft-Frozen BASE, renormalized
- Regime router / Exact T+1 / E22_v2s unchanged vs live E16

## Dual paper metrics

| Book | Window | CAGR | MDD | Fin mean | Fin max | Exact T+1 |
|---|---|---:|---:|---:|---:|---|
| BASE_E16 | full | 13.43% | -22.07% | 71.7% | 80.0% | True |
| BASE_E16 | oof_2011_2018 | 8.78% | -17.12% | 72.2% | 80.0% | True |
| BASE_E16 | validation_2019_2022 | 11.55% | -22.07% | 71.0% | 76.9% | True |
| BASE_E16 | sealed_2023_plus | 24.41% | -12.04% | 71.5% | 76.9% | True |
| BASE_E16 | heldout_2019_plus | 17.57% | -22.07% | 71.2% | 76.9% | True |
| BLEND_025 | full | 13.44% | -21.29% | 66.3% | 72.5% | True |
| BLEND_025 | oof_2011_2018 | 8.91% | -15.98% | 66.7% | 72.5% | True |
| BLEND_025 | validation_2019_2022 | 11.60% | -21.29% | 65.8% | 70.2% | True |
| BLEND_025 | sealed_2023_plus | 24.21% | -11.18% | 66.1% | 70.2% | True |
| BLEND_025 | heldout_2019_plus | 17.50% | -21.29% | 65.9% | 70.2% | True |

Held-out vs BASE: MDD improve **0.78 pp**; CAGR giveback **0.07 pp**.
Sealed vs BASE: MDD improve **0.87 pp**; CAGR giveback **0.20 pp**.

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
