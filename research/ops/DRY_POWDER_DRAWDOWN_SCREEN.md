# Dry-Powder Drawdown Screen — Stage A

Generated: `2026-09-10T15:10:23.697163+00:00` · asof **2026-09-10**
Charter: `DRY_POWDER_DRAWDOWN_CHARTER.md`
Verdict: **`NO_LIFT`** · powder **10%** · books **37**

## Question

Does 10% dry powder + observable PORT/TAIEX drawdown entry + fixed exit tip-clean beat **LIVE_STACK**?

## Summary

- Beat live: **0** → `[]`
- Near (tip-clean, score &gt; −0.05): `[]`
- Grid: gates `['PORT_DD', 'TAIEX_DD', 'PORT_OR_TAIEX']` · D `[0.1, 0.12, 0.15]` · exits `['HOLD_40', 'RECOVER_HALF', 'RECOVER_FULL', 'TIME_OR_HALF']`

## Top 20

| ID | Gate | Exit | Tip YTD | Tip 1y | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD | Entries | Deploy% |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `LIVE_STACK` | none | none | PASS | PASS | 0.000 | 0.000 | 18.07% | -21.72% | 24.86% | -12.81% | 0 | 0.00% |
| `DP10_PORT_OR_TAIEX_D10_HOLD_40` | PORT_OR_TAIEX | HOLD_40 | ALERT | ALERT | -0.735 | -0.059 | 16.72% | -21.78% | 22.70% | -10.84% | 35 | 38.59% |
| `DP10_PORT_DD_D15_RECOVER_FULL` | PORT_DD | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -0.569 | 0.604 | 15.72% | -21.12% | 20.07% | -8.52% | 3 | 19.93% |
| `DP10_PORT_OR_TAIEX_D10_RECOVER_FULL` | PORT_OR_TAIEX | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -0.632 | 0.124 | 16.56% | -21.60% | 22.50% | -11.07% | 54 | 43.25% |
| `DP10_TAIEX_DD_D10_RECOVER_FULL` | TAIEX_DD | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -0.635 | 0.124 | 16.55% | -21.60% | 22.49% | -11.07% | 54 | 43.08% |
| `DP10_PORT_DD_D12_RECOVER_FULL` | PORT_DD | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -0.824 | 0.319 | 15.78% | -21.40% | 20.41% | -8.56% | 4 | 24.51% |
| `DP10_TAIEX_DD_D10_HOLD_40` | TAIEX_DD | HOLD_40 | PAUSE_REVIEW | PAUSE_REVIEW | -0.882 | -0.059 | 16.42% | -21.78% | 22.22% | -10.89% | 33 | 36.57% |
| `DP10_PORT_DD_D10_RECOVER_HALF` | PORT_DD | RECOVER_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -0.912 | 0.271 | 15.70% | -21.45% | 19.91% | -8.51% | 8 | 16.80% |
| `DP10_PORT_DD_D10_RECOVER_FULL` | PORT_DD | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -0.919 | 0.243 | 15.74% | -21.48% | 20.42% | -9.36% | 4 | 26.98% |
| `DP10_PORT_OR_TAIEX_D10_RECOVER_HALF` | PORT_OR_TAIEX | RECOVER_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -0.936 | -0.072 | 16.34% | -21.79% | 21.88% | -10.22% | 58 | 35.46% |
| `DP10_PORT_DD_D12_RECOVER_HALF` | PORT_DD | RECOVER_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -1.003 | 0.347 | 15.37% | -21.37% | 19.23% | -8.51% | 7 | 11.45% |
| `DP10_PORT_DD_D15_RECOVER_HALF` | PORT_DD | RECOVER_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -1.014 | 0.611 | 14.82% | -21.11% | 17.66% | -8.66% | 3 | 5.68% |
| `DP10_PORT_OR_TAIEX_D10_TIME_OR_HALF` | PORT_OR_TAIEX | TIME_OR_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -1.026 | -0.146 | 16.31% | -21.87% | 21.43% | -10.10% | 77 | 29.42% |
| `DP10_TAIEX_DD_D15_RECOVER_FULL` | TAIEX_DD | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -1.088 | -0.087 | 16.07% | -21.81% | 21.13% | -9.25% | 8 | 32.96% |
| `DP10_PORT_OR_TAIEX_D15_RECOVER_FULL` | PORT_OR_TAIEX | RECOVER_FULL | PAUSE_REVIEW | PAUSE_REVIEW | -1.088 | -0.087 | 16.07% | -21.81% | 21.13% | -9.25% | 8 | 32.96% |
| `DP10_PORT_DD_D10_HOLD_40` | PORT_DD | HOLD_40 | PAUSE_REVIEW | PAUSE_REVIEW | -1.131 | 0.210 | 15.39% | -21.51% | 19.20% | -8.50% | 14 | 15.53% |
| `DP10_PORT_DD_D12_HOLD_40` | PORT_DD | HOLD_40 | PAUSE_REVIEW | PAUSE_REVIEW | -1.178 | 0.312 | 15.09% | -21.41% | 18.40% | -8.77% | 9 | 9.98% |
| `DP10_PORT_DD_D15_HOLD_40` | PORT_DD | HOLD_40 | PAUSE_REVIEW | PAUSE_REVIEW | -1.201 | 0.599 | 14.47% | -21.12% | 17.10% | -8.88% | 3 | 3.33% |
| `DP10_PORT_OR_TAIEX_D15_RECOVER_HALF` | PORT_OR_TAIEX | RECOVER_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -1.224 | -0.115 | 15.85% | -21.84% | 20.72% | -9.26% | 10 | 25.20% |
| `DP10_PORT_DD_D15_TIME_OR_HALF` | PORT_DD | TIME_OR_HALF | PAUSE_REVIEW | PAUSE_REVIEW | -1.235 | 0.611 | 14.38% | -21.11% | 16.79% | -8.95% | 3 | 3.19% |

## LIVE_STACK reference

- full CAGR/MDD: 13.85% / -21.72%
- heldout CAGR/MDD: 18.07% / -21.72%
- sealed CAGR/MDD: 24.86% / -12.81%

## Reading

- Held score = MDD↑pp − 0.5·|CAGRΔpp| vs **LIVE_STACK** (not FIN_EQUAL).
- Sealed is report-only in Stage A.
- **Outcome:** tip-clean challengers **0** · coexist **0** · cash drag dominates (best held score ≈ −0.57; most tip PAUSE_REVIEW).
- **Decision:** **STOP / archive**; keep Soft-Frozen / KD_OPT / TEL live unchanged. Expand grid only on human ask.

## Non-actions

- No Soft-Frozen / live KD / TEL / E45 / Soft-assist wire from this screen

## Label

`DRY_POWDER_DRAWDOWN_SCREEN_STAGE_A_2026-09-10__NO_LIFT__STOP`
