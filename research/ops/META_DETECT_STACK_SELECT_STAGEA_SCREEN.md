# META_DETECT_STACK_SELECT_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`META_DETECT_MDD_BLOCK`** · champion=**`DETECT_P3_THETA`**
Register: **0kat** · mech=`META_DETECT_STACK_SELECT` · base=`STATIC_L3_LIVE_FUSE_COOL`

## Arms vs live Soft+FUSE+COOL

| Arm | vs live | held | full | sealed MDD↑ | tipY | fuse% | cool% | p3% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| STATIC_L1_SOFT | MDD_BLOCK | 1.5328 | 0.8749 | -3.2544 | 8.8607 | 0.0 | 0.0 | 0.0 |
| STATIC_L2_SOFT_FUSE | MDD_BLOCK | -1.7035 | -0.8242 | -3.4929 | -11.1273 | 100.0 | 0.0 | 0.0 |
| STATIC_L4_LIVE_P3 | MDD_BLOCK | 0.8475 | 0.3296 | -0.5026 | 2.8524 | 100.0 | 100.0 | 100.0 |
| DETECT_P3_THETA | MDD_BLOCK | 1.248 | 0.487 | -0.5026 | 2.8672 | 100.0 | 100.0 | 73.14 |
| DETECT_P3_FLIP | TIP_BLOCK | 0.0389 | -0.0962 | 0.1088 | -2.0757 | 100.0 | 100.0 | 5.94 |
| DETECT_FUSE_RISKON | MDD_BLOCK | 0.5163 | 0.2809 | -0.4627 | 7.1249 | 78.43 | 100.0 | 0.0 |
| DETECT_COOL_DEFEND | MDD_BLOCK | -0.7079 | -0.217 | -0.3978 | -11.1078 | 100.0 | 21.57 | 0.0 |
| DETECT_COMPLEMENT | MDD_BLOCK | -0.1948 | 0.0633 | -1.1431 | -4.5176 | 78.43 | 21.57 | 0.0 |
| DETECT_ALL_GATED | MDD_BLOCK | 1.0356 | 0.5478 | -1.7832 | -1.7714 | 78.43 | 21.57 | 73.14 |
| DETECT_MUTE_FUSE_ON_P3FLIP | MDD_BLOCK | 0.7682 | 0.2509 | -1.9223 | -3.4004 | 94.06 | 100.0 | 73.14 |
| ORACLE_BEST_LAYER_DIAG | DIAGNOSTIC | 59.5982 | 44.1978 | 2.1212 | 130.8534 |  |  |  |

## Optimize / disposition

1. Meta rule: Soft shell always-on; FUSE/COOL/P3 are optional blocks gated by detectors
2. Detect champion `DETECT_P3_THETA` → MDD_BLOCK held 1.248 tipY 2.8672 sealedMDD -0.5026
3. Best static contrast `STATIC_L1_SOFT` → MDD_BLOCK held 1.5328 tipY 8.8607 sealedMDD -3.2544
4. DETECT_P3_THETA (live stack + Path3 only when |trail|≥θ) lifts held vs always-on P3 but sealed MDD still blocks
5. DETECT_FUSE_RISKON lifts tipY a lot vs always-on FUSE+COOL but sealed MDD still blocks
6. Oracle DIAG lookahead upper bound proves selection headroom — never promote
7. Path4 OFF · Soft KEEP · broker false · no live wire · next harden sealed-MDD detectors

Repro: `PYTHONPATH=scripts python3 scripts/meta_detect_stack_select_stagea.py`

Label: `META_DETECT_STACK_SELECT_STAGEA_SCREEN_2026-09-30__META_DETECT_MDD_BLOCK`
