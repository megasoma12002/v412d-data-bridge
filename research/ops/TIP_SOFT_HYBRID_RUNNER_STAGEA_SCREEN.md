# TIP_SOFT_HYBRID_RUNNER_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`HYBRID_MDD_BLOCK`** · champion=**`HYBRID_P3_P4_CASH_00025_T0`**
Register: **0kas** · runner=`TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE` · base=`BASE_LIVE_FUSE_COOL`

## Arms vs live Soft+FUSE+COOL

| Arm | vs live | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |
|---|---|---:|---:|---:|---:|---:|---|
| TIPSOFT_P3_WITHIN_T1 | MDD_BLOCK | 0.8475 | 0.3296 | -0.5026 | 2.8524 | 2.0757 | 10-5 |
| HYBRID_P3_WITHIN_T0 | MDD_BLOCK | -3.7406 | -3.1276 | -11.4448 | -5.6871 | -5.527 | 2-13 |
| HYBRID_P3_P4_CASH_00025_T0 | MDD_BLOCK | -3.2202 | -2.7661 | -8.7247 | -5.6993 | -5.5353 | 2-13 |

## Optimize / disposition

1. Default twin runner = `TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE` (Soft Exact T+1 overlays + P3/P4 Exact T+0 carve premium)
2. Hybrid Path3 `HYBRID_P3_WITHIN_T0` → MDD_BLOCK held -3.7406 tipY -5.6871 sealedMDD -11.4448
3. Hybrid P3+P4 `HYBRID_P3_P4_CASH_00025_T0` → MDD_BLOCK held -3.2202 tipY -5.6993 sealedMDD -8.7247
4. Contrast Exact T+1 tip Soft Path3 `TIPSOFT_P3_WITHIN_T1` was MDD_BLOCK (clock-mismatch ref from 0kap)
5. Hybrid still blocked vs live Soft+FUSE+COOL — keep live stack; do not promote P3/P4 on Soft-core HIT alone
6. Soft KEEP · broker false · Path4 live flag OFF · no wire this pack

Repro: `PYTHONPATH=scripts python3 scripts/tip_soft_hybrid_runner_stagea.py`

Label: `TIP_SOFT_HYBRID_RUNNER_STAGEA_SCREEN_2026-09-30__HYBRID_MDD_BLOCK`
