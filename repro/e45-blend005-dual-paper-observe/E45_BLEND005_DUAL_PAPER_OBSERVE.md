# E45 Blend-α=0.05 Dual-Paper Observe Sleeve

Generated: `2026-09-09T12:52:37.211516+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`); live stitch **FORBIDDEN**.

## Locked paper books

- **BASE_E16_E18_E22_v2s**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books
- **BLEND_E45_A05**: same stack + α=0.05 × E45 `E3_VOLTARGET_WINNER` exposure overlay
- Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** (do not cite)
- Primary comparable MDD: E1.1 val **-15.81%** (dated lineage)

## Dual paper metrics

| Book | Window | CAGR | MDD | n_days | Exact T+1 |
|---|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | full | 13.97% | -22.39% | 3353 | True |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 8.98% | -17.57% | 1495 | True |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 12.24% | -22.39% | 977 | True |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 25.55% | -13.97% | 881 | True |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 18.47% | -22.39% | 1858 | True |
| BLEND_E45_A05 | full | 13.56% | -21.75% | 3353 | True |
| BLEND_E45_A05 | oof_2011_2018 | 9.08% | -17.49% | 1495 | True |
| BLEND_E45_A05 | validation_2019_2022 | 11.72% | -21.75% | 977 | True |
| BLEND_E45_A05 | sealed_2023_plus | 24.23% | -11.22% | 881 | True |
| BLEND_E45_A05 | heldout_2019_plus | 17.59% | -21.75% | 1858 | True |

Held-out vs BASE: MDD improve **0.64 pp**; CAGR giveback **0.88 pp**.
Sealed vs BASE: MDD improve **2.75 pp**; CAGR giveback **1.32 pp**.

## Ops checklist

1. Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR
2. Run BASE + BLEND_E45_A05 paper ledgers in parallel with month-end monitor
3. Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)
4. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
5. Observe sleeve ≠ stitch license; second human stitch ACCEPT still required
6. Never cite the retired handoff MDD narrative; use dated lineage / challenger MDDs only

## Explicit non-goals

- Auto live-wire / four-layer stitch from this observe sleeve
- Soft-Frozen clip flip
- DEFAULT books flip away from E22_v2s_tw
- Invent replacement for retired MDD narrative
- Bundle FIN50 / L4 / BLEND / odd-lot / tax DEFAULT promote

## Label

`E45_BLEND005_DUAL_PAPER_OBSERVE_SLEEVE`

Artifacts:
- `/workspace/repro/e45-blend005-dual-paper-observe/reports/e45_blend005_dual_paper_observe.json`
- `/workspace/repro/e45-blend005-dual-paper-observe/outputs/dual_paper_nav_compare.csv`
