# TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_CHARTER

Date: 2026-10-04
Register: **0kbh** · Parents: 0kbg, 0kbf, 0kb4
Label: **SIGNAL_PARALLEL** · SOAK-SAFE parallel · **signal ≠ apply**

## Question

Which causal lag-1 features best **detect** Mar2020 cliff / 2020 crisis stress days on the L4 twin world (0050 / soft NAV / market), measured by IC / hit-rate / lead days — without applying exposure?

## Labels

- Forward N-day MDD / crash return (5/10/20) on L4 & 0050
- In Mar2020 window 2020-02-20→2020-03-23
- Soft/L4 NAV dd-from-peak crossing −5%/−8%/−10%

## Detectors (lag-1 causal)

- Realized vol 20/63 (L4 & 0050)
- ATR-like range 20
- 0050 vs MA60/MA120/MA200 (neg gap / below flags)
- dd63 (mkt/L4/soft) · proxy_mdd63 · COOL defend · FUSE-prem proxies
- Consecutive down days
- VIX proxy if available else skip · breadth skip if unavailable

## Metrics / verdict

- Spearman/Pearson IC vs `fwd_mdd_10` · Mar hit P/R/F1 · lead days · FA outside 2020
- Floors: |IC|≥0.08 · hit≥0.58 · lead≥3.0d · FA≤0.12 · OOS|IC|≥0.05 · not year-dummy
- `SIGNAL_HIT` / `SIGNAL_WEAK` / `SIGNAL_NO_EDGE`

## Hard constraints

- Soft KEEP · Path4 OFF · broker false · Exact T+1
- **signal ≠ apply** · no tip Soft promote · no year-oracle
- does **not** unlock soak freeze · no LIVE wire · no size-overlay promote
- vs 0kbg: size overlays MDD_ONLY → this fork is detection-only

Label: `TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_CHARTER_2026-10-04__SIGNAL_PARALLEL`
