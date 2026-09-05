# L1 Sealed-Window Attribution (for L2 charter)

Generated: `2026-09-05T01:44:34.509099+00:00`
Locked (frozen, no retune): `L1_FINCAP50_COMBO_50`
Status: **RESEARCH_ONLY** — explains `STOP_L1_HELDOUT_MIXED`; does not reopen L1 cuts.

## Held-out deltas (recomputed)

- Val CAGR giveback: **-0.65 pp** (negative = L1 better)
- Val MDD improve: **9.98 pp**
- Sealed CAGR giveback: **8.91 pp** (gate ≤3.0) → **FAIL**
- Sealed MDD improve: **7.72 pp**

## Flag coverage

| Window | COMBO share | CRISIS share |
|---|---:|---:|
| oof_2012_2018 | 33.2% | 8.9% |
| val_2019_2022 | 35.1% | 17.5% |
| sealed_2023_plus | 38.3% | 13.5% |

## Sealed day conditionals

- BASE mean ret flag-on / off: `0.0009230975878964617` / `0.0009483313774384043`
- L1 mean ret flag-on / off: `0.0003586773588345514` / `0.0007652735142664113`
- L1 mean E45 scale (sealed / flag-on): `0.8083048919226393` / `0.5`

## Sealed by year

| Year | BASE CAGR | L1 CAGR | Giveback pp | MDD Δpp |
|---:|---:|---:|---:|---:|
| 2023 | 7.48% | 8.42% | -0.94 | +0.66 |
| 2024 | 22.31% | 11.89% | +10.43 | +1.62 |
| 2025 | 19.19% | 15.48% | +3.71 | +3.09 |
| 2026 | 68.27% | 34.92% | +33.35 | +7.72 |

## Implications for L2

1. COMBO flag stays elevated in sealed bull years; equity scale 0.50 truncates upside more than it saves drawdown.
2. Validation had negative CAGR giveback (L1 beat BASE) because stress episodes repaid the cut; sealed did not.
3. L2 must separate FIN_CAP (concentration) from gross-cut (timing), cap flag share, and require asymmetric restore.
4. Do not retune L1_FINCAP50_COMBO_50 — axis STOPPED; new L2 charter required.

See charter: `research/gaps/MDD_L2_LOSS_ENGINE_CHARTER.md`
