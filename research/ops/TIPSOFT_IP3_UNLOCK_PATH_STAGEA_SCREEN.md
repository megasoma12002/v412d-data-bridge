# TIPSOFT_IP3_UNLOCK_PATH_STAGEA_SCREEN

Date: 2026-10-01 · Register: **0kb9** · Verdict: **`UNLOCK_HIGHON_FILL_HIT`**

## Track A — Soft FIN/TEL refill (loosen WITHIN)

- MUTE vs L4: held **+0.6702** tipY **+3.1878** sealedMDD **0.4503**
- OVERRIDE vs L4: held **+0.7661** tipY **+3.1878**
- Requires explicit ACCEPT to carve/undo Soft FIN/TEL OFF under 0kac WITHIN

## Track B — high-ON% × fill (Soft FIN/TEL OFF)

Gates in band: `ON_UNLESS_MUTE` 94.385%, `TRAIL21_GE_m001` 97.5639%, `TRAIL42_GE_m001` 94.7415%, `TRAIL63_GE_0` 55.8229%, `TRAIL63_GE_m001` 93.4046%
Clears: **2** / 15

| Arm | held | tipY | sealedMDD | ON% |
|---|---:|---:|---:|---:|
| `B_TRAIL21_GE_m001__FT_TO_CASH` | 1.4968 | 12.1819 | -2.5068 | 97.5639 |
| `B_TRAIL42_GE_m001__FT_TO_CASH` | 1.2006 | 8.533 | -0.0077 | 94.7415 |
| `B_ON_UNLESS_MUTE__FT_TO_CASH` | 0.6427 | -0.3935 | 0.5072 | 94.385 |
| `B_TRAIL63_GE_m001__FT_TO_CASH` | 0.2425 | -4.9382 | 0.5019 | 93.4046 |
| `B_TRAIL42_GE_m001__FREEZE` | -0.2066 | 0.1366 | -0.2147 | 94.7415 |
| `B_ON_UNLESS_MUTE__FREEZE` | -0.2099 | 0.1196 | -0.323 | 94.385 |
| `B_TRAIL63_GE_m001__FREEZE` | -0.2797 | 0.0646 | -0.3576 | 93.4046 |
| `B_TRAIL21_GE_m001__FREEZE` | -0.4266 | -2.3555 | -0.4044 | 97.5639 |
| `B_TRAIL63_GE_0__FREEZE` | -2.1823 | 3.0299 | -3.6091 | 55.8229 |
| `B_MUTE_S3_SAT__FREEZE` | -4.8107 | -6.7744 | -8.9413 | 9.8336 |
| `B_TRAIL63_GE_0__FT_TO_CASH` | -4.8249 | -5.762 | -0.3594 | 55.8229 |
| `B_ON_UNLESS_MUTE__FT_TO_0050` | -7.0884 | 63.4817 | -63.9128 | 94.385 |

## Optimize live

1. Question: Soft FIN/TEL refill (loosen WITHIN) vs high-ON% gate + new fill?
2. Verdict `UNLOCK_HIGHON_FILL_HIT`: Soft-refill MUTE tipY **+3.1878** held **+0.6702** · OVERRIDE tipY **+3.1878** (requires Soft FIN/TEL Exact T+1 carve / WITHIN loosen ACCEPT)
3. High-ON gate catalog: ON_UNLESS_MUTE=94.385%, TRAIL21_GE_m001=97.5639%, TRAIL42_GE_m001=94.7415%, TRAIL63_GE_0=55.8229%, TRAIL63_GE_m001=93.4046%
4. Track B Soft-core clears (held>+0.05 · sealedMDD≥−0.25 · tipY≥−1): **B_TRAIL42_GE_m001__FT_TO_CASH** held **1.2006** tipY **8.533** sealedMDD **-0.0077**
5. Disposition: promote high-ON fill champion → tip Soft twin Stage B / observe draft
6. Soft KEEP · Path4 OFF · broker false · no live wire this pack

Label: `TIPSOFT_IP3_UNLOCK_PATH_STAGEA_SCREEN_2026-10-01__UNLOCK_HIGHON_FILL_HIT`
