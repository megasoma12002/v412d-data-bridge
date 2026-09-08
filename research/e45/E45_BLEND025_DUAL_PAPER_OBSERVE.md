# E45 Blend-α=0.25 Dual-Paper Observe Sleeve

Generated: `2026-09-08T00:52:19.497338+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`); live stitch **FORBIDDEN**.

## Locked paper books

- **BASE_E16_E18_E22_v2s**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books
- **BLEND_E45_A25**: same stack + α=0.25 × E45 `E3_VOLTARGET_WINNER` exposure overlay
- Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** (do not cite)
- Primary comparable MDD: E1.1 val **-15.81%** (dated lineage)

## Dual paper metrics

| Book | Window | CAGR | MDD | n_days | Exact T+1 |
|---|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | full | 13.81% | -22.39% | 3352 | True |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 9.46% | -16.49% | 1495 | True |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 11.18% | -22.39% | 977 | True |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 25.33% | -13.04% | 880 | True |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 17.78% | -22.39% | 1857 | True |
| BLEND_E45_A25 | full | 13.31% | -21.98% | 3352 | True |
| BLEND_E45_A25 | oof_2011_2018 | 9.35% | -16.47% | 1495 | True |
| BLEND_E45_A25 | validation_2019_2022 | 11.39% | -21.98% | 977 | True |
| BLEND_E45_A25 | sealed_2023_plus | 23.13% | -10.71% | 880 | True |
| BLEND_E45_A25 | heldout_2019_plus | 16.91% | -21.98% | 1857 | True |

Held-out vs BASE: MDD improve **0.41 pp**; CAGR giveback **0.87 pp**.
Sealed vs BASE: MDD improve **2.33 pp**; CAGR giveback **2.21 pp**.

## Ops checklist

1. Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR
2. Run BASE + BLEND_E45_A25 paper ledgers in parallel with month-end monitor
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

`E45_BLEND025_DUAL_PAPER_OBSERVE_SLEEVE`

Artifacts:
- `/workspace/repro/e45-blend025-dual-paper-observe/reports/e45_blend025_dual_paper_observe.json`
- `/workspace/repro/e45-blend025-dual-paper-observe/outputs/dual_paper_nav_compare.csv`
