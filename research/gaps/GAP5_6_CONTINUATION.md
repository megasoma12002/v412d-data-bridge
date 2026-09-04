# Gap #5 / #6 Continuation Research

Generated: `2026-09-04T18:05:18.281484+00:00`

**EXPERIMENTAL.** No live overlay wire. No R1 promotion. No live NAV history rewrite.

## Predeclared controls

- Overlay mixes: `[('CORE_100', 1.0, 0.0), ('CORE_90_OVL_10', 0.9, 0.1), ('CORE_80_OVL_20', 0.8, 0.2), ('CORE_70_OVL_30', 0.7, 0.3)]`
- Overlap start: `2019-01-02` (R1 validation start)
- Core books: E22_v2s historical recompute NAV
- Overlay: A3-R1 `daily_nav.csv` (standalone sleeve)

## Paper combined book (capital-weighted index stitch)

| Mix | Full CAGR | Full MDD | Val CAGR | Val MDD | Sealed CAGR | Sealed MDD |
|---|---:|---:|---:|---:|---:|---:|
| CORE_100 | 17.22% | -22.64% | 12.33% | -22.64% | 22.71% | -14.46% |
| CORE_90_OVL_10 | 18.89% | -23.29% | 12.60% | -23.29% | 26.13% | -11.04% |
| CORE_80_OVL_20 | 20.43% | -23.96% | 12.87% | -23.96% | 29.29% | -13.50% |
| CORE_70_OVL_30 | 21.85% | -24.64% | 13.14% | -24.64% | 32.22% | -15.90% |

Interpretation: sealed strength of R1 lifts mixes with more overlay weight, but validation
still shows deep MDD and does **not** clear R1 gates. Paper stitch ≠ promotion.

## Failure signature (R1 vs 0050 stand-in)

- Months losing to proxy: `0.5760869565217391`
- Mean monthly excess: `0.010102288333519314`
- Proxy note: Stand-in proxy (0050), not the official PIT equal-weight proxy used in R1 gates. Overlay NAV chained across validation→sealed reset.

Worst months (by excess):

| Month | Excess | Ovl | 0050 |
|---|---:|---:|---:|
| 2025-09 | -7.92% | 1.81% | 9.72% |
| 2021-05 | -7.43% | -9.61% | -2.17% |
| 2020-07 | -6.66% | 7.92% | 14.59% |
| 2024-06 | -5.99% | 5.85% | 11.84% |
| 2024-10 | -5.71% | -1.37% | 4.33% |
| 2019-10 | -4.63% | 1.73% | 6.36% |
| 2026-05 | -4.41% | 11.20% | 15.62% |
| 2020-09 | -3.95% | -2.68% | 1.28% |

## Lot / fractional sensitivity (end positions from E22_v2s sim)

- `float_keep`: stranded_total_shares=`0.0000`
- `floor_int`: stranded_total_shares=`2.1956`
- `board_lot_1000`: stranded_total_shares=`1716.1956`
- Note: Board-lot 1000 zeros small telecom sleeves; floor_int only drops fractional dust. Full fill re-sim under board lots left as follow-on E18 challenger.

## Decision

- Live overlay: `STILL_NO`
- Do not promote any mix from this paper stitch
- Next: Use failure months to design overlay risk budget (not live weights); E18 board-lot full re-sim challenger if capacity questions arise; Keep E22_v2s as formal books; fractional floor+CIL optional follow-on

## Artifacts

- `research/gaps/GAP5_6_CONTINUATION.json`
- `repro/gap5-6-continuation/`

