# Live Baseline — Leverage Combination Trial (DIAGNOSE ONLY)

Date: 2026-09-13 · asof tip `2026-09-11`  
Status: **DIAGNOSE ONLY** · synthetic `r_L = e_t · r_BASE`  
Base: Soft-Frozen + `KD_OPT` + `TEL_EQUAL` · `repro/kelly-exposure-stagea/outputs/nav_BASE_LIVE_STACK.csv`  

## Fidelity / non-actions

- **Not** a margin/borrow simulator; L>1 is **not executable** in current Exact T+1 cash engine.
- `e45_exposure` clips to `[0,1]` — do not pass L>1 expecting gearing.
- No live wire · no Soft-Frozen flip · no promote from this table alone.

## Candidate menu (pick 1..N)

| id | meaning |
|---|---|
| `L100` | constant 1.00× (Live BASE) |
| `L125` / `L150` / `L175` / `L200` | constant 1.25× / 1.50× / 1.75× / 2.00× |
| `REGIME_B15_X08` | Bull 1.50× · else 0.80× |
| `REGIME_B20_X07` | Bull 2.00× · else 0.70× |
| `DDGATE_15_07` | BASE lagged DD ≤ −10% → 0.70× · else 1.50× |

### Combine rules

- **equal_weight**: capital split across selected books → effective e = mean(e_i).
- **product**: daywise product of selected schedules → e = ∏ e_i.

```bash
python3 scripts/e16_live_leverage_combo_trial.py --pick L150 L200 --mode equal_weight
python3 scripts/e16_live_leverage_combo_trial.py --pick L125 DDGATE_15_07 --mode product
```

## Single-candidate grid (heldout sort)

| book | picks | mode | mean e | heldout_2019_plus CAGR | heldout_2019_plus MDD | vs BASE CAGR | MDD improve | util |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `SINGLE__REGIME_B20_X07` | REGIME_B20_X07 | equal_weight | 1.65 | 39.78% | -19.40% | +21.39pp | +2.32pp | 30.08% |
| `SINGLE__REGIME_B15_X08` | REGIME_B15_X08 | equal_weight | 1.31 | 28.87% | -19.70% | +10.48pp | +2.02pp | 19.02% |
| `SINGLE__L200` | L200 | equal_weight | 2.00 | 37.14% | -39.35% | +18.74pp | -17.63pp | 17.46% |
| `SINGLE__L175` | L175 | equal_weight | 1.75 | 32.46% | -35.29% | +14.07pp | -13.57pp | 14.82% |
| `SINGLE__DDGATE_15_07` | DDGATE_15_07 | equal_weight | 1.44 | 24.53% | -24.20% | +6.14pp | -2.48pp | 12.43% |
| `SINGLE__L150` | L150 | equal_weight | 1.50 | 27.77% | -31.00% | +9.38pp | -9.28pp | 12.27% |
| `SINGLE__L125` | L125 | equal_weight | 1.25 | 23.08% | -26.48% | +4.68pp | -4.76pp | 9.84% |
| `SINGLE__L100` | L100 | equal_weight | 1.00 | 18.39% | -21.72% | -0.00pp | +0.00pp | 7.53% |

### Full-sample

| book | picks | mode | mean e | full CAGR | full MDD | vs BASE CAGR | MDD improve | util |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `SINGLE__REGIME_B20_X07` | REGIME_B20_X07 | equal_weight | 1.65 | 31.79% | -19.40% | +17.77pp | +2.32pp | 22.09% |
| `SINGLE__REGIME_B15_X08` | REGIME_B15_X08 | equal_weight | 1.31 | 22.85% | -19.70% | +8.83pp | +2.02pp | 13.00% |
| `SINGLE__L200` | L200 | equal_weight | 2.00 | 27.82% | -39.35% | +13.79pp | -17.63pp | 8.14% |
| `SINGLE__L175` | L175 | equal_weight | 1.75 | 24.42% | -35.29% | +10.40pp | -13.57pp | 6.78% |
| `SINGLE__DDGATE_15_07` | DDGATE_15_07 | equal_weight | 1.44 | 18.76% | -24.21% | +4.73pp | -2.49pp | 6.65% |
| `SINGLE__L150` | L150 | equal_weight | 1.50 | 20.98% | -31.00% | +6.96pp | -9.28pp | 5.48% |
| `SINGLE__L125` | L125 | equal_weight | 1.25 | 17.51% | -26.48% | +3.49pp | -4.76pp | 4.27% |
| `SINGLE__L100` | L100 | equal_weight | 1.00 | 14.02% | -21.72% | -0.00pp | +0.00pp | 3.16% |

### Sealed 2023+

