# TIPSOFT_NEARPEAK3_PATH4_STACK_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`PATH4_STACK_HIT`** · champion=**`P3NEAR_P4_DEFEND`**
Register: **0kax** · mech=`TIPSOFT_NEARPEAK3_PATH4_STACK` · base=`BASE_LIVE_FUSE_COOL` · clock Exact T+1

## Arms vs live Soft+FUSE+COOL

| Arm | vs live | held | sealed MDD↑ | tipY | p3% | p4% | vs NEAR held | vs NEAR sealed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| REF_P3_THETA_NEARPEAK3 | HIT | 1.4473 | -0.0434 | 5.6789 | 50.83 | 0.0 |  |  |
| REF_ALWAYS_P3 | MDD_BLOCK | 0.8475 | -0.5026 | 2.8524 | 100.0 | 0.0 | -0.5998 | -0.4592 |
| REF_ALWAYS_P3P4 | MDD_BLOCK | 0.4137 | -0.53 | 2.6826 | 100.0 | 100.0 | -1.0336 | -0.4866 |
| P3NEAR_P4_ALWAYS | HIT | 1.0109 | -0.071 | 5.5057 | 50.83 | 100.0 | -0.4364 | -0.0276 |
| P3NEAR_P4_SAME | HIT | 1.0512 | -0.054 | 5.6762 | 50.83 | 50.83 | -0.3961 | -0.0106 |
| P3NEAR_P4_PEAK3 | HELD_HIT | 1.0056 | -0.054 | 5.7508 | 50.83 | 70.92 | -0.4417 | -0.0106 |
| P3NEAR_P4_PEAK5 | HELD_HIT | 0.9067 | -0.0278 | 5.6817 | 50.83 | 86.57 | -0.5406 | 0.0156 |
| P3NEAR_P4_RISKON | HIT | 1.0025 | -0.071 | 5.5901 | 50.83 | 78.43 | -0.4448 | -0.0276 |
| P3NEAR_P4_DEFEND | HIT | 1.4558 | -0.0434 | 5.5945 | 50.83 | 21.57 | 0.0085 | 0.0 |
| P3NEAR_P4_PROXY05 | HIT | 1.3046 | -0.054 | 5.7447 | 50.83 | 40.88 | -0.1427 | -0.0106 |
| P3NEAR_P4_NOTBLEED | HIT | 1.1909 | -0.054 | 5.518 | 50.83 | 21.66 | -0.2564 | -0.0106 |
| P3NEAR_P4_HARD | HIT | 1.2658 | -0.054 | 5.5289 | 50.83 | 18.57 | -0.1815 | -0.0106 |
| P4_ONLY_NEARPEAK3 | NO_EDGE | -0.3092 | -0.0691 | -0.2112 | 0.0 | 50.83 | -1.7565 | -0.0257 |

## Optimize / disposition

1. Stack Path4 only as Exact T+1 incremental on tip Soft shell; hybrid T+0 carve FORBIDDEN
2. Path4 champion `P3NEAR_P4_DEFEND` → HIT held 1.4558 tipY 5.5945 sealedMDD -0.0434
3. vs NEARPEAK3-only: held 0.0085 tipY -0.0844 sealed 0.0 → NO_EDGE
4. 0kaw ref `REF_P3_THETA_NEARPEAK3` → HIT
5. Path4 live flag stays OFF; Soft KEEP; broker false; no wire this pack
6. Next: Path4 clears live gates under NEARPEAK3 but vs NEARPEAK3-only is NO_EDGE — keep Path4 OFF on 0kaw observe unless a +held Path4 gate appears

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_nearpeak3_path4_stack_stagea.py`

Label: `TIPSOFT_NEARPEAK3_PATH4_STACK_STAGEA_SCREEN_2026-09-30__PATH4_STACK_HIT`
