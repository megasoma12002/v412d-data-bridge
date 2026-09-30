# RESEARCH_LIVE_ALIGN_GAP_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`ALIGN_GAP_LARGE`** · held gap research→live = **+2.51** pp
Register: **0kar** · research=`R0_T0_P3_WITHIN` · live=`L3_LIVE_FUSE_COOL`

## Gap: tip Soft / Path4 arm **minus** Soft-core research R0

| Compare | held | full | sealed MDD↑ | tipY | tip1y |
|---|---:|---:|---:|---:|---:|
| L1_SOFT_T1_minus_R0_T0_P3_WITHIN | 4.0476 | 3.6737 | 3.7736 | 11.0218 | 8.6169 |
| L2_SOFT_FUSE_T1_minus_R0_T0_P3_WITHIN | 0.8113 | 1.9746 | 3.5351 | -10.2211 | -9.0015 |
| L3_LIVE_FUSE_COOL_minus_R0_T0_P3_WITHIN | 2.5148 | 2.7988 | 7.028 | 1.7877 | 2.1278 |
| L4_LIVE_P3_WITHIN_minus_R0_T0_P3_WITHIN | 3.3623 | 3.1284 | 6.5254 | 4.8589 | 4.648 |
| R1_T0_P3_P4_CASH_00025_minus_R0_T0_P3_WITHIN | 2.9862 | 2.0279 | 1.3609 | -0.2831 | -0.1865 |

## Tip Soft layer ladder deltas

| Step | held | full | sealed MDD↑ | tipY |
|---|---:|---:|---:|---:|
| +FUSE_SELL_a75 | -3.2363 | -1.6991 | -0.2385 | -19.988 |
| +COOL_c8 | 1.7035 | 0.8242 | 3.4929 | 11.1273 |
| +Path3_WITHIN_tipSoft | 0.8475 | 0.3296 | -0.5026 | 2.8524 |

## Recommendations

1. Research Soft-core `R0_T0_P3_WITHIN` vs live `L3_LIVE_FUSE_COOL` held gap = **+2.51** pp (tipY 1.7877) → `ALIGN_GAP_LARGE`
2. Vs tip Soft Soft-only `L1_SOFT_T1` held gap = **+4.05** pp — clock/book still diverge even without FUSE/COOL
3. Vs tip Soft +P3 `L4_LIVE_P3_WITHIN` held gap = **+3.36** pp
4. Largest tip Soft layer step: `+FUSE_SELL_a75` held -3.2363 / sealedMDD -0.2385 / tipY -19.988
5. Adopt protocol P1–P6 as research↔live alignment SSOT (see decision pack)
6. Next implementable fix: tip Soft hybrid runner (Soft Exact T+1 overlays + P3/P4 Exact T+0 carve) as default twin template
7. Soft KEEP · broker false · Path4 live OFF · no wire this pack

Repro: `PYTHONPATH=scripts python3 scripts/research_live_align_gap_stagea.py`

Label: `RESEARCH_LIVE_ALIGN_GAP_STAGEA_SCREEN_2026-09-30__ALIGN_GAP_LARGE`
