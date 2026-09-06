# E45 Dual-Paper Observe — Design Pack (Stage 3)

Generated: `2026-09-05T18:17:09.546625+00:00`
Status: **DESIGN LOCKED — OBSERVE NOW OPERATING**
Live stitch: **FORBIDDEN** · Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT books **`E22_v2s_tw` KEEP**
Claimed MDD ≈ −13.16%: **`RETIRED_HISTORICAL_NARRATIVE`** (do not invent a replacement)
Operating observe: **OPEN** (`E45_DUAL_PAPER_OBSERVE_OPEN.md`) — paper only; stitch still FORBIDDEN

## Locked paper books

| Book | Definition |
|---|---|
| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack Exact T+1 + E22_v2s formal books |
| `CHAL_E45_E3` | Same stack + E45 `E3_VOLTARGET_WINNER` exposure overlay (challenger) |

## Window metrics (Exact T+1; paper only)

| Book | Window | CAGR | MDD | n_days |
|---|---|---:|---:|---:|
| BASE_E16_E18_E22_v2s | full | 13.78% | -22.64% | 3351 |
| BASE_E16_E18_E22_v2s | oof_2011_2018 | 8.85% | -17.41% | 1495 |
| BASE_E16_E18_E22_v2s | validation_2019_2022 | 12.33% | -22.64% | 977 |
| BASE_E16_E18_E22_v2s | sealed_2023_plus | 24.93% | -14.46% | 879 |
| BASE_E16_E18_E22_v2s | heldout_2019_plus | 18.23% | -22.64% | 1856 |
| CHAL_E45_E3 | full | 10.79% | -20.76% | 3351 |
| CHAL_E45_E3 | oof_2011_2018 | 8.91% | -15.57% | 1495 |
| CHAL_E45_E3 | validation_2019_2022 | 9.97% | -20.76% | 977 |
| CHAL_E45_E3 | sealed_2023_plus | 15.52% | -9.56% | 879 |
| CHAL_E45_E3 | heldout_2019_plus | 12.59% | -20.76% | 1856 |

## Deltas vs BASE (challenger − base)

| Window | MDD Δ (pp; + = shallower drawdown) | CAGR giveback (pp) |
|---|---:|---:|
| heldout_2019_plus | 1.88 | 5.65 |
| sealed_2023_plus | 4.90 | 9.40 |
| full | 1.88 | 2.99 |

## Ops checklist (design → future observe)

1. Soft-Frozen live default stays BASE until a **separate** human cutover/stitch PR
2. Observe OPEN: run BASE + CHAL_E45_E3 paper ledgers in parallel month-end
3. Re-check trailing YTD / 1y PAUSE gates each month-end (observe ≠ promote)
4. Do **not** silent-edit Soft-Frozen; do **not** rewrite `forward/e21` history
5. Observe sleeve ≠ stitch license; V1–V6 still gate any live stitch
6. Never cite −13.16% as verified; use dated lineage / challenger MDDs only

## Explicit non-goals

- Auto live-wire from this design pack
- Soft-Frozen clip flip
- Four-layer live stitch
- Bundling FIN50 / L4 / BLEND / odd-lot / tax DEFAULT promote
- Closing V1 by inventing an MDD

## V4 / V5 attachment

- V4: lineage E3 cost sensitivity attached → `repro/e45-dual-paper-observe-design/outputs/lineage_e3_cost_sensitivity.csv` (E45-named seal still open)
- V5: multi-window table above; lineage multi-val windows already dated — E45-named multi-crisis seal still open

## Artifacts

- `repro/e45-dual-paper-observe-design/outputs/dual_paper_window_metrics.csv`
- `repro/e45-dual-paper-observe-design/summary.json`
- This memo: `research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md`
- Checklist: `research/ops/E45_DUAL_PAPER_OBSERVE_CHECKLIST.md`

## Label

`E45_DUAL_PAPER_OBSERVE_DESIGN_2026-09-05__OPERATING_OBSERVE__STITCH_FORBIDDEN`

