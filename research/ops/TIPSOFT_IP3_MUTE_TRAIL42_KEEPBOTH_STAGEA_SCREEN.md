# TIPSOFT_IP3_MUTE_TRAIL42_KEEPBOTH_STAGEA_SCREEN

Date: 2026-10-01 · Verdict: **`KEEPBOTH_PARTIAL`** · Register: **0kbc**

## Census (MUTE vs TRAIL42 disagreement)

- MUTE ON **94.385%** · TRAIL42 ON **94.7415%** · both_on **92.8402%**
- mute_only (MUTE ON / TRAIL OFF): **52** days (1.5449%)
- tr42_only (TRAIL ON / MUTE OFF): **64** days (1.9014%)
- both_off: **3.7136%**

## Tip Soft excess attribution (sum of daily excess vs L4)

| bucket | n | MUTE | TRAIL | TRAIL−MUTE |
|---|---:|---:|---:|---:|
| both_on | 3119 | -0.0092 | 0.063 | 0.0722 |
| mute_only | 52 | 0.0113 | -0.003 | -0.0142 |
| tr42_only | 64 | 0.0183 | 0.0008 | -0.0175 |
| both_off | 125 | -0.0682 | -0.0676 | 0.0007 |

## Arms

| arm | clock | held | tipY | sealedMDD | pct_on | verdict |
|---|---|---:|---:|---:|---:|---|
| `REF_TWIN_MUTE_CASH` | tipsoft_exact_t1_twin | 0.8735 | 2.4396 | 0.0173 | 94.385 | PARTIAL_MUTE_MDD |
| `REF_TWIN_TRAIL42_CASH` | tipsoft_exact_t1_twin | 1.4549 | 11.3364 | -0.3632 | 94.7415 | PARTIAL_TRAIL_TIPY |
| `TWIN_REF_MUTE__FT_CASH` | tipsoft_exact_t1_twin | 0.8735 | 2.4396 | 0.0173 | 94.385 | PARTIAL_MUTE_MDD |
| `TWIN_REF_TRAIL42__FT_CASH` | tipsoft_exact_t1_twin | 1.4549 | 11.3364 | -0.3632 | 94.7415 | PARTIAL_TRAIL_TIPY |
| `TWIN_OR_MUTE_TRAIL42__FT_CASH` | tipsoft_exact_t1_twin | 0.9811 | 2.2896 | 0.0239 | 96.2864 | PARTIAL_MUTE_MDD |
| `TWIN_AND_MUTE_TRAIL42__FT_CASH` | tipsoft_exact_t1_twin | 1.3878 | 11.784 | -0.3817 | 92.8402 | PARTIAL_TRAIL_TIPY |
| `TWIN_TRAIL42_PLUS_MUTE_ONLY_ON__FT_CASH` | tipsoft_exact_t1_twin | 0.9811 | 2.2896 | 0.0239 | 96.2864 | PARTIAL_MUTE_MDD |
| `TWIN_MUTE_PLUS_TRAIL_ONLY_ON__FT_CASH` | tipsoft_exact_t1_twin | 0.9811 | 2.2896 | 0.0239 | 96.2864 | PARTIAL_MUTE_MDD |
| `TWIN_TRAIL42_OFF_IF_SAT__FT_CASH` | tipsoft_exact_t1_twin | 0.844 | 2.3518 | 0.0212 | 95.9002 | PARTIAL_MUTE_MDD |
| `TWIN_OFF_IF_TRAIL42_SAT_OR_MUTE__FT_CASH` | tipsoft_exact_t1_twin | 0.7362 | 2.5041 | 0.0145 | 93.9988 | PARTIAL_MUTE_MDD |
| `TWIN_TRAIL42_HYST_OFF_R3__FT_CASH` | tipsoft_exact_t1_twin | 0.2954 | 10.6852 | -0.3361 | 88.5027 | PARTIAL_TRAIL_TIPY |
| `BLEND_TRAIL_a25` | tipsoft_return_blend | 1.0266 | 4.6572 | -0.0771 |  | PARTIAL_MIX |
| `BLEND_TRAIL_a50` | tipsoft_return_blend | 1.1745 | 6.8797 | -0.1719 |  | PARTIAL_MIX |
| `BLEND_TRAIL_a75` | tipsoft_return_blend | 1.3173 | 9.1064 | -0.2673 |  | PARTIAL_TRAIL_TIPY |
| `DIAG_ORACLE_DAYMAX` | diag_lookahead | 9.4495 | 65.3631 | 1.1946 |  | DIAG_KEEPBOTH_CEILING |
| `DIAG_SEALED_MUTE_ELSE_TRAIL` | diag_lookahead | 0.7679 | 2.4396 | 0.0173 |  | DIAG_ONLY |


Champion: `BLEND_TRAIL_a50` · held **1.1745** · tipY **6.8797** · sealedMDD **-0.1719**

Repro: `repro/tipsoft-ip3-mute-trail42-keepboth-stagea/`
