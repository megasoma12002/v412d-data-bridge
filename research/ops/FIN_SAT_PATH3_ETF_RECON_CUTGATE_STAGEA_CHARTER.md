# FIN_SAT_PATH3_ETF_RECON_CUTGATE_STAGEA_CHARTER

Date: 2026-09-30
Status: **Stage A — Path3 0050 ETF feature cut-gate** · Soft **KEEP** · broker **false** · cutover **BLOCKED** · no live
Parent: 0kai `ETF_YEARMIT_HIT` / `ADD_FULL_CUT_D05`
Register: **0kaj**

## Question

Can **causal** tip-gap / book-tenure features gate large Soft `0050` cuts to shrink loser-year drag vs parent `ADD_FULL_CUT_D05` without look-ahead year labels, while keeping HIT vs sticky KEEP?

## Features (as-of)

- `prior_book_days` — completed prior-book run length on flip
- `r0050_63_l1`, `trail_drag_l1`, `zz08_bear_l1` — tipgap panel lag-1
- `trail_rel_63` — Path3 flip depth (same-bar definition)

## Arms

- Baselines: KEEP · RATIO · DEAD_05 · ADD_FULL_CUT_D05
- Gates on large cuts (|Δw|≥5pp): TENURE_LT{5,10} · R50_POS · DRAG_ONLY · ZZ08_ALLOW · DEEP_SAT · TENURE5_R50

## Non-goals

- Year labels · live wire · mute expand · Soft Exact T+1 · satellite · broker

Label: `FIN_SAT_PATH3_ETF_RECON_CUTGATE_STAGEA_CHARTER_2026-09-30__CUTGATE__NO_LIVE`
