# E45 Sleeve-Local FIN_ONLY α=0.10 Dual-Paper Observe Sleeve

Generated: `2026-09-09T12:45:13.511339+00:00`
Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged**; live stitch **FORBIDDEN**.

## Locked paper books

- **BASE_E16_E18_E22_v2s**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books
- **SLEEVE_FIN_ONLY_A10**: same stack + α=0.10 × E45 `E3_VOLTARGET_WINNER` on sleeves `Financial` only
- Retired MDD narrative: **`RETIRED_HISTORICAL_NARRATIVE`** (do not cite)

## Dual paper metrics

| Book | Window | CAGR | MDD | n_days | Exact T+1 |
|---|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | full | 13.97% | -22.39% | 3353 | True |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 8.98% | -17.57% | 1495 | True |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 12.24% | -22.39% | 977 | True |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 25.55% | -13.97% | 881 | True |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 18.47% | -22.39% | 1858 | True |
| SLEEVE_FIN_ONLY_A10 | full | 13.37% | -21.69% | 3353 | True |
| SLEEVE_FIN_ONLY_A10 | oof_2011_2018 | 9.12% | -17.32% | 1495 | True |
| SLEEVE_FIN_ONLY_A10 | validation_2019_2022 | 11.40% | -21.69% | 977 | True |
| SLEEVE_FIN_ONLY_A10 | sealed_2023_plus | 23.78% | -10.62% | 881 | True |
| SLEEVE_FIN_ONLY_A10 | heldout_2019_plus | 17.20% | -21.69% | 1858 | True |

Held-out vs BASE: MDD improve **0.70 pp**; CAGR giveback **1.26 pp**; score **0.065**.
Sealed vs BASE: MDD improve **3.35 pp**; CAGR giveback **1.77 pp**; score **2.460**.

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
