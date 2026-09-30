# FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_SCREEN

Date: 2026-09-30 · Verdict: **`ETF_NAV_DUAL_HIT`**
Register: **0kag** · parent 0kae · end=`2026-09-24` · flips KEEP/RATIO=199/199 · etf_moves RATIO=199

## Improvement: `LEDGER_SOFT_RATIO` − `KEEP` (pp)

| Window | CAGR lift pp | MDD improve pp | KEEP → RATIO CAGR |
|---|---:|---:|---|
| full | 0.8217 | 0.4934 | 0.053444 → 0.061661 |
| heldout_2019_plus | 1.6469 | 0.4934 | 0.083203 → 0.099672 |
| sealed_2023_plus | 2.9338 | 9.883 | 0.094062 → 0.1234 |

## Tip

- YTD CAGR lift pp: **1.882** · MDD improve pp: -0.3684
- Trailing 1y CAGR lift pp: **-0.4106** · MDD improve pp: -0.3684

## ETF turnover on flips

- KEEP sum |Δw_0050|: 0.0
- RATIO sum |Δw_0050|: 2.679016

## Context FULL_DAILY − KEEP

| full | 2.0294 | 1.7948 | 0.053444 → 0.073738 |
| held | 4.1686 | 1.7948 | 0.083203 → 0.124889 |

Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_nav_dual_stageb.py`

Label: `FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_SCREEN_2026-09-30__ETF_NAV_DUAL_HIT`
