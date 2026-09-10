# Sleeve-Layer Tilt Screen — Stage A

Generated: `2026-09-10T15:47:46.130798+00:00` · asof **2026-09-10**
Charter: `SLEEVE_LAYER_TILT_CHARTER.md`
Verdict: **`BEATS_LIVE`** · books **21** · seed `SLEEVE_BELOW_MA60_a01`

## Question

Does Soft-Frozen router sleeve-NAV tilt tip-clean beat **LIVE_STACK** (clips KEEP, KD/TEL unchanged)?

## Summary

- Beat live: **3** → `['SLEEVE_BELOW_MA60_a01', 'SLEEVE_BELOW_MA60_a005', 'SLEEVE_RSI14_LT30_a02']`
- Tip-clean challengers: **20** · coexist **3**
- Near (tip-clean, score &gt; −0.05): `['SLEEVE_BELOW_MA60_a01', 'SLEEVE_BELOW_MA60_a005', 'SLEEVE_RSI14_LT30_a02', 'SLEEVE_RSI14_LT30_a015', 'SLEEVE_RSI14_LT30_a005', 'SLEEVE_RSI14_LT30_a01', 'SLEEVE_BELOW_MA120_a015', 'SLEEVE_BELOW_MA40_a015']`
- Seed `SLEEVE_BELOW_MA60_a01`: tip_clean=True · coexist=True · held=0.050 · vs live Δ=0.050
- Grid: signals `['BELOW_MA60', 'BELOW_MA40', 'BELOW_MA120', 'RSI14_LT30', 'MOM20_NEG']` · α `[0.05, 0.1, 0.15, 0.2]` · sign +1

## Top 20

| ID | Signal | α | Tip YTD | Tip 1y | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD | Seed |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|:---:|
| `SLEEVE_BELOW_MA60_a01` | BELOW_MA60 | 0.10 | PASS | PASS | 0.050 | 0.062 | 18.09% | -21.66% | 24.93% | -12.96% | Y |
| `SLEEVE_BELOW_MA60_a005` | BELOW_MA60 | 0.05 | PASS | PASS | 0.021 | 0.035 | 18.04% | -21.69% | 24.83% | -12.87% |  |
| `SLEEVE_RSI14_LT30_a02` | RSI14_LT30 | 0.20 | PASS | PASS | 0.003 | 0.010 | 18.06% | -21.71% | 24.86% | -12.80% |  |
| `LIVE_STACK` | none | — | PASS | PASS | 0.000 | 0.000 | 18.07% | -21.72% | 24.86% | -12.81% |  |
| `SLEEVE_RSI14_LT30_a015` | RSI14_LT30 | 0.15 | PASS | PASS | -0.007 | 0.002 | 18.09% | -21.72% | 24.89% | -12.88% |  |
| `SLEEVE_RSI14_LT30_a005` | RSI14_LT30 | 0.05 | PASS | PASS | -0.013 | -0.008 | 18.08% | -21.73% | 24.86% | -12.83% |  |
| `SLEEVE_RSI14_LT30_a01` | RSI14_LT30 | 0.10 | PASS | PASS | -0.013 | -0.006 | 18.08% | -21.73% | 24.89% | -12.87% |  |
| `SLEEVE_BELOW_MA120_a015` | BELOW_MA120 | 0.15 | PASS | PASS | -0.035 | 0.037 | 17.92% | -21.68% | 24.62% | -12.99% |  |
| `SLEEVE_BELOW_MA40_a015` | BELOW_MA40 | 0.15 | PASS | PASS | -0.040 | 0.028 | 18.21% | -21.69% | 25.20% | -12.82% |  |
| `SLEEVE_BELOW_MA40_a01` | BELOW_MA40 | 0.10 | PASS | PASS | -0.058 | -0.031 | 18.12% | -21.75% | 24.99% | -12.95% |  |
| `SLEEVE_BELOW_MA120_a005` | BELOW_MA120 | 0.05 | PASS | PASS | -0.066 | -0.024 | 17.98% | -21.74% | 24.72% | -12.89% |  |
| `SLEEVE_MOM20_NEG_a005` | MOM20_NEG | 0.05 | PASS | PASS | -0.078 | -0.060 | 18.03% | -21.78% | 24.87% | -12.82% |  |
| `SLEEVE_BELOW_MA120_a01` | BELOW_MA120 | 0.10 | PASS | PASS | -0.081 | 0.006 | 17.89% | -21.71% | 24.64% | -12.83% |  |
| `SLEEVE_BELOW_MA120_a02` | BELOW_MA120 | 0.20 | PASS | PASS | -0.091 | -0.009 | 17.90% | -21.73% | 24.59% | -13.05% |  |
| `SLEEVE_BELOW_MA60_a02` | BELOW_MA60 | 0.20 | PASS | PASS | -0.134 | -0.057 | 18.22% | -21.78% | 25.17% | -13.26% |  |
| `SLEEVE_BELOW_MA40_a005` | BELOW_MA40 | 0.05 | PASS | PASS | -0.138 | -0.132 | 18.06% | -21.85% | 24.91% | -12.94% |  |
| `SLEEVE_BELOW_MA40_a02` | BELOW_MA40 | 0.20 | PASS | PASS | -0.146 | -0.057 | 18.25% | -21.78% | 25.28% | -13.23% |  |
| `SLEEVE_BELOW_MA60_a015` | BELOW_MA60 | 0.15 | PASS | PASS | -0.161 | -0.111 | 18.17% | -21.83% | 25.13% | -13.22% |  |
| `SLEEVE_MOM20_NEG_a01` | MOM20_NEG | 0.10 | PASS | PASS | -0.199 | -0.143 | 18.18% | -21.86% | 25.04% | -13.07% |  |
| `SLEEVE_MOM20_NEG_a02` | MOM20_NEG | 0.20 | PASS | PASS | -0.211 | -0.083 | 18.32% | -21.80% | 25.31% | -13.17% |  |

## LIVE_STACK reference

- full CAGR/MDD: 13.85% / -21.72%
- heldout CAGR/MDD: 18.07% / -21.72%
- sealed CAGR/MDD: 24.86% / -12.81%

## Reading

- Held score = MDD↑pp − 0.5·|CAGRΔpp| vs **LIVE_STACK**.
- Prior Track C seed **confirmed** tip-clean beat-live under live-stack scoring (held ≈ +0.050; lift small).
- Soft-assist observe stays independent — **no auto-combo**.
- **Decision:** Stage A **`BEATS_LIVE`** · champion **`SLEEVE_BELOW_MA60_a01`** · draft **OPEN observe** ballot only on human ask · **no live wire**.

## Non-actions

- No Soft-Frozen clip / KD / TEL / Soft-assist / E45 wire from this screen

## Label

`SLEEVE_LAYER_TILT_SCREEN_STAGE_A_2026-09-10__BEATS_LIVE`
