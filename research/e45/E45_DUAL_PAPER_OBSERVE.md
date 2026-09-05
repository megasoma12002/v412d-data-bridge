# E45 Dual-Paper Observe Sleeve

Generated: `2026-09-05T18:45:09.411488+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`); live stitch **FORBIDDEN**.

## Locked paper books

- **BASE_E16_E18_E22_v2s**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books
- **CHAL_E45_E3**: same stack + E45 `E3_VOLTARGET_WINNER` exposure overlay
- Claimed −13.16%: **`RETIRED_HISTORICAL_NARRATIVE`** (do not cite)
- Primary comparable MDD: E1.1 val **-15.81%** (dated lineage)

## Dual paper metrics

| Book | Window | CAGR | MDD | n_days | Exact T+1 |
|---|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | full | 13.78% | -22.64% | 3351 | True |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 8.85% | -17.41% | 1495 | True |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 12.33% | -22.64% | 977 | True |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 24.93% | -14.46% | 879 | True |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 18.23% | -22.64% | 1856 | True |
| CHAL_E45_E3 | full | 10.79% | -20.76% | 3351 | True |
| CHAL_E45_E3 | oof_2011_2018 | 8.91% | -15.57% | 1495 | True |
| CHAL_E45_E3 | validation_2019_2022 | 9.97% | -20.76% | 977 | True |
| CHAL_E45_E3 | sealed_2023_plus | 15.52% | -9.56% | 879 | True |
| CHAL_E45_E3 | heldout_2019_plus | 12.59% | -20.76% | 1856 | True |

Held-out vs BASE: MDD improve **1.88 pp**; CAGR giveback **5.65 pp**.
Sealed vs BASE: MDD improve **4.90 pp**; CAGR giveback **9.40 pp**.

## Ops checklist

1. Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR
2. Run BASE + CHAL_E45_E3 paper ledgers in parallel with month-end monitor
3. Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)
4. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
5. Observe sleeve ≠ stitch license; second human stitch ACCEPT still required
6. Never cite −13.16%; use dated lineage / challenger MDDs only

## Explicit non-goals

- Auto live-wire / four-layer stitch from this observe sleeve
- Soft-Frozen clip flip
- DEFAULT books flip away from E22_v2s_tw
- Invent a replacement for retired −13.16% narrative
- Bundle FIN50 / L4 / BLEND / odd-lot / tax DEFAULT promote

## Label

`E45_DUAL_PAPER_OBSERVE_SLEEVE`

Artifacts:
- `/workspace/repro/e45-dual-paper-observe/reports/e45_dual_paper_observe.json`
- `/workspace/repro/e45-dual-paper-observe/outputs/dual_paper_nav_compare.csv`
