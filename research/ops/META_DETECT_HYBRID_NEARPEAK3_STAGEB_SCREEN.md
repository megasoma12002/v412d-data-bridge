# META_DETECT_HYBRID_NEARPEAK3_STAGEB_SCREEN

Date: 2026-09-30 · Verdict: **`HYBRID_NEARPEAK3_MDD_BLOCK`** · target=**`HYBRID_P3_NEARPEAK3`**
Register: **0kav** · runner=`TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE` · base=`BASE_LIVE_FUSE_COOL`

## Arms vs live Soft+FUSE+COOL

| Arm | vs live | held | full | sealed MDD↑ | tipY | gate% |
|---|---|---:|---:|---:|---:|---:|
| TIPSOFT_P3_THETA_NEARPEAK3 | HIT | 1.4473 | 0.2907 | -0.0434 | 5.6789 | None |
| TIPSOFT_P3_WITHIN_T1 | MDD_BLOCK | 0.8475 | 0.3296 | -0.5026 | 2.8524 |  |
| HYBRID_P3_UNGATED | MDD_BLOCK | -3.7406 | -3.1276 | -11.4448 | -5.6871 | 100.0 |
| HYBRID_P3P4_UNGATED | MDD_BLOCK | -3.2202 | -2.7661 | -8.7247 | -5.6993 | 100.0 |
| HYBRID_P3_NEARPEAK3 | MDD_BLOCK | -2.2498 | -2.6409 | -3.0616 | -5.7831 | 50.86 |
| HYBRID_P3P4_NEARPEAK3 | MDD_BLOCK | -2.1661 | -2.5313 | -3.2559 | -5.7953 | 50.86 |
| HYBRID_P3_PROXY05 | MDD_BLOCK | -0.9705 | -1.8651 | -2.4569 | 1.7579 | 26.25 |
| HYBRID_P3P4_PROXY05 | MDD_BLOCK | -0.8622 | -1.7408 | -2.4569 | 1.7579 | 26.25 |
| HYBRID_P3_PEAK3_RISKON | MDD_BLOCK | -2.4803 | -2.7129 | -3.0616 | -9.1459 | 41.8 |
| HYBRID_P3P4_PEAK3_RISKON | MDD_BLOCK | -2.3753 | -2.5808 | -3.2559 | -9.1578 | 41.8 |
| HYBRID_P3_NEARPEAK5 | MDD_BLOCK | -0.6419 | -2.4262 | -11.7763 | 7.2171 | 62.04 |
| HYBRID_P3P4_NEARPEAK5 | MDD_BLOCK | -0.2166 | -2.0236 | -4.1407 | 7.2038 | 62.04 |

## Optimize / disposition

1. Stage B target `HYBRID_P3_NEARPEAK3` → MDD_BLOCK held -2.2498 tipY -5.7831 sealedMDD -3.0616
2. Ungated hybrid ref `HYBRID_P3_UNGATED` → MDD_BLOCK sealedMDD -11.4448 · sealed Δ vs ungated = 8.3832 pp
3. Dual-track tip Soft `TIPSOFT_P3_THETA_NEARPEAK3` → HIT held 1.4473 sealedMDD -0.0434
4. Best hybrid overall `HYBRID_P3P4_PROXY05` → MDD_BLOCK
5. Promote only if hybrid NEARPEAK3 clears tip Soft gates; Soft-core HIT alone insufficient
6. Soft KEEP · Path4 OFF · broker false · no live wire this pack

Repro: `PYTHONPATH=scripts python3 scripts/meta_detect_hybrid_nearpeak3_stageb.py`

Label: `META_DETECT_HYBRID_NEARPEAK3_STAGEB_SCREEN_2026-09-30__HYBRID_NEARPEAK3_MDD_BLOCK`