| book | picks | mode | mean e | sealed_2023_plus CAGR | sealed_2023_plus MDD | vs BASE CAGR | MDD improve | util |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `SINGLE__REGIME_B20_X07` | REGIME_B20_X07 | equal_weight | 1.65 | 50.68% | -14.74% | +25.11pp | -1.93pp | 43.31% |
| `SINGLE__REGIME_B15_X08` | REGIME_B15_X08 | equal_weight | 1.31 | 37.63% | -13.36% | +12.06pp | -0.56pp | 30.95% |
| `SINGLE__L200` | L200 | equal_weight | 2.00 | 53.59% | -24.67% | +28.02pp | -11.86pp | 41.26% |
| `SINGLE__L175` | L175 | equal_weight | 1.75 | 46.41% | -21.80% | +20.84pp | -8.99pp | 35.51% |
| `SINGLE__DDGATE_15_07` | DDGATE_15_07 | equal_weight | 1.44 | 34.20% | -21.75% | +8.63pp | -8.94pp | 23.33% |
| `SINGLE__L150` | L150 | equal_weight | 1.50 | 39.34% | -18.86% | +13.77pp | -6.05pp | 29.91% |
| `SINGLE__L125` | L125 | equal_weight | 1.25 | 32.39% | -15.86% | +6.81pp | -3.06pp | 24.45% |
| `SINGLE__L100` | L100 | equal_weight | 1.00 | 25.57% | -12.81% | -0.00pp | -0.00pp | 19.17% |

## Multi-candidate combinations

| book | picks | mode | mean e | heldout_2019_plus CAGR | heldout_2019_plus MDD | vs BASE CAGR | MDD improve | util |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `PROD__L125_REGIME_B15_X08_DDGATE_15_07` | L125+REGIME_B15_X08+DDGATE_15_07 | product | 2.39 | 52.61% | -26.79% | +34.21pp | -5.07pp | 39.21% |
| `PROD__REGIME_B15_X08_DDGATE_15_07` | REGIME_B15_X08+DDGATE_15_07 | product | 1.91 | 41.32% | -21.91% | +22.93pp | -0.19pp | 30.37% |
| `PROD__L125_REGIME_B15_X08` | L125+REGIME_B15_X08 | product | 1.64 | 36.67% | -24.06% | +18.28pp | -2.34pp | 24.64% |
| `PROD__L150_DDGATE_15_07` | L150+DDGATE_15_07 | product | 2.16 | 36.78% | -34.55% | +18.38pp | -12.83pp | 19.50% |
| `PROD__L125_DDGATE_15_07` | L125+DDGATE_15_07 | product | 1.80 | 30.69% | -29.52% | +12.29pp | -7.80pp | 15.93% |
| `EQ__L150_L200` | L150+L200 | equal_weight | 1.75 | 32.46% | -35.29% | +14.07pp | -13.57pp | 14.82% |
| `EQ__L125_L175_L200` | L125+L175+L200 | equal_weight | 1.67 | 30.90% | -33.89% | +12.51pp | -12.16pp | 13.96% |
| `EQ__L125_L150_L175` | L125+L150+L175 | equal_weight | 1.50 | 27.77% | -31.00% | +9.38pp | -9.28pp | 12.27% |
| `EQ__L100_L200` | L100+L200 | equal_weight | 1.50 | 27.77% | -31.00% | +9.38pp | -9.28pp | 12.27% |
| `EQ__L100_L150_L200` | L100+L150+L200 | equal_weight | 1.50 | 27.77% | -31.00% | +9.38pp | -9.28pp | 12.27% |
| `EQ__L125_L150` | L125+L150 | equal_weight | 1.38 | 25.42% | -28.77% | +7.03pp | -7.05pp | 11.04% |

### Multi — sealed 2023+

| book | picks | mode | mean e | sealed_2023_plus CAGR | sealed_2023_plus MDD | vs BASE CAGR | MDD improve | util |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `PROD__L125_REGIME_B15_X08_DDGATE_15_07` | L125+REGIME_B15_X08+DDGATE_15_07 | product | 2.39 | 69.56% | -26.79% | +43.99pp | -13.99pp | 56.17% |
| `PROD__REGIME_B15_X08_DDGATE_15_07` | REGIME_B15_X08+DDGATE_15_07 | product | 1.91 | 54.09% | -21.91% | +28.52pp | -9.10pp | 43.13% |
| `PROD__L125_REGIME_B15_X08` | L125+REGIME_B15_X08 | product | 1.64 | 48.23% | -16.52% | +22.66pp | -3.71pp | 39.97% |
| `PROD__L150_DDGATE_15_07` | L150+DDGATE_15_07 | product | 2.16 | 52.17% | -31.29% | +26.60pp | -18.48pp | 36.52% |
| `PROD__L125_DDGATE_15_07` | L125+DDGATE_15_07 | product | 1.80 | 43.16% | -26.63% | +17.59pp | -13.82pp | 29.85% |
| `EQ__L150_L200` | L150+L200 | equal_weight | 1.75 | 46.41% | -21.80% | +20.84pp | -8.99pp | 35.51% |
| `EQ__L125_L175_L200` | L125+L175+L200 | equal_weight | 1.67 | 44.04% | -20.83% | +18.47pp | -8.02pp | 33.63% |
| `EQ__L125_L150_L175` | L125+L150+L175 | equal_weight | 1.50 | 39.34% | -18.86% | +13.77pp | -6.05pp | 29.91% |
| `EQ__L100_L200` | L100+L200 | equal_weight | 1.50 | 39.34% | -18.86% | +13.77pp | -6.05pp | 29.91% |
| `EQ__L100_L150_L200` | L100+L150+L200 | equal_weight | 1.50 | 39.34% | -18.86% | +13.77pp | -6.05pp | 29.91% |
| `EQ__L125_L150` | L125+L150 | equal_weight | 1.38 | 35.85% | -17.37% | +10.27pp | -4.56pp | 27.16% |

