# Stage-4B Bad-Month Feature Attribution (Diagnosis Only)

Shared C2/C4/C8 negative-excess months from Stage-3. **No retune. No held-out selection.**

Bad months (n=13): 2021-02, 2021-03, 2021-06, 2021-07, 2021-09, 2021-12, 2022-02, 2022-03, 2022-04, 2022-05, 2022-06, 2022-08, 2022-12

## Univariate rank IC: bad months vs other 2019–2022

| feature | bad IC | other IC | Δ | OOF IC |
|---|---:|---:|---:|---:|
| pct_downside_vol_60d | 0.1331 | -0.0281 | 0.1612 | 0.0724 |
| defensive_family_score | 0.1190 | -0.0148 | 0.1338 | 0.0719 |
| pct_vol_60d | 0.1172 | -0.0126 | 0.1297 | 0.0795 |
| pct_asset_growth_yoy | 0.1130 | -0.0116 | 0.1246 | 0.0161 |
| pct_drawdown_63d | 0.0665 | -0.0568 | 0.1233 | 0.0355 |
| pct_book_to_price_proxy | 0.0985 | 0.0102 | 0.0883 | 0.0239 |
| pct_sales_yield_proxy | 0.0991 | 0.0212 | 0.0779 | 0.0090 |
| pct_mom_63d | 0.0183 | -0.0479 | 0.0662 | -0.0154 |
| value_family_score | 0.0824 | 0.0248 | 0.0576 | 0.0382 |
| pct_revenue_yoy_acceleration | 0.0647 | 0.0110 | 0.0537 | 0.0292 |
| pct_mom_126d | -0.0173 | -0.0392 | 0.0219 | 0.0014 |
| momentum_family_score | -0.0230 | -0.0407 | 0.0176 | -0.0009 |
| pct_reversal_5d | 0.0243 | 0.0218 | 0.0024 | -0.0164 |
| pct_amihud_20d | 0.0267 | 0.0428 | -0.0161 | 0.0316 |
| pct_earnings_yield_proxy | 0.0146 | 0.0349 | -0.0203 | 0.0523 |
| pct_accruals_to_assets | 0.0004 | 0.0317 | -0.0313 | 0.0191 |
| pct_mom_12_1 | -0.0538 | -0.0187 | -0.0351 | 0.0065 |
| pct_monthly_revenue_yoy | -0.0374 | 0.0046 | -0.0419 | 0.0278 |
| pct_revenue_3m_yoy | -0.0424 | 0.0073 | -0.0497 | 0.0199 |
| pct_net_income_growth_yoy | -0.0590 | 0.0198 | -0.0789 | 0.0050 |
| growth_family_score | -0.0707 | 0.0175 | -0.0883 | 0.0157 |
| pct_leverage | -0.0943 | -0.0023 | -0.0920 | -0.0322 |
| pct_revenue_growth_yoy | -0.1136 | 0.0014 | -0.1149 | -0.0220 |
| pct_cfo_to_assets | -0.0703 | 0.0459 | -0.1162 | 0.0158 |
| pct_roe_ttm | -0.0866 | 0.0328 | -0.1194 | 0.0216 |

## Relatively resilient (OOF IC>0.02 and Δ>-0.02)

- `pct_downside_vol_60d`: bad=0.1331, other=-0.0281, OOF=0.0724
- `defensive_family_score`: bad=0.1190, other=-0.0148, OOF=0.0719
- `pct_vol_60d`: bad=0.1172, other=-0.0126, OOF=0.0795
- `pct_drawdown_63d`: bad=0.0665, other=-0.0568, OOF=0.0355
- `pct_book_to_price_proxy`: bad=0.0985, other=0.0102, OOF=0.0239
- `value_family_score`: bad=0.0824, other=0.0248, OOF=0.0382
- `pct_revenue_yoy_acceleration`: bad=0.0647, other=0.0110, OOF=0.0292
- `pct_amihud_20d`: bad=0.0267, other=0.0428, OOF=0.0316

## Fragile in bad months (OOF IC>0.02 and Δ<-0.03)

- `pct_monthly_revenue_yoy`: bad=-0.0374, other=0.0046, Δ=-0.0419
- `pct_roe_ttm`: bad=-0.0866, other=0.0328, Δ=-0.1194

## C4 buy tilts in bad months (vs same-day universe)

- `pct_vol_60d`: tilt=0.2347 (buy=0.735, uni=0.500)
- `pct_downside_vol_60d`: tilt=0.2081 (buy=0.708, uni=0.500)
- `pct_mom_126d`: tilt=-0.1758 (buy=0.324, uni=0.500)
- `defensive_family_score`: tilt=0.1699 (buy=0.670, uni=0.500)
- `pct_amihud_20d`: tilt=0.1624 (buy=0.662, uni=0.500)
- `momentum_family_score`: tilt=-0.1587 (buy=0.341, uni=0.500)
- `pct_mom_63d`: tilt=-0.1570 (buy=0.343, uni=0.500)
- `pct_mom_12_1`: tilt=-0.1434 (buy=0.357, uni=0.500)
- `pct_earnings_yield_proxy`: tilt=0.1413 (buy=0.641, uni=0.500)
- `pct_book_to_price_proxy`: tilt=0.1240 (buy=0.624, uni=0.500)
- `pct_monthly_revenue_yoy`: tilt=-0.1215 (buy=0.379, uni=0.500)
- `value_family_score`: tilt=0.1139 (buy=0.615, uni=0.501)

## Implication

Bad-month IC gaps show which atomic signals weaken in shared failure months; use only as navigation for OOF atomic screens — do not select on held-out deltas.

Artifact: `reports/stage4_bad_month_attribution.json`
