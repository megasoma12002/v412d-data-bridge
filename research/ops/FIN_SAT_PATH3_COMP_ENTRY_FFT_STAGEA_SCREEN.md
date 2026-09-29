# FIN_SAT_PATH3_COMP_ENTRY_FFT_STAGEA_SCREEN

Date: 2026-09-29 · generated `2026-09-29T03:43:18Z`
Verdict: **`FFT_ENTRY_WEAK`** · Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live

## COMP-entry labels

- n entries: **76** · good **55** (72.37%) · bad **21**
- 2022 entries: **7** · good **4**
- FFT best: `w256_dphase` IC=0.1908 hit=0.5
- TD baseline `rel_5`: IC=0.1713 hit=0.5921 · fft_beats_td=True

## Feature screen (ranked |IC|)

| feature | fam | IC full | IC≤2018 | IC≥2019 | hit med | side |
|---|---|---:|---:|---:|---:|---|
| `w256_dphase` | fft | 0.1908 | 0.2981 | 0.0968 | 0.5 | high→good |
| `rel_5` | td | 0.1713 | -0.0075 | 0.3508 | 0.5921 | high→good |
| `vol_rel_21` | td | 0.1555 | 0.1393 | 0.2157 | 0.5132 | high→good |
| `w256_amp` | fft | -0.1456 | -0.2773 | -0.0222 | 0.5846 | low→good |
| `w64_recon` | fft | -0.1426 | -0.1806 | -0.0403 | 0.5132 | low→good |
| `w128_dphase` | fft | 0.1277 | 0.1274 | 0.1548 | 0.5467 | high→good |
| `w256_phase` | fft | 0.1191 | 0.2443 | 0.025 | 0.5231 | high→good |
| `w128_amp` | fft | -0.1146 | -0.2297 | 0.0109 | 0.5733 | low→good |
| `w128_recon` | fft | -0.0846 | -0.2266 | 0.1242 | 0.5467 | low→good |
| `w256_recon` | fft | 0.0838 | 0.1697 | 0.0234 | 0.5538 | high→good |
| `w64_dphase` | fft | -0.0584 | 0.1344 | -0.2581 | 0.5132 | low→good |
| `w128_phase` | fft | 0.0482 | 0.1144 | 0.0036 | 0.5733 | low→good |
| `w64_amp` | fft | 0.0467 | 0.0984 | -0.0044 | 0.5395 | high→good |
| `w64_phase` | fft | -0.0329 | -0.1931 | 0.1125 | 0.5395 | low→good |

## Spectrum peaks (descriptive)

- `daily_rel`: 2.89d(0.00493), 3.72d(0.00421), 2.78d(0.00416), 2.62d(0.00384)
- `trail_rel_63`: 471.86d(0.08632), 173.84d(0.06803), 220.2d(0.06079), 825.75d(0.05894)

## Threshold probe `BLOCK_w256_dphase`

- rule: block COMP when `w256_dphase` risk side (`high→good`), thr=0.0206993
- 2022: BASE 6.5 · P3 5.75 (-0.75) · probe 5.42 (-1.08)
- held↑ P3 3.4758 · probe 2.7535
- tipY↑ P3 2.7325 · probe -0.7996
- flips 153→115 · %SAT 24.16→29.69

Repro: `repro/fin-sat-path3-comp-entry-fft-stagea/`

