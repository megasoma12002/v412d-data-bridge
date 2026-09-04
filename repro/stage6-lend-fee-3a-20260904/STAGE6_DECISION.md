# Stage 6 Decision — Lending Fee 3A Probe

Feature: `-z(lend_fee_1m)` monthly top-20% vs EW  
Source: FinMind `TaiwanStockSecuritiesLending` (new PIT family)

## Gates (dev 2019–2024)

{
  "net40_mean_excess_gt_0": false,
  "net40_no_consec_neg_3y": false,
  "loyo_not_fragile": false,
  "coverage_months_dev_ge_36": true,
  "codes_ge_40": true
}

Net40 mean excess: **-0.007952100420667865**  
Sealed 2025+ net40: **0.006087932133904795**

## Decision

**`STOP_STAGE6_LEND_FEE_FEATURE_SET`**

Promotion: **False** (even on PASS — needs explicit approval + locked C4 bar).