## Tip hygiene (YTD / trailing ~1y CAGR vs BASE)

| book | YTD CAGR | YTD vs BASE | 1y CAGR | 1y vs BASE | YTD MDD | 1y MDD |
|---|---:|---:|---:|---:|---:|---:|
| `SINGLE__L100` | 73.62% | -0.00pp | 55.31% | -0.00pp | -12.81% | -12.81% |
| `SINGLE__L125` | 97.61% | +24.00pp | 72.29% | +16.97pp | -15.86% | -15.86% |
| `SINGLE__L150` | 124.17% | +50.55pp | 90.63% | +35.32pp | -18.86% | -18.86% |
| `SINGLE__L175` | 153.43% | +79.81pp | 110.39% | +55.08pp | -21.80% | -21.80% |
| `SINGLE__L200` | 185.55% | +111.93pp | 131.61% | +76.30pp | -24.67% | -24.67% |
| `SINGLE__REGIME_B15_X08` | 115.57% | +41.95pp | 85.56% | +30.25pp | -13.36% | -13.36% |
| `SINGLE__REGIME_B20_X07` | 168.24% | +94.62pp | 121.85% | +66.54pp | -14.74% | -14.74% |
| `SINGLE__DDGATE_15_07` | 95.48% | +21.86pp | 73.47% | +18.15pp | -21.75% | -21.75% |
| `EQ__L125_L150` | 110.56% | +36.94pp | 81.28% | +25.97pp | -17.37% | -17.37% |
| `EQ__L150_L200` | 153.43% | +79.81pp | 110.39% | +55.08pp | -21.80% | -21.80% |
| `EQ__L125_L150_L175` | 124.17% | +50.55pp | 90.63% | +35.32pp | -18.86% | -18.86% |
| `EQ__L100_L200` | 124.17% | +50.55pp | 90.63% | +35.32pp | -18.86% | -18.86% |
| `EQ__L125_L175_L200` | 143.37% | +69.75pp | 103.64% | +48.33pp | -20.83% | -20.83% |
| `EQ__L100_L150_L200` | 124.17% | +50.55pp | 90.63% | +35.32pp | -18.86% | -18.86% |
| `PROD__L125_REGIME_B15_X08` | 158.80% | +85.18pp | 114.95% | +59.63pp | -16.52% | -16.52% |
| `PROD__L150_DDGATE_15_07` | 162.02% | +88.40pp | 121.31% | +65.99pp | -31.29% | -31.29% |
| `PROD__L125_DDGATE_15_07` | 127.11% | +53.49pp | 96.46% | +41.14pp | -26.63% | -26.63% |
| `PROD__REGIME_B15_X08_DDGATE_15_07` | 177.23% | +103.61pp | 130.08% | +74.77pp | -21.91% | -21.91% |
| `PROD__L125_REGIME_B15_X08_DDGATE_15_07` | 250.76% | +177.14pp | 178.82% | +123.51pp | -26.79% | -26.79% |

## Reading guide

- **Constant L** (L125…L200): CAGR and |MDD| both scale roughly with L on this synthetic overlay (near-linear).
- **Equal-weight mixes** of constants ≈ arithmetic mean L (e.g. L100+L200 ≈ L150).
- **PRODUCT stacks of L>1 schedules are diagnose-only fantasies** — multiplying L125 × REGIME × DDGATE compounds gross exposure (mean e can exceed 2) with **no** borrow/liquidation model; do **not** treat as executable or promote-shaped.
- Regime / DD-gate alone can show shallower MDD than constant L at similar mean e — still synthetic; tip giveback must be checked before any charter talk.
- Live wire / Soft-Frozen flip / executable margin: **out of scope**.


## Label

`LIVE_LEVERAGE_COMBO_TRIAL_2026-09-13__SYNTHETIC__NO_LIVE_WIRE`

