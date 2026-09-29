# FIN_SAT_SOFT_PATH3_COEXIST_MUTE_STAGEA_SCREEN

Date: 2026-09-29 · `2026-09-29T13:51:03Z` · Verdict **`MUTE_LIVE_WIRED_OK`**
Mechanism `SOFT_PATH3_FLIP_MUTE` · policy `MUTE_SOFT_FIN_TEL` · live flag ON=True

## Flip-day mute demo

| leg | asof | n_soft | n_muted | Soft FIN/TEL left | Soft 0050 | satellite | n_Path3 | all_-P3T0 |
|---|---|---:|---:|---:|---|---|---:|---|
| COMP→SAT | 2026-06-12 | 9 | 7 | 0 | True | True | 6 | True |
| SAT→COMP | 2026-05-20 | 9 | 7 | 0 | True | True | 6 | True |

no-flip @2026-09-24: n_muted=0 · should_mute=False · `no_flip`

Repro: `repro/fin-sat-soft-path3-coexist-mute-stagea/`

