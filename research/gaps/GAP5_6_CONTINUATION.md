# Gap #5 / #6 Continuation Research

Generated: `2026-09-04T18:08:40.825995+00:00`

**EXPERIMENTAL.** No live overlay wire. No R1 promotion. No live NAV history rewrite.

## Predeclared controls

- Overlay mixes: `[('CORE_100', 1.0, 0.0), ('CORE_90_OVL_10', 0.9, 0.1), ('CORE_80_OVL_20', 0.8, 0.2), ('CORE_70_OVL_30', 0.7, 0.3)]`
- Overlap start: `2019-01-02` (R1 validation start)
- Core books: E22_v2s historical recompute NAV
- Overlay: A3-R1 `daily_nav.csv` (standalone sleeve)
- Risk-budget base mix: `CORE_80_OVL_20` rules=`['STATIC', 'TRAIL_3M_HALVE', 'TRAIL_3M_ZERO', 'COMBINED_DD15_CUT']`
- E18 lot re-sim: `[('share_1', 1), ('board_lot_1000', 1000)]`

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

## Overlay risk budget (paper, causal throttles on CORE_80/20)

Rules use only **prior complete months** (or running combined DD). No calendar blacklists. Not live weights.

| Rule | Mean scale | % days scaled | Full CAGR | Full MDD | Val CAGR | Val MDD | Sealed CAGR | Sealed MDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| STATIC | 1.000 | 0.0% | 20.43% | -23.96% | 12.87% | -23.96% | 29.29% | -13.50% |
| TRAIL_3M_HALVE | 0.920 | 16.1% | 20.43% | -24.06% | 12.87% | -23.18% | 29.29% | -24.06% |
| TRAIL_3M_ZERO | 0.839 | 16.1% | 20.43% | -37.68% | 12.87% | -27.73% | 29.29% | -37.68% |
| COMBINED_DD15_CUT | 0.745 | 25.5% | 20.43% | -36.56% | 6.04% | -36.56% | 38.57% | -13.50% |

Interpretation: throttles can trim overlay exposure after losing streaks / deep combined DD, but do **not** create a promotion path while R1 itself fails gates.

## Lot / fractional sensitivity (end positions from E22_v2s sim)

- `float_keep`: stranded_total_shares=`0.0000`
- `floor_int`: stranded_total_shares=`2.1956`
- `board_lot_1000`: stranded_total_shares=`1716.1956`
- Note: End-position stranding only. Full fill re-sim under board lots is in e18_board_lot_resim() below.

## E18 board-lot full re-sim (E22_v2s books)

| Policy | lot_size | CAGR | MDD | n_fills | end_nav | stranded_vs_1000 |
|---|---:|---:|---:|---:|---:|---:|
| share_1 | 1 | 13.78% | -22.64% | 6262 | 16695201.77 | 1716.20 |
| board_lot_1000 | 1000 | 13.66% | -22.90% | 1901 | 16461488.91 | 2182.51 |
- Delta board vs 1-share: CAGR Δ=`-0.12060109828684329` pp; MDD Δ=`-0.2610576802481557` pp; end_nav ratio=`0.9860011961047616`

Interpretation: board-lot 1000 is a capacity/fill challenger for small sleeves; do not silently replace 1-share research books without a named E18 version.

## Decision

- Live overlay: `STILL_NO`
- Risk budget live: `STILL_NO`
- Board-lot live: `STILL_NO_CHALLENGER_ONLY`
- Do not promote any mix / throttle / lot policy from this paper work
- Next: Alpha-repair track: E50-A3-R1 turnover/held-out diagnosis (separate branch); Optional: fractional floor + cash-in-lieu formal books challenger; Do not live-wire risk budget or board-lot until governance PR

## Artifacts

- `research/gaps/GAP5_6_CONTINUATION.json`
- `repro/gap5-6-continuation/`

