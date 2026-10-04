# TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_CHARTER

Date: 2026-10-04
Register: **0kbi** · Parents: 0kbh, 0kbg, 0kbf
Label: **SIGNAL_REFINE_PARALLEL** · SOAK-SAFE parallel · **signal ≠ apply**

## Question

訊號有弱邊，可以研究出強邊嗎？ — Can refine families (combos / confirms / adaptive thresholds / dual-horizon / episodes) upgrade 0kbh SIGNAL_WEAK singles to SIGNAL_HIT on Mar2020 / 2020 crisis detection — without apply?

## Refine families

1. AND/OR combos of top 0kbh singles (rvol20, atr_like_20, fuse_neg, cool_defend, …)
2. k-confirm (2–3 consecutive lag-1 alert flags)
3. Adaptive thresholds (rolling p80/p90/p95 of vol/ATR/dd)
4. Dual-horizon score (IC vs fwd_mdd_5 ∧ fwd_mdd_10 / crash)
5. Enter/exit episode rules (enter on spike, hold min days)

## Floors (match 0kbh)

- |IC|≥0.08 · hit≥0.58 · recall≥0.35 · lead≥3.0d · FA≤0.12 · OOS|IC|≥0.05 · year-dummy|IC|<0.55

## Hard constraints

- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1
- **signal ≠ apply** · no tip Soft promote · no year-oracle
- does **not** unlock soak freeze · no LIVE wire

Label: `TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_CHARTER_2026-10-04__SIGNAL_REFINE_PARALLEL`
