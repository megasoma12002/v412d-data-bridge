# META_DETECT_SEALED_MDD_HARDEN_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`SEALED_MDD_HARDEN_HIT`** · champion=**`P3_THETA_NEARPEAK3`**
Register: **0kau** · mech=`META_DETECT_SEALED_MDD_HARDEN` · base=`STATIC_L3_LIVE_FUSE_COOL`

## Arms vs live Soft+FUSE+COOL

| Arm | vs live | held | full | sealed MDD↑ | tipY | fuse% | cool% | p3% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| REF_DETECT_P3_THETA | MDD_BLOCK | 1.248 | 0.487 | -0.5026 | 2.8672 | 100.0 | 100.0 | 73.14 |
| REF_DETECT_FUSE_RISKON | MDD_BLOCK | 0.5163 | 0.2809 | -0.4627 | 7.1249 | 78.43 | 100.0 | 0.0 |
| P3_THETA_PROXY05 | HIT | 0.7883 | 0.5536 | -0.0434 | 2.5383 | 100.0 | 100.0 | 26.23 |
| P3_THETA_PROXY08 | MDD_BLOCK | 1.0123 | 0.4607 | -0.5026 | 3.3759 | 100.0 | 100.0 | 49.14 |
| P3_THETA_PROXY10 | MDD_BLOCK | 0.8624 | 0.3411 | -0.5026 | 2.8672 | 100.0 | 100.0 | 53.95 |
| P3_THETA_NEARPEAK3 | HIT | 1.4473 | 0.2907 | -0.0434 | 5.6789 | 100.0 | 100.0 | 50.83 |
| P3_THETA_NEARPEAK5 | MDD_BLOCK | 1.4694 | 0.3444 | -0.4263 | 3.5609 | 100.0 | 100.0 | 62.0 |
| P3_THETA_RISKON | MDD_BLOCK | 0.9979 | 0.3267 | -0.5026 | 1.6545 | 100.0 | 100.0 | 55.2 |
| P3_THETA_NOT_BLEED | MDD_BLOCK | -0.4893 | -1.0583 | -0.9977 | 4.0281 | 100.0 | 100.0 | 37.17 |
| P3_HARD_PEAK3_RISKON | HIT | 1.1531 | 0.1884 | -0.0434 | 4.4856 | 100.0 | 100.0 | 41.77 |
| P3_HARD_PEAK5_PROXY08 | MDD_BLOCK | 1.1392 | 0.4397 | -0.4263 | 3.4789 | 100.0 | 100.0 | 46.29 |
| P3_HARD_PEAK3_NOTBLEED | NO_EDGE | -0.1182 | -0.7334 | -0.1638 | 4.3 | 100.0 | 100.0 | 26.11 |
| FUSE_RISKON_PROXY08 | MDD_BLOCK | 0.5555 | 0.2997 | -0.4627 | 12.3672 | 70.23 | 100.0 | 0.0 |
| FUSE_RISKON_NEARPEAK5 | MDD_BLOCK | -0.0501 | 0.0059 | -2.2534 | 0.1134 | 71.98 | 100.0 | 0.0 |
| COMBO_HARD_P3PEAK_FUSERISK | MDD_BLOCK | 0.7108 | -0.1117 | -0.6257 | 17.4282 | 70.23 | 100.0 | 21.84 |
| COMBO_HARD_DEFEND_COOL | MDD_BLOCK | 2.3855 | 1.1403 | -4.1291 | -8.7736 | 71.98 | 28.02 | 41.77 |

## Optimize / disposition

1. Objective: clear sealed MDD floor (−0.25pp) while keeping Soft shell + detector-gated blocks
2. Harden champion `P3_THETA_NEARPEAK3` → HIT held 1.4473 tipY 5.6789 sealedMDD -0.0434
3. 0kat ref `REF_DETECT_FUSE_RISKON` → MDD_BLOCK sealedMDD -0.4627
4. Sealed MDD delta vs REF_DETECT_P3_THETA = 0.4592 pp
5. n_harden arms clearing sealed floor: 4 / 14
6. Soft KEEP · Path4 OFF · broker false · no live wire this pack
7. Next: if HIT/CLEARED → Stage B under hybrid promote twin; else tighter peak/bleed gates or Path3 OFF

Repro: `PYTHONPATH=scripts python3 scripts/meta_detect_sealed_mdd_harden_stagea.py`

Label: `META_DETECT_SEALED_MDD_HARDEN_STAGEA_SCREEN_2026-09-30__SEALED_MDD_HARDEN_HIT`
