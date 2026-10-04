# TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_DECISION_PACK

Date: 2026-10-04 · Verdict: **`IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020`** · top=**`and::rvol63_l4&fuse_prem_neg5`**
Register: **0kbj** · Parents: 0kbi, 0kbh, 0kbf · **SIGNAL_HIST_OOS_PARALLEL**

## Answer

- Global: **`IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020`**
- Champ `and::rvol63_l4&fuse_prem_neg5` by episode: `{'GFC_2008': 'NO_DATA', 'TW_CN_2015': 'OOS_MISS', 'EU_US_2011': 'NO_DATA', 'Q4_2018': 'OOS_WEAK', 'MAR2020': 'OOS_WEAK'}`
- Hist OOS_HIT cores: [] · WEAK [] · MISS ['TW_CN_2015'] · NO_DATA ['GFC_2008']
- Mar2020 ref (in-sample): `OOS_WEAK`
- Data start: NAV **2012-12-04** · 0050 **2010-01-04**

## Constraints kept

- Soft KEEP · Path4 OFF · broker false · Exact T+1
- **signal ≠ apply** · no LIVE · no tip Soft promote · no year-oracle
- soak freeze unchanged · no size-apply promote

## Disposition

- **SIGNAL_HIST_OOS / PARALLEL** — detection only; **signal ≠ apply**
- Does **not** unlock soak freeze · does **not** recommend LIVE wire
- No tip Soft promote · no year-oracle · Soft KEEP · Path4 OFF · broker false
- Data limitation: panel/NAV start 2012-12-04; 0050 start 2010-01-04 — GFC 2008 = NO_DATA (fail loud)
- Champ selected on Mar2020 (0kbi) fails OOS floors on available hist cores (2015 miss / 2008 no-data) — overfit-2020 risk elevated; do not promote signal→apply

Label: `TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_DECISION_PACK_2026-10-04__IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020__SIGNAL_HIST_OOS_PARALLEL__NO_LIVE`
