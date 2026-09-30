# FIN_SAT_PATH3_PATH4_LIVESTACK_T0_TWIN_STAGEB_SCREEN

Date: 2026-09-30 · Verdict: **`LIVESTACK_T0_MDD_BLOCK`** · champion=**`T0COOL_P3_P4_CASH_00025`**
Register: **0kaq** · base=`BASE_LIVE_FUSE_COOL` · Soft-core fill=`t0` · live base fill=`exact_t1`

## Arms vs live Exact T+1

| Arm | vs live | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |
|---|---|---:|---:|---:|---:|---:|---|
| T0_REF_P3_WITHIN | MDD_BLOCK | -2.5148 | -2.7988 | -7.028 | 1.923 | -0.2688 | 5-10 |
| T0COOL_REF_P3_WITHIN | MDD_BLOCK | -1.7637 | -1.957 | -7.1212 | -1.3987 | -2.0253 | 4-11 |
| T0_P3_P4_CASH_00025 | MDD_BLOCK | 0.4714 | -0.7709 | -5.6671 | 1.6422 | -0.4557 | 7-8 |
| T0COOL_P3_P4_CASH_00025 | MDD_BLOCK | 0.9913 | -0.2057 | -3.1588 | -1.6733 | -2.2097 | 7-8 |
| T0_P3_P4_CASH_0005 | MDD_BLOCK | 0.2552 | -0.922 | -5.2622 | 1.923 | -0.2688 | 6-9 |
| T0COOL_P3_P4_CASH_0005 | MDD_BLOCK | 0.9233 | -0.2899 | -3.1588 | -1.3987 | -2.0253 | 7-8 |
| T0_P3_P4_CASH_001 | MDD_BLOCK | 0.053 | -1.3406 | -6.4203 | 1.923 | -0.2688 | 6-9 |
| T0COOL_P3_P4_CASH_001 | MDD_BLOCK | 0.6478 | -0.6307 | -3.939 | -1.3987 | -2.0253 | 5-10 |
| T1_LIVE_P3_WITHIN | MDD_BLOCK | 0.8475 | 0.3296 | -0.5026 | 2.8524 | 2.0757 | 10-5 |

## Optimize live

1. **Yes — live promote must score P3/P4 on Exact T+0** (carve clock); Exact T+1 twin alone (0kap) is insufficient.
2. Soft-core **T+0×COOL vs live Exact T+1** still **`MDD_BLOCK`** (best `T0COOL_P3_P4_CASH_00025` held +0.99 but sealed MDD **−3.16** tipY **−1.67**).
3. Pure Soft-core T+0 Path3 WITHIN is worse vs live (held **−2.5** / sealed MDD **−7.0**) — Soft-core carve HIT ≠ beat live Soft+FUSE+COOL book.
4. Under T+0×COOL, Path4 CASH lifts held vs Path3-only but stays MDD/TIP blocked → **Path4 live OFF**.
5. Exact T+1 tip Soft P3 (0kap) has milder sealed MDD (−0.50) + tipY +2.85 — different clock/book; do not mix promote gates.
6. **Keep live Soft + COOL + FUSE** until a T+0 tip Soft hybrid (Soft Exact T+1 overlays + P3/P4 T+0 carve) clears sealed MDD — or human ACCEPTABLE disposition.
7. Soft KEEP · broker false · Path4 live flag OFF · no wire this pack

Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_path4_livestack_t0_twin_stageb.py`

Label: `FIN_SAT_PATH3_PATH4_LIVESTACK_T0_TWIN_STAGEB_SCREEN_2026-09-30__LIVESTACK_T0_MDD_BLOCK`
