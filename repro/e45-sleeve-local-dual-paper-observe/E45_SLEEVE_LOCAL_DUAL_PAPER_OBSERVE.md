# E45 Sleeve-Local FIN_ONLY α=0.10 Dual-Paper Observe Sleeve

Generated: `2026-09-06T03:38:39.710365+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged**; live stitch **FORBIDDEN**.

## Locked paper books

- **BASE_E16_E18_E22_v2s**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books
- **SLEEVE_FIN_ONLY_A10**: same stack + α=0.10 × E45 `E3_VOLTARGET_WINNER` on sleeves `Financial` only
- Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** (do not cite)

## Dual paper metrics

| Book | Window | CAGR | MDD | n_days | Exact T+1 |
|---|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | full | 13.79% | -22.54% | 3351 | True |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 8.89% | -17.55% | 1495 | True |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 12.30% | -22.54% | 977 | True |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 24.89% | -14.09% | 879 | True |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 18.20% | -22.54% | 1856 | True |
| SLEEVE_FIN_ONLY_A10 | full | 13.23% | -21.63% | 3351 | True |
| SLEEVE_FIN_ONLY_A10 | oof_2011_2018 | 9.11% | -17.31% | 1495 | True |
| SLEEVE_FIN_ONLY_A10 | validation_2019_2022 | 11.51% | -21.63% | 977 | True |
| SLEEVE_FIN_ONLY_A10 | sealed_2023_plus | 23.09% | -10.67% | 879 | True |
| SLEEVE_FIN_ONLY_A10 | heldout_2019_plus | 16.95% | -21.63% | 1856 | True |

Held-out vs BASE: MDD improve **0.91 pp**; CAGR giveback **1.25 pp**; score **0.285**.
Sealed vs BASE: MDD improve **3.42 pp**; CAGR giveback **1.80 pp**; score **2.518**.

## Ops checklist

1. Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR
2. Run BASE + SLEEVE_FIN_ONLY_A10 paper ledgers in parallel with month-end monitor
3. Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)
4. Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history
5. Observe sleeve ≠ stitch license; second human stitch ACCEPT still required
6. Never cite the retired handoff MDD narrative; use dated lineage / challenger MDDs only
7. Leave FULL + A25 + A05 observe sleeves operating in parallel

## Explicit non-goals

- Auto live-wire / four-layer stitch from this observe sleeve
- Soft-Frozen clip flip
- DEFAULT books flip away from E22_v2s_tw
- Invent replacement for retired MDD narrative
- Retire FULL / A25 / A05 observe without separate ballot

## Label

`E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE_SLEEVE`

## Reproduce

```bash
python3 scripts/e45_sleeve_local_dual_paper_ledgers.py
```
