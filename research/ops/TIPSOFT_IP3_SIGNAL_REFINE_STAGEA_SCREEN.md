# TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_SCREEN

Date: 2026-09-30 · Verdict: **`IP3_REFINE_NO_EDGE`** · champion=**`NEAR&PEAK2__P4_SAT`**
Register: **0kaz** · screened_refine=145 · held_pos=0 · year_gap_close=24

## Year-oracle baseline

- live gap_to_oracle **1.1068** pp · NEAR **0.7507** · P34 **0.738**
- base_best counts (live/P3/P3+P4): `{'live': 8, 'P3': 5, 'P3+P4': 2, 'policy': 6}`

## Top causal arms

| Arm | heldΔNEAR | gap↑vsNEAR | sealedΔlive | tipYΔlive | vs live | p3% | p4% |
|---|---:|---:|---:|---:|---|---:|---:|
| NEAR&PEAK2__P4_SAT | -0.0209 | 0.0973 | -0.0523 | 6.4231 | HIT | 43.29 | 20.5 |
| NEAR&PEAK2__P4_NEAR_SAT | -0.0209 | 0.0973 | -0.0523 | 6.4231 | HIT | 43.29 | 20.5 |
| NEAR&PEAK2__P4OFF | -0.0434 | 0.0872 | -0.0434 | 6.1222 | HIT | 43.29 | 0.0 |
| NEAR&PEAK2__P4_DEFEND | -0.0701 | 0.0755 | -0.0434 | 6.2327 | HIT | 43.29 | 7.43 |
| NEAR&R21POS__P4_SAT | -0.1683 | 0.3477 | -0.0523 | 5.0708 | HIT | 41.77 | 20.89 |
| NEAR&R21POS__P4_NEAR_SAT | -0.1683 | 0.3477 | -0.0523 | 5.0708 | HIT | 41.77 | 20.89 |
| NEAR&R21POS__P4OFF | -0.1953 | 0.3345 | -0.0434 | 4.7252 | HIT | 41.77 | 0.0 |
| NEAR&R21POS__P4_DEFEND | -0.2246 | 0.3213 | -0.0434 | 4.7979 | HIT | 41.77 | 6.95 |
| NEAR&PROXY08__P4_SAT | -0.2757 | 0.0637 | -0.0523 | 6.2459 | HIT | 38.71 | 22.28 |
| NEAR&PROXY08__P4_NEAR_SAT | -0.2757 | 0.0637 | -0.0523 | 6.2459 | HIT | 38.71 | 22.28 |
| NEAR&R21POS__P4_NOTBLEED | -0.2879 | 0.2881 | -0.0523 | 4.941 | HIT | 41.77 | 21.84 |
| NEAR&PROXY08__P4_DEFEND | -0.2956 | 0.0553 | -0.0434 | 5.9912 | HIT | 38.71 | 0.71 |
| NEAR&PROXY08__P4OFF | -0.2972 | 0.0544 | -0.0434 | 5.9656 | HIT | 38.71 | 0.0 |
| NEAR&COMP__P4OFF | -0.4377 | 0.1101 | 0.0 | 1.1609 | HIT | 26.17 | 0.0 |
| NEAR&COMP__P4_SAT | -0.4377 | 0.1101 | 0.0 | 1.1609 | HIT | 26.17 | 0.0 |

## Oracle DIAG (lookahead)

| ORACLE_POS_DIAG__P4_SAT | heldΔNEAR 6.7378 | gap↑ 6.284 | sealed 0.2229 | tipY 14.6189 |

## Optimize / disposition

1. Objective: causal daily refine of I_p3 (± I_p4) so stack-on days beat live edge and off days fall back to live; close year-oracle gap without year dummies
2. Champion `NEAR&PEAK2__P4_SAT` held_vs_near=-0.0209 gap_improve=0.0973 sealed_vs_live=-0.0523 tipY=6.4231 live=HIT
3. I_p3-refine held_pos clears: n=0 · year_gap_close n=24 / screened_refine=145 (excl plain NEAR±P4)
4. P4OFF-only max held_vs_near=-0.0 · max gap_improve=0.3345 · held_pos n=0
5. Path4-on-NEAR held_pos confirms (0kay): n=2 NEAR__P4_SAT
6. NEAR year gap_to_oracle=0.7507 · live gap=1.1068 · P34 gap=0.738
7. Oracle DIAG best held_vs_near=6.7378 (lookahead — never promote)
8. If IP3_REFINE_HIT → draft observe; IP3_YEAR_GAP_SOFT → note only; IP3_REFINE_NO_EDGE → KEEP 0kaw NEARPEAK3 · Path4 DRAFT 0kay only
9. Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut · no wire

Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_signal_refine_stagea.py`

Label: `TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_SCREEN_2026-09-30__IP3_REFINE_NO_EDGE`
