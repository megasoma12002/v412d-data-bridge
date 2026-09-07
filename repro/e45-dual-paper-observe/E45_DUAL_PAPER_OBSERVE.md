# E45 Dual-Paper Observe Sleeve

Generated: `2026-09-07T17:02:43.335467+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`); live stitch **FORBIDDEN**.

## Locked paper books

- **BASE_E16_E18_E22_v2s**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books
- **CHAL_E45_E3**: same stack + E45 `E3_VOLTARGET_WINNER` exposure overlay
- Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** (do not cite)
- Primary comparable MDD: E1.1 val **-15.81%** (dated lineage)

## Dual paper metrics

| Book | Window | CAGR | MDD | n_days | Exact T+1 |
|---|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | full | 14.21% | -23.37% | 3352 | True |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 9.00% | -17.40% | 1495 | True |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 12.88% | -23.37% | 977 | True |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 25.68% | -15.09% | 880 | True |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 18.89% | -23.37% | 1857 | True |
| CHAL_E45_E3 | full | 10.92% | -20.84% | 3352 | True |
| CHAL_E45_E3 | oof_2011_2018 | 8.88% | -15.94% | 1495 | True |
| CHAL_E45_E3 | validation_2019_2022 | 10.14% | -20.84% | 977 | True |
| CHAL_E45_E3 | sealed_2023_plus | 15.81% | -9.59% | 880 | True |
| CHAL_E45_E3 | heldout_2019_plus | 12.82% | -20.84% | 1857 | True |

Held-out vs BASE: MDD improve **2.53 pp**; CAGR giveback **6.07 pp**.
Sealed vs BASE: MDD improve **5.49 pp**; CAGR giveback **9.87 pp**.

## Ops checklist

1. Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR
2. Run BASE + CHAL_E45_E3 paper ledgers in parallel with month-end monitor
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

`E45_DUAL_PAPER_OBSERVE_SLEEVE`

Artifacts:
- `/workspace/repro/e45-dual-paper-observe/reports/e45_dual_paper_observe.json`
- `/workspace/repro/e45-dual-paper-observe/outputs/dual_paper_nav_compare.csv`
